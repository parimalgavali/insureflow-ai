from __future__ import annotations

from pathlib import Path

import pandas as pd


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

CATEGORICAL_FEATURES = ["claim_type", "product_type"]
NUMERIC_FEATURES = [column for column in FEATURE_COLUMNS if column not in CATEGORICAL_FEATURES]


def load_training_frame(data_dir: Path) -> pd.DataFrame:
    claims = pd.read_csv(data_dir / "claims.csv")
    policies = pd.read_csv(data_dir / "policies.csv")
    labels = pd.read_csv(data_dir / "ai_triage_labels.csv")

    frame = claims.merge(policies, on="policy_id", how="inner").merge(labels, on="claim_id", how="inner")
    frame["customer_id"] = frame["customer_id_x"]
    frame["loss_date"] = pd.to_datetime(frame["loss_date"])
    frame["reported_date"] = pd.to_datetime(frame["reported_date"])
    frame["start_date"] = pd.to_datetime(frame["start_date"])
    frame["loss_report_delay_days"] = (frame["reported_date"] - frame["loss_date"]).dt.days.clip(lower=0)
    frame["policy_age_days"] = (frame["loss_date"] - frame["start_date"]).dt.days.clip(lower=0)
    frame["prior_claims_count"] = _prior_claims_count(frame)

    for column in ["injury_reported", "third_party_involved", "police_report_available"]:
        frame[column] = frame[column].astype(bool)

    selected = frame[FEATURE_COLUMNS + ["severity_label", "fraud_label"]].copy()
    selected["severity_label"] = pd.Categorical(selected["severity_label"], categories=LABELS, ordered=True)
    selected["fraud_label"] = pd.Categorical(selected["fraud_label"], categories=LABELS, ordered=True)
    return selected


def _prior_claims_count(frame: pd.DataFrame) -> pd.Series:
    ordered = frame.sort_values(["customer_id", "reported_date", "claim_id"]).copy()
    ordered["prior_claims_count"] = ordered.groupby("customer_id").cumcount()
    return ordered.sort_index()["prior_claims_count"]
