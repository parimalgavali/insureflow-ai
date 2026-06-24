from __future__ import annotations

from typing import Literal, TypedDict

Label = Literal["LOW", "MEDIUM", "HIGH"]


class RuleScore(TypedDict):
    score: int
    label: Label
    reason_codes: list[str]


def _label(score: int) -> Label:
    if score >= 75:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def score_severity(
    *,
    estimated_damage_eur: int,
    injury_reported: bool,
    third_party_involved: bool,
) -> RuleScore:
    score = 20
    reason_codes: list[str] = []

    if estimated_damage_eur > 25_000:
        score += 45
        reason_codes.append("HIGH_ESTIMATED_DAMAGE")
    elif estimated_damage_eur > 10_000:
        score += 25

    if injury_reported:
        score += 30
        reason_codes.append("INJURY_REPORTED")

    if third_party_involved:
        score += 15
        reason_codes.append("THIRD_PARTY_INVOLVED")

    score = min(score, 100)
    return {"score": score, "label": _label(score), "reason_codes": reason_codes}


def score_fraud(
    *,
    policy_age_days: int,
    fnol_delay_days: int,
    police_report_available: bool,
    prior_claims_count: int,
) -> RuleScore:
    score = 15
    reason_codes: list[str] = []

    if policy_age_days < 30:
        score += 25
        reason_codes.append("POLICY_RECENTLY_STARTED")

    if fnol_delay_days > 21:
        score += 25
        reason_codes.append("LATE_FNOL")

    if not police_report_available:
        score += 15
        reason_codes.append("MISSING_POLICE_REPORT")

    if prior_claims_count >= 3:
        score += 25
        reason_codes.append("PRIOR_CLAIMS_HIGH")

    score = min(score, 100)
    return {"score": score, "label": _label(score), "reason_codes": reason_codes}


def score_litigation(
    *,
    injury_reported: bool,
    description: str,
    third_party_involved: bool,
) -> RuleScore:
    score = 10
    reason_codes: list[str] = []
    legal_keywords = ["lawyer", "attorney", "legal", "court", "lawsuit", "solicitor"]

    if injury_reported:
        score += 30
        reason_codes.append("INJURY_REPORTED")

    if any(keyword in description.lower() for keyword in legal_keywords):
        score += 30
        reason_codes.append("LEGAL_KEYWORDS_DETECTED")

    if third_party_involved:
        score += 15
        reason_codes.append("THIRD_PARTY_INVOLVED")

    score = min(score, 100)
    return {"score": score, "label": _label(score), "reason_codes": reason_codes}
