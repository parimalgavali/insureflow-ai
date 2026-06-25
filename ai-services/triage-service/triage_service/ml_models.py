from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd

from triage_service.rules import score_triage
from triage_service.schemas import RiskLabel, ScoreBlock, TriageScoreRequest, TriageScoreResponse


DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "ml" / "artifacts"
LABELS = ["LOW", "MEDIUM", "HIGH"]
FEATURE_COLUMNS = [
    "claim_type",
    "estimated_damage_eur",
    "injury_reported",
    "third_party_involved",
    "police_report_available",
    "loss_report_delay_days",
    "policy_age_days",
    "prior_claims_count",
    "product_type",
    "annual_premium_eur",
    "deductible_eur",
    "coverage_limit_eur",
]


@dataclass(frozen=True)
class LoadedModel:
    model_name: str
    model_version: str
    pipeline: object
    feature_columns: list[str]


def score_with_optional_ml(
    request: TriageScoreRequest,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
) -> TriageScoreResponse:
    base = score_triage(request)
    severity = _load_model(artifacts_dir / "severity")
    fraud = _load_model(artifacts_dir / "fraud")
    if severity is None or fraud is None:
        return base

    features = _feature_frame(request)
    severity_block = _predict_block(severity, features, base.severity.reason_codes)
    fraud_block = _predict_block(fraud, features, base.fraud.reason_codes)
    recommended_queue = _recommended_queue(severity_block.label, fraud_block.label, base.litigation.label)
    human_review_required = (
        RiskLabel.HIGH in {severity_block.label, fraud_block.label, base.litigation.label}
        or not request.policy_features.coverage_valid
        or recommended_queue != "STANDARD_CLAIMS"
    )
    return TriageScoreResponse(
        claim_id=request.claim_id,
        claim_number=request.claim_number,
        model_name="ml-triage",
        model_version=f"{severity.model_version}+{fraud.model_version}",
        severity=severity_block,
        fraud=fraud_block,
        litigation=base.litigation,
        recommended_queue=recommended_queue,
        human_review_required=human_review_required,
        explanation=(
            "ML triage assigned severity and fraud-risk labels with rule-based reason codes; "
            "litigation scoring remains rule-based. Signals are decision-support only."
        ),
    )


def _load_model(model_dir: Path) -> LoadedModel | None:
    try:
        metadata = json.loads((model_dir / "metadata.json").read_text())
        pipeline = joblib.load(model_dir / "model.joblib")
    except (FileNotFoundError, OSError, ValueError, KeyError):
        return None
    return LoadedModel(
        model_name=metadata["modelName"],
        model_version=metadata["modelVersion"],
        pipeline=pipeline,
        feature_columns=list(metadata["featureColumns"]),
    )


def _feature_frame(request: TriageScoreRequest) -> pd.DataFrame:
    return pd.DataFrame([{
        "claim_type": request.claim_features.claim_type,
        "estimated_damage_eur": request.claim_features.estimated_loss_amount,
        "injury_reported": request.claim_features.injury_reported,
        "third_party_involved": request.claim_features.third_party_involved,
        "police_report_available": request.claim_features.police_report_available,
        "loss_report_delay_days": request.claim_features.loss_report_delay_days,
        "policy_age_days": request.policy_features.policy_age_days,
        "prior_claims_count": request.claim_features.prior_claims_count,
        "product_type": request.policy_features.policy_type,
        "annual_premium_eur": 0,
        "deductible_eur": request.policy_features.deductible_amount,
        "coverage_limit_eur": request.policy_features.coverage_limit_amount,
    }])


def _predict_block(model: LoadedModel, features: pd.DataFrame, reason_codes: list[str]) -> ScoreBlock:
    label = str(model.pipeline.predict(features[model.feature_columns])[0])
    probabilities = model.pipeline.predict_proba(features[model.feature_columns])[0]
    classes = [str(value) for value in model.pipeline.classes_]
    probability_by_class = {risk_label: 0.0 for risk_label in LABELS}
    probability_by_class.update(
        {class_label: float(probability) for class_label, probability in zip(classes, probabilities)}
    )
    return ScoreBlock(
        label=RiskLabel(label),
        score=round(probability_by_class[label], 4),
        reason_codes=reason_codes,
    )


def _recommended_queue(severity: RiskLabel, fraud: RiskLabel, litigation: RiskLabel) -> str:
    if fraud == RiskLabel.HIGH:
        return "SIU_REVIEW"
    if severity == RiskLabel.HIGH or litigation == RiskLabel.HIGH:
        return "COMPLEX_CLAIMS"
    return "STANDARD_CLAIMS"
