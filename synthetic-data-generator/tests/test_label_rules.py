from __future__ import annotations

from generator.rules import score_fraud, score_litigation, score_severity


def test_severity_is_high_for_large_damage_with_injury():
    result = score_severity(
        estimated_damage_eur=31_000,
        injury_reported=True,
        third_party_involved=False,
    )

    assert result["label"] == "HIGH"
    assert result["score"] >= 80
    assert "HIGH_ESTIMATED_DAMAGE" in result["reason_codes"]
    assert "INJURY_REPORTED" in result["reason_codes"]


def test_fraud_risk_rises_for_recent_policy_and_late_fnol():
    result = score_fraud(
        policy_age_days=12,
        fnol_delay_days=24,
        police_report_available=True,
        prior_claims_count=0,
    )

    assert result["label"] in {"MEDIUM", "HIGH"}
    assert result["score"] >= 45
    assert "POLICY_RECENTLY_STARTED" in result["reason_codes"]
    assert "LATE_FNOL" in result["reason_codes"]


def test_litigation_risk_rises_for_injury_with_legal_keywords():
    result = score_litigation(
        injury_reported=True,
        description="Customer mentioned lawyer review after the accident.",
        third_party_involved=False,
    )

    assert result["label"] in {"MEDIUM", "HIGH"}
    assert result["score"] >= 45
    assert "INJURY_REPORTED" in result["reason_codes"]
    assert "LEGAL_KEYWORDS_DETECTED" in result["reason_codes"]
