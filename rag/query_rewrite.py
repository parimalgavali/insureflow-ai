"""Query rewriting: turn a user's question into German search queries in policy language.

Two implementations share one interface:
- ``AnthropicRewriter`` calls Claude (needs ``ANTHROPIC_API_KEY``).
- ``RecordedRewriter`` replays rewrites stored in a JSON fixture, so eval/CI run offline and
  deterministically. ``python -m rag.eval --record`` refreshes the fixture with the live model.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Protocol

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
REWRITES_PATH = Path(__file__).parent / "eval" / "rewrites.json"

SYSTEM_PROMPT = """You help a retrieval system find clauses in the German motor insurance model \
terms (GDV AKB 2015: Kfz-Haftpflicht, Teilkasko, Vollkasko, Schutzbrief, Pflichten im Schadenfall).
Given a policyholder's question (German or English), write 3 short German search queries that use \
the vocabulary the policy wording itself would use (e.g. "Entwendung" for theft, "mut- oder \
böswillige Handlungen" for vandalism, "Anzeigepflicht" for reporting a loss, "Zusammenstoß mit \
Haarwild" for hitting a deer, "Selbstbeteiligung" for deductible, "grobe Fahrlässigkeit", \
"Leistungsfreiheit").
Return only a JSON array of 3 strings, no commentary."""


class QueryRewriter(Protocol):
    def rewrite(self, question: str, lang: str) -> list[str]: ...


class NoRewriter:
    def rewrite(self, question: str, lang: str) -> list[str]:
        return []


class RecordedRewriter:
    """Looks rewrites up by exact question text; unknown questions get no variants."""

    def __init__(self, path: Path = REWRITES_PATH):
        self.path = path
        self._data: dict[str, list[str]] = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        )

    def rewrite(self, question: str, lang: str) -> list[str]:
        return list(self._data.get(question.strip(), []))

    def record(self, question: str, variants: list[str]) -> None:
        self._data[question.strip()] = variants

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


class AnthropicRewriter:
    def __init__(self, model: str | None = None, api_key: str | None = None):
        import anthropic

        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def rewrite(self, question: str, lang: str) -> list[str]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Question ({lang}): {question}"}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        return parse_variants(text)


def parse_variants(text: str) -> list[str]:
    match = re.search(r"\[.*\]", text, re.S)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return [str(v).strip() for v in data if str(v).strip()][:3]


def make_rewriter(kind: str) -> QueryRewriter:
    if kind == "none":
        return NoRewriter()
    if kind == "recorded":
        return RecordedRewriter()
    if kind == "anthropic":
        return AnthropicRewriter()
    raise ValueError(f"unknown rewriter {kind!r}; expected none|recorded|anthropic")
