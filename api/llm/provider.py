"""One interface for every LLM backend.

``Provider.complete`` returns free text or, when ``response_schema`` is given, a validated pydantic
object. ``tag`` names the agent step ("extract", "compose" …) so ``RecordedProvider`` can replay
fixtures in order and the API can attribute cost/latency per step.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from api.agent.schemas import ChatMessage


class ProviderError(RuntimeError):
    pass


@dataclass
class Completion:
    text: str
    parsed: BaseModel | None = None
    raw: Any = None
    usage: dict[str, int] = field(default_factory=dict)


class Provider(Protocol):
    name: str

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        system: str | None = None,
        response_schema: type[BaseModel] | None = None,
        tag: str = "default",
        max_tokens: int = 1024,
    ) -> Completion: ...


def _parse_structured[T: BaseModel](payload: Any, schema: type[T]) -> T:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                f"model returned non-JSON for {schema.__name__}: {payload[:200]}"
            ) from exc
    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise ProviderError(f"model output failed {schema.__name__} validation: {exc}") from exc


class AnthropicProvider:
    """Structured output via a forced tool call whose input schema is the pydantic JSON schema."""

    name = "anthropic"
    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(self, model: str | None = None, api_key: str | None = None, client: Any = None):
        self.model = model or os.environ.get("ANTHROPIC_MODEL", self.DEFAULT_MODEL)
        if client is None:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.client = client

    def build_request(
        self,
        messages: Sequence[ChatMessage],
        *,
        system: str | None,
        response_schema: type[BaseModel] | None,
        max_tokens: int,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": 0,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages if m.role != "system"
            ],
        }
        system_parts = [m.content for m in messages if m.role == "system"]
        if system:
            system_parts.insert(0, system)
        if system_parts:
            request["system"] = "\n\n".join(system_parts)
        if response_schema is not None:
            tool_name = response_schema.__name__
            request["tools"] = [
                {
                    "name": tool_name,
                    "description": response_schema.__doc__ or f"Return a {tool_name}",
                    "input_schema": response_schema.model_json_schema(),
                }
            ]
            request["tool_choice"] = {"type": "tool", "name": tool_name}
        return request

    def complete(
        self, messages, *, system=None, response_schema=None, tag="default", max_tokens=1024
    ):
        request = self.build_request(
            messages, system=system, response_schema=response_schema, max_tokens=max_tokens
        )
        response = self.client.messages.create(**request)
        usage = {}
        if getattr(response, "usage", None) is not None:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        if response_schema is not None:
            for block in response.content:
                if getattr(block, "type", "") == "tool_use":
                    parsed = _parse_structured(block.input, response_schema)
                    return Completion(
                        json.dumps(block.input, ensure_ascii=False), parsed, response, usage
                    )
            raise ProviderError("Anthropic returned no tool_use block for structured output")
        text = "".join(
            getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text"
        )
        return Completion(text, None, response, usage)


class OllamaProvider:
    """Local fallback via Ollama /api/chat; structured output through the ``format`` JSON schema."""

    name = "ollama"

    def __init__(
        self, model: str | None = None, base_url: str | None = None, http_client: Any = None
    ):
        import httpx

        self.model = model or os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
        self.base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.http = http_client or httpx.Client(timeout=120)

    def build_request(self, messages, *, system, response_schema, max_tokens) -> dict[str, Any]:
        chat = [{"role": m.role, "content": m.content} for m in messages]
        if system:
            chat.insert(0, {"role": "system", "content": system})
        request: dict[str, Any] = {
            "model": self.model,
            "messages": chat,
            "stream": False,
            "options": {"temperature": 0, "num_predict": max_tokens},
        }
        if response_schema is not None:
            request["format"] = response_schema.model_json_schema()
        return request

    def complete(
        self, messages, *, system=None, response_schema=None, tag="default", max_tokens=1024
    ):
        request = self.build_request(
            messages, system=system, response_schema=response_schema, max_tokens=max_tokens
        )
        response = self.http.post(f"{self.base_url}/api/chat", json=request)
        if response.status_code != 200:
            raise ProviderError(f"Ollama HTTP {response.status_code}: {response.text[:200]}")
        text = response.json().get("message", {}).get("content", "")
        parsed = _parse_structured(text, response_schema) if response_schema is not None else None
        return Completion(text, parsed, response.json())


class RecordedProvider:
    """Replays responses from a JSON fixture ``{tag: [response, ...]}`` in call order.

    With ``record_from`` set (and typically ``RECORD=1``), every call is forwarded to the live
    provider and the response appended to the fixture, which makes the fixture reproducible.
    """

    name = "recorded"

    def __init__(self, path: Path, record_from: Provider | None = None):
        self.path = Path(path)
        self.record_from = record_from
        self._data: dict[str, list[Any]] = (
            json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        )
        self._cursor: dict[str, int] = {}
        self.calls: list[dict[str, Any]] = []

    def complete(
        self, messages, *, system=None, response_schema=None, tag="default", max_tokens=1024
    ):
        self.calls.append(
            {"tag": tag, "messages": [m.model_dump() for m in messages], "system": system}
        )
        if self.record_from is not None:
            live = self.record_from.complete(
                messages,
                system=system,
                response_schema=response_schema,
                tag=tag,
                max_tokens=max_tokens,
            )
            self._data.setdefault(tag, []).append(
                json.loads(live.text) if response_schema is not None else live.text
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            return live
        responses = self._data.get(tag, [])
        index = self._cursor.get(tag, 0)
        if index >= len(responses):
            raise ProviderError(f"no recorded response #{index + 1} for tag {tag!r} in {self.path}")
        self._cursor[tag] = index + 1
        payload = responses[index]
        if response_schema is not None:
            parsed = _parse_structured(payload, response_schema)
            return Completion(json.dumps(payload, ensure_ascii=False), parsed)
        return Completion(str(payload), None)


def make_provider(kind: str | None = None, **kwargs) -> Provider:
    kind = (kind or os.environ.get("LLM_PROVIDER", "anthropic")).lower()
    if kind == "anthropic":
        return AnthropicProvider(**kwargs)
    if kind == "ollama":
        return OllamaProvider(**kwargs)
    if kind == "recorded":
        return RecordedProvider(**kwargs)
    raise ValueError(f"unknown LLM_PROVIDER {kind!r}; expected anthropic|ollama|recorded")
