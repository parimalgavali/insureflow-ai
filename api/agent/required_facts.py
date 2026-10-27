"""Which facts must be known before coverage can be assessed, and how to describe them."""

from __future__ import annotations

from api.agent.schemas import ClaimFacts, Language

REQUIRED: tuple[str, ...] = (
    "incident_date",
    "event_type",
    "third_party_involved",
    "damage_description",
)
MAX_PER_TURN = 2

LABELS: dict[str, dict[Language, str]] = {
    "incident_date": {"de": "Datum des Schadens", "en": "date of the incident"},
    "event_type": {
        "de": "Art des Schadens (Unfall, Diebstahl, Glasbruch …)",
        "en": "what kind of incident it was",
    },
    "third_party_involved": {
        "de": "ob ein anderes Fahrzeug / eine andere Person beteiligt war",
        "en": "whether another vehicle or person was involved",
    },
    "damage_description": {
        "de": "welche Schäden am Fahrzeug sichtbar sind",
        "en": "what damage the vehicle has",
    },
    "police_report_filed": {
        "de": "ob die Polizei informiert wurde",
        "en": "whether the police were informed",
    },
    "location": {"de": "wo es passiert ist", "en": "where it happened"},
}


def missing_facts(facts: ClaimFacts) -> list[str]:
    missing = []
    for name in REQUIRED:
        value = getattr(facts, name)
        if value is None or (name == "event_type" and value == "unknown"):
            missing.append(name)
    return missing


def describe(missing: list[str], language: Language) -> str:
    return "; ".join(LABELS.get(name, {}).get(language, name) for name in missing[:MAX_PER_TURN])
