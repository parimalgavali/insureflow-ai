from fastapi.testclient import TestClient

from triage_service.app import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "triage-service"}


def test_score_endpoint_returns_rule_based_triage():
    client = TestClient(app)

    response = client.post(
        "/ai/v1/triage/score",
        json={
            "claim_id": "11111111-1111-1111-1111-111111111111",
            "claim_number": "CLM-20260625-000001",
            "policy_features": {
                "policy_type": "PERSONAL_AUTO",
                "policy_age_days": 12,
                "coverage_limit_amount": 25000.0,
                "deductible_amount": 500.0,
                "coverage_valid": True,
                "coverage_reasons": [],
            },
            "claim_features": {
                "claim_type": "AUTO_COLLISION",
                "estimated_loss_amount": 30000.0,
                "injury_reported": True,
                "third_party_involved": True,
                "police_report_available": False,
                "loss_report_delay_days": 25,
                "prior_claims_count": 0,
            },
            "text_features": {"loss_description": "Attorney contacted after injury collision."},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["modelName"] == "rule-based-triage"
    assert body["modelVersion"] == "rules-v1"
    assert body["severity"]["label"] == "HIGH"
    assert body["fraud"]["label"] in {"MEDIUM", "HIGH"}
    assert body["humanReviewRequired"] is True
