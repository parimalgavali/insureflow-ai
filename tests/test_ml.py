from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from api.agent.schemas import ClaimFacts, PolicyContext
from ml.features import (
    CATEGORICAL,
    DEFAULTS,
    EXCLUDED,
    FEATURES,
    NUMERIC,
    TARGET,
    facts_to_features,
    split_xy,
)
from ml.predict import ARTIFACT, load_scorer
from ml.train import train

CATEGORIES = {
    "Month": ["Jan", "Feb", "Mar", "Dec"],
    "DayOfWeek": ["Monday", "Friday", "Sunday"],
    "AccidentArea": ["Urban", "Rural"],
    "Fault": ["Policy Holder", "Third Party"],
    "VehicleCategory": ["Sedan", "Sport", "Utility"],
    "VehiclePrice": ["less than 20,000", "20,000 to 29,000", "more than 69,000"],
    "Days:Policy-Accident": ["more than 30", "none"],
    "Days:Policy-Claim": ["more than 30", "none"],
    "PastNumberOfClaims": ["none", "1", "2 to 4"],
    "AgeOfVehicle": ["new", "3 years", "more than 7"],
    "PoliceReportFiled": ["No", "Yes"],
    "WitnessPresent": ["No", "Yes"],
    "BasePolicy": ["Liability", "Collision", "All Perils"],
}


def synthetic_frame(n: int = 1000, seed: int = 0) -> pd.DataFrame:
    """Same schema as carclaims.csv (incl. excluded columns) with a planted signal on Fault/BasePolicy."""
    rng = np.random.default_rng(seed)
    data = {col: rng.choice(vals, n) for col, vals in CATEGORIES.items()}
    # skew so the explanation baseline (mode) is the low-risk value
    data["Fault"] = rng.choice(["Policy Holder", "Third Party"], n, p=[0.3, 0.7])
    data["BasePolicy"] = rng.choice(["Liability", "Collision", "All Perils"], n, p=[0.6, 0.2, 0.2])
    data["Deductible"] = rng.choice([300, 400, 500, 700], n)
    for col in EXCLUDED:
        data[col] = rng.integers(0, 5, n)
    logit = (
        -3.0 + 1.5 * (data["Fault"] == "Policy Holder") + 1.0 * (data["BasePolicy"] == "All Perils")
    )
    data[TARGET] = np.where(rng.random(n) < 1 / (1 + np.exp(-logit)), "Yes", "No")
    return pd.DataFrame(data)


def test_excluded_columns_never_reach_model():
    assert not set(EXCLUDED) & set(FEATURES)
    x, y = split_xy(synthetic_frame(50))
    assert list(x.columns) == FEATURES
    assert y.isin([0, 1]).all()


def test_training_smoke(tmp_path: Path):
    metrics = train(synthetic_frame(1000), tmp_path, cv=False)
    assert (tmp_path / "fraud_model.joblib").exists()
    assert (tmp_path / "metrics.json").exists()
    assert metrics["test"]["roc_auc"] > 0.6
    assert metrics["test"]["auprc"] > metrics["baselines"]["majority_class"]["auprc"]
    scorer = load_scorer(tmp_path / "fraud_model.joblib")
    at_fault = scorer.score(ClaimFacts(event_type="collision"), PolicyContext(product="vollkasko"))
    not_at_fault = scorer.score(
        ClaimFacts(event_type="hit_and_run"), PolicyContext(product="haftpflicht")
    )
    assert at_fault.score > not_at_fault.score
    assert at_fault.band in ("low", "medium", "high")
    assert 0 < len(at_fault.reasons) <= 3
    assert any("at fault" in r for r in at_fault.reasons)


def test_facts_mapping_covers_every_fact_field_and_defaults():
    today = date(2026, 10, 27)
    row = facts_to_features(ClaimFacts(), PolicyContext(), today=today)
    assert set(row) == set(FEATURES)
    for col, default in DEFAULTS.items():
        assert row[col] == default

    full = ClaimFacts(
        incident_date="2026-10-24",
        incident_time="18:30",
        location="Köln",
        event_type="collision",
        description="x",
        third_party_involved=True,
        third_party_known=True,
        injuries=False,
        police_report_filed=True,
        witnesses=True,
        damage_description="bumper",
        estimated_amount_eur=1200.0,
        vehicle_drivable=True,
        photos_attached=True,
    )
    assert set(full.model_fields) <= set(ClaimFacts.model_fields)  # every field constructed above
    row = facts_to_features(
        full,
        PolicyContext(product="haftpflicht", deductible_eur=450, vehicle_age_years=0),
        today=today,
    )
    assert row["Month"] == "Oct" and row["DayOfWeek"] == "Saturday"
    assert row["Fault"] == "Third Party"
    assert row["PoliceReportFiled"] == "Yes" and row["WitnessPresent"] == "Yes"
    assert (
        row["BasePolicy"] == "Liability"
        and row["Deductible"] == 400
        and row["AgeOfVehicle"] == "new"
    )
    for col in CATEGORICAL:
        assert isinstance(row[col], str)
    for col in NUMERIC:
        assert isinstance(row[col], int)


@pytest.mark.skipif(not ARTIFACT.exists(), reason="trained artifact not present")
def test_committed_artifact_is_deterministic():
    scorer = load_scorer()
    facts = ClaimFacts(
        incident_date="2026-10-25", event_type="hit_and_run", third_party_involved=True
    )
    a = scorer.score(facts, PolicyContext())
    b = scorer.score(facts, PolicyContext())
    assert a == b
    assert a.model_version == "hgb-v1"
    assert 0.0 <= a.score <= 1.0
