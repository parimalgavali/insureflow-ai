from pathlib import Path
import sys

import pandas as pd

from triage_service.ml_models import _default_artifacts_dir, score_with_optional_ml
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


def test_default_artifacts_dir_can_be_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("INSUREFLOW_ML_ARTIFACTS_DIR", str(tmp_path / "artifacts"))

    assert _default_artifacts_dir() == tmp_path / "artifacts"


def test_score_with_optional_ml_uses_loaded_artifacts(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.append(str(repo_root / "ml"))
    from insureflow_ml.training import train_all

    train_all(_training_frame(), tmp_path, random_state=13)

    result = score_with_optional_ml(make_request(), artifacts_dir=tmp_path)

    assert result.model_name == "ml-triage"
    assert "severity-synthetic-v1" in result.model_version
    assert "fraud-risk-synthetic-v1" in result.model_version
    assert result.severity.label in {"LOW", "MEDIUM", "HIGH"}
    assert result.fraud.label in {"LOW", "MEDIUM", "HIGH"}
    assert result.litigation.reason_codes


def _training_frame() -> pd.DataFrame:
    labels = ["LOW", "MEDIUM", "HIGH"] * 4
    return pd.DataFrame([
        {
            "claim_type": "AUTO_COLLISION" if index % 2 == 0 else "GLASS_DAMAGE",
            "estimated_damage_eur": 8000 + index * 3500,
            "injury_reported": index % 3 == 0,
            "third_party_involved": index % 2 == 0,
            "police_report_available": index % 4 != 0,
            "loss_report_delay_days": index + 1,
            "policy_age_days": 120 + index * 15,
            "prior_claims_count": index % 3,
            "product_type": "PERSONAL_AUTO" if index % 2 == 0 else "HOME",
            "annual_premium_eur": 900 + index * 110,
            "deductible_eur": 250 + (index % 3) * 250,
            "coverage_limit_eur": 25000 + (index % 4) * 25000,
            "severity_label": labels[index],
            "fraud_label": labels[-index - 1],
        }
        for index in range(12)
    ])
