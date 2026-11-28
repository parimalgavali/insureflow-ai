"""Bounded PDF text preparation; the worker never calls a model or executes document text."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

MAX_TEXT = 2_000_000
MAX_PASSAGE = 1800
HEADING = re.compile(
    r"^(?:[A-Z](?:\.\d+)+|§\s*\d+|\d+(?:\.\d+)*\.?)\s+\S.{2,115}$" r"|^[A-Z]\s+[A-ZÄÖÜ]\S.{2,115}$"
)


class PolicyTextError(Exception):
    pass


@dataclass
class Passage:
    page: int
    section_heading: str | None
    text: str


def extract_passages(path: Path) -> tuple[int, list[Passage]]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise PolicyTextError("encrypted_pdf")
        if not 0 < len(reader.pages) <= 300:
            raise PolicyTextError("unsupported_page_count")
        passages = []
        total = 0
        heading = None
        for number, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").replace("\x00", "")
            total += len(text)
            if total > MAX_TEXT:
                raise PolicyTextError("text_too_large")
            letters = sum(c.isalpha() for c in text)
            if letters < 20:
                # Truly blank spacer pages are allowed; nonempty unreadable pages
                # must not silently disappear from a supposedly ready policy.
                if page.get_contents() is not None or text.strip():
                    raise PolicyTextError("unreadable_page")
                continue
            if text.count("\ufffd") > max(3, len(text) // 100):
                raise PolicyTextError("unreadable_page")
            buffer = ""
            for line in text.splitlines():
                line = " ".join(line.split())
                if not line:
                    continue
                if HEADING.match(line):
                    if buffer:
                        passages.append(Passage(number, heading, buffer))
                        buffer = ""
                    heading = line
                # Keep long lines bounded without dropping text or crossing pages.
                for word in line.split():
                    while len(word) > MAX_PASSAGE:
                        if buffer:
                            passages.append(Passage(number, heading, buffer))
                            buffer = ""
                        passages.append(Passage(number, heading, word[:MAX_PASSAGE]))
                        word = word[MAX_PASSAGE:]
                    if len(buffer) + len(word) + 1 > MAX_PASSAGE:
                        passages.append(Passage(number, heading, buffer))
                        buffer = ""
                    buffer = f"{buffer} {word}".strip()
            if buffer:
                passages.append(Passage(number, heading, buffer))
        if not passages:
            raise PolicyTextError("no_readable_text")
        return len(reader.pages), passages
    except PolicyTextError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PolicyTextError("unreadable_pdf") from exc


def prepare_pdf(path: Path) -> tuple[int, list[Passage]]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "api.policy_text", str(path.resolve())],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PolicyTextError("processing_timeout") from exc
    if result.returncode or len(result.stdout) > 16_000_000:
        raise PolicyTextError("processing_failed")
    try:
        payload = json.loads(result.stdout)
        if "error" in payload:
            raise PolicyTextError(payload["error"])
        return payload["page_count"], [Passage(**p) for p in payload["passages"]]
    except (ValueError, KeyError, TypeError) as exc:
        raise PolicyTextError("processing_failed") from exc


def _main():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
        try:
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        except (ValueError, OSError):
            pass  # RLIMIT_AS is not supported on every development host.
        pages, passages = extract_passages(Path(sys.argv[1]))
        print(json.dumps({"page_count": pages, "passages": [asdict(p) for p in passages]}))
    except PolicyTextError as exc:
        print(json.dumps({"error": str(exc)}))


def search_passages(session, conversation_id, document_id, query: str, limit: int = 5):
    """Search only one ready policy in one conversation, preserving citation metadata."""
    from sqlalchemy import func, literal_column, select

    from db.models import PolicyDocument, PolicyPassage

    if not query.strip():
        return []
    terms = func.plainto_tsquery(literal_column("'simple'::regconfig"), query[:1000])
    return list(
        session.scalars(
            select(PolicyPassage)
            .join(PolicyDocument, PolicyDocument.id == PolicyPassage.document_id)
            .where(
                PolicyPassage.conversation_id == conversation_id,
                PolicyDocument.conversation_id == conversation_id,
                PolicyPassage.document_id == document_id,
                PolicyDocument.status == "ready",
                PolicyDocument.is_current.is_(True),
                PolicyPassage.search_vector.op("@@")(terms),
            )
            .order_by(
                func.ts_rank(PolicyPassage.search_vector, terms).desc(), PolicyPassage.position
            )
            .limit(min(max(limit, 1), 20))
        )
    )


if __name__ == "__main__":
    _main()
