"""Server-Sent Events helpers: ``event: <type>\\ndata: <json>\\n\\n`` per message."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


def encode(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=_default)}\n\n"


def _default(obj: Any):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return str(obj)


def chunk_words(text: str, size: int = 3) -> Iterable[str]:
    """Deliver a finished answer in word groups so the UI can type it out."""
    words = text.split(" ")
    for i in range(0, len(words), size):
        piece = " ".join(words[i : i + size])
        yield piece + (" " if i + size < len(words) else "")
