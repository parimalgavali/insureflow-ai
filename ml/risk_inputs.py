"""Operational scoring gate, not a statistical guarantee of model reliability."""

import math
from datetime import date
from typing import Any

KNOWN_EVENTS = {
    "collision",
    "hit_and_run",
    "theft",
    "vandalism",
    "glass",
    "wild_animal",
    "storm_hail",
    "fire",
    "other",
}


def missing_risk_inputs(facts: Any, policy: Any) -> list[str]:
    missing = []
    incident = getattr(facts, "incident_date", None)
    try:
        valid_date = (
            isinstance(incident, str) and date.fromisoformat(incident).isoformat() == incident
        )
    except ValueError:
        valid_date = False
    if not valid_date:
        missing.append("incident_date")
    event = getattr(facts, "event_type", "unknown")
    if event not in KNOWN_EVENTS:
        missing.append("event_type")
    for name in ("third_party_involved", "police_report_filed", "witnesses"):
        if not isinstance(getattr(facts, name, None), bool):
            missing.append(name)
    if event == "collision" and getattr(facts, "third_party_involved", None) is True:
        if not isinstance(getattr(facts, "third_party_known", None), bool):
            missing.append("third_party_known")
    if getattr(policy, "product", None) not in {"haftpflicht", "teilkasko", "vollkasko"}:
        missing.append("policy_product")
    deductible = getattr(policy, "deductible_eur", None)
    if (
        isinstance(deductible, bool)
        or not isinstance(deductible, (int, float))
        or not math.isfinite(deductible)
        or deductible < 0
    ):
        missing.append("policy_deductible")
    return missing
