from pathlib import Path
import sys

from triage_service.ml_models import score_with_optional_ml
from triage_service.schemas import (
    ClaimFeatures,
    PolicyFeatures,
    TextFeatures,
    TriageScoreRequest,
)


def make_request() -> TriageScoreRequest:
    return TriageScoreRequest(
        claim_id="11111111-1111-1111-1111-111111111111",
        claim_number="CLM-20260625-000001",
        policy_features=PolicyFeatures(
            policy_type="PERSONAL_AUTO",
            policy_age_days=12,
            coverage_limit_amount=25000.0,
            deductible_amount=500.0,
            coverage_valid=True,
            coverage_reasons=[],
        ),
        claim_features=ClaimFeatures(
            claim_type="AUTO_COLLISION",
            estimated_loss_amount=30000.0,
            injury_reported=True,
            third_party_involved=True,
            police_report_available=False,
            loss_report_delay_days=25,
            prior_claims_count=0,
        ),
        text_features=TextFeatures(loss_description="Attorney contacted after injury collision."),
    )


def test_score_with_optional_ml_falls_back_when_artifacts_are_missing(tmp_path):
    result = score_with_optional_ml(make_request(), artifacts_dir=tmp_path / "missing")

    assert result.model_name == "rule-based-triage"
    assert result.model_version == "rules-v1"
    assert result.severity.label == "HIGH"


def test_score_with_optional_ml_uses_loaded_artifacts(tmp_path):
    sys.path.append(str(Path(__file__).resolve().parents[3] / "ml"))
    from insureflow_ml.features import load_training_frame
    from insureflow_ml.training import train_all

    frame = load_training_frame(Path("../../data/sample"))
    train_all(frame, tmp_path, random_state=13)

    result = score_with_optional_ml(make_request(), artifacts_dir=tmp_path)

    assert result.model_name == "ml-triage"
    assert "severity-synthetic-v1" in result.model_version
    assert "fraud-risk-synthetic-v1" in result.model_version
    assert result.severity.label in {"LOW", "MEDIUM", "HIGH"}
    assert result.fraud.label in {"LOW", "MEDIUM", "HIGH"}
    assert result.litigation.reason_codes
