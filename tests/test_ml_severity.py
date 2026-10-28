from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from api.agent.schemas import PolicyContext
from ml.severity import ARTIFACT, FEATURES, load_estimator, prepare, train


def synthetic(n: int = 4000, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    freq = pd.DataFrame(
        {
            "IDpol": np.arange(n, dtype=float),
            "Exposure": rng.uniform(0.1, 1.0, n),
            "Area": rng.choice(list("ABCDEF"), n),
            "VehPower": rng.integers(4, 12, n),
            "VehAge": rng.integers(0, 20, n),
            "DrivAge": rng.integers(18, 85, n),
            "BonusMalus": rng.integers(50, 150, n),
            "VehBrand": "B1",
            "VehGas": rng.choice(["Regular", "Diesel"], n),
            "Density": rng.lognormal(5, 1.5, n),
            "Region": "R11",
        }
    )
    lam = (
        freq["Exposure"]
        * 0.05
        * np.exp(0.02 * (freq["BonusMalus"] - 50) - 0.01 * (freq["DrivAge"] - 18))
    )
    freq["ClaimNb"] = rng.poisson(lam)
    claimants = freq[freq["ClaimNb"] > 0]
    sev = pd.DataFrame(
        {"IDpol": np.repeat(claimants["IDpol"].to_numpy(), claimants["ClaimNb"].to_numpy())}
    )
    sev["ClaimAmount"] = rng.gamma(2.0, 900.0, len(sev))
    return freq, sev


def test_prepare_has_exactly_the_features():
    freq, _ = synthetic(50)
    x = prepare(freq)
    assert list(x.columns) == FEATURES
    assert x["AreaCode"].between(1, 6).all()


def test_train_smoke_and_estimator_direction(tmp_path: Path):
    metrics = train(*synthetic(), tmp_path)
    assert (tmp_path / "severity_model.joblib").exists()
    assert (
        metrics["frequency_poisson_deviance"]["hgb"]
        <= metrics["frequency_poisson_deviance"]["null"] * 1.05
    )
    est = load_estimator(tmp_path / "severity_model.joblib")
    young_malus = est.estimate(PolicyContext(driver_age=19, bonus_malus=140))
    old_bonus = est.estimate(PolicyContext(driver_age=60, bonus_malus=50))
    assert young_malus.claims_per_year > old_bonus.claims_per_year
    assert young_malus.annual_cost_eur == pytest.approx(
        young_malus.claims_per_year * young_malus.claim_eur, rel=1e-3
    )
    assert est.estimate(PolicyContext()) == est.estimate(PolicyContext())


@pytest.mark.skipif(not ARTIFACT.exists(), reason="trained artifact not present")
def test_committed_artifact_is_sane():
    est = load_estimator()
    c = est.estimate(
        PolicyContext(vehicle_age_years=3, vehicle_power=6, driver_age=40, bonus_malus=50)
    )
    assert 0.01 < c.claims_per_year < 1.0
    assert 500 < c.claim_eur < 10_000
    assert "freMTPL2" in c.basis
