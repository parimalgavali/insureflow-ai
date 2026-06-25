from triage_service.rules import score_triage
from triage_service.schemas import (
    ClaimFeatures,
    PolicyFeatures,
    TextFeatures,
    TriageScoreRequest,
)


def make_request(**overrides):
    claim = {
        "claim_type": "AUTO_COLLISION",
        "estimated_loss_amount": 9000.0,
        "injury_reported": False,
        "third_party_involved": False,
        "police_report_available": True,
        "loss_report_delay_days": 2,
        "prior_claims_count": 0,
    }
    claim.update(overrides)
    return TriageScoreRequest(
        claim_id="11111111-1111-1111-1111-111111111111",
        claim_number="CLM-20260625-000001",
        policy_features=PolicyFeatures(
            policy_type="PERSONAL_AUTO",
            policy_age_days=120,
            coverage_limit_amount=25000.0,
            deductible_amount=500.0,
            coverage_valid=True,
            coverage_reasons=[],
        ),
        claim_features=ClaimFeatures(**claim),
        text_features=TextFeatures(loss_description="Rear-end collision at a stop light."),
    )


def test_high_severity_for_injury_and_large_loss():
    result = score_triage(make_request(estimated_loss_amount=45000.0, injury_reported=True))

    assert result.severity.label == "HIGH"
    assert "HIGH_ESTIMATED_DAMAGE" in result.severity.reason_codes
    assert "INJURY_REPORTED" in result.severity.reason_codes
    assert result.recommended_queue == "COMPLEX_CLAIMS"


def test_high_fraud_risk_for_recent_policy_late_fnol_and_missing_police_report():
    request = make_request(
        police_report_available=False,
        loss_report_delay_days=30,
        prior_claims_count=3,
    )
    request.policy_features.policy_age_days = 10

    result = score_triage(request)

    assert result.fraud.label == "HIGH"
    assert result.recommended_queue == "SIU_REVIEW"
    assert "POLICY_RECENTLY_STARTED" in result.fraud.reason_codes
    assert "LATE_FNOL" in result.fraud.reason_codes
    assert "MISSING_POLICE_REPORT" in result.fraud.reason_codes


def test_litigation_risk_for_legal_keywords():
    result = score_triage(make_request(injury_reported=True))
    request_with_legal_text = make_request(injury_reported=True)
    request_with_legal_text.text_features.loss_description = "Customer says an attorney may file a lawsuit."
    result_with_legal_text = score_triage(request_with_legal_text)

    assert result.litigation.label in {"LOW", "MEDIUM"}
    assert result_with_legal_text.litigation.label == "HIGH"
    assert "LEGAL_KEYWORDS_DETECTED" in result_with_legal_text.litigation.reason_codes
