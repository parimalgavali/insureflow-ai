"""Cheap DE/EN detection from the user's first message (no model call)."""

from __future__ import annotations

import re

from api.agent.schemas import Language

GERMAN_HINTS = {
    "der",
    "die",
    "das",
    "und",
    "ich",
    "ist",
    "nicht",
    "mein",
    "meine",
    "wurde",
    "auto",
    "unfall",
    "gestern",
    "heute",
    "schaden",
    "wagen",
    "fahrzeug",
    "polizei",
    "bei",
    "mit",
    "ein",
    "eine",
    "am",
    "habe",
    "hat",
    "war",
    "im",
    "auf",
    "wie",
    "zahlt",
    "versicherung",
    "kasko",
}
ENGLISH_HINTS = {
    "the",
    "and",
    "my",
    "car",
    "was",
    "is",
    "not",
    "someone",
    "hit",
    "parked",
    "yesterday",
    "today",
    "damage",
    "police",
    "with",
    "a",
    "an",
    "on",
    "at",
    "have",
    "has",
    "insurance",
    "cover",
    "covered",
}
UMLAUT = re.compile(r"[äöüß]")


def detect_language(text: str, default: Language = "de") -> Language:
    words = set(re.findall(r"[a-zA-ZäöüßÄÖÜ]+", text.lower()))
    de = len(words & GERMAN_HINTS) + (2 if UMLAUT.search(text) else 0)
    en = len(words & ENGLISH_HINTS)
    if de == en:
        return default
    return "de" if de > en else "en"
