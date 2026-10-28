from __future__ import annotations

from pathlib import Path

import pytest

from scripts.seed_policyholders import SEED_COLUMNS, sample_seed, write_seed

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")


def make_freq(n: int = 500, seed: int = 0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "IDpol": np.arange(1, n + 1),
            "ClaimNb": rng.integers(0, 3, n),
            "Exposure": rng.uniform(0.05, 1.0, n),
            "Area": rng.choice(list("ABCDEF"), n),
            "VehPower": rng.integers(4, 12, n),
            "VehAge": rng.integers(0, 20, n),
            "DrivAge": rng.integers(18, 95, n),
            "BonusMalus": rng.integers(50, 150, n),
            "VehBrand": rng.choice(["B1", "B2", "B12"], n),
            "VehGas": rng.choice(["Regular", "Diesel"], n),
            "Density": rng.integers(10, 20000, n),
            "Region": rng.choice(["R11", "R24", "R82"], n),
        }
    )


def test_sample_seed_is_deterministic_and_shaped():
    frame = make_freq()
    a = sample_seed(frame, n=50, seed=42)
    b = sample_seed(frame, n=50, seed=42)
    c = sample_seed(frame, n=50, seed=7)
    assert a.equals(b)
    assert not a.equals(c)
    assert len(a) == 50 and list(a.columns) == SEED_COLUMNS
    assert a["IDpol"].is_monotonic_increasing
    assert (a["Exposure"] >= 0.5).all() and a["DrivAge"].between(18, 85).all()


def test_sample_seed_requires_columns():
    with pytest.raises(ValueError, match="missing columns"):
        sample_seed(make_freq().drop(columns=["BonusMalus"]))


def test_sample_seed_requires_enough_eligible_rows():
    with pytest.raises(ValueError, match="eligible rows"):
        sample_seed(make_freq(n=30))


def test_write_seed_round_trip(tmp_path: Path):
    parquet = tmp_path / "freq.parquet"
    make_freq().to_parquet(parquet, index=False)
    out = write_seed(parquet, tmp_path / "seed.csv", n=10)
    back = pd.read_csv(out)
    assert len(back) == 10 and list(back.columns) == SEED_COLUMNS


def test_write_seed_missing_input(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="fetch_data.py openml"):
        write_seed(tmp_path / "nope.parquet", tmp_path / "seed.csv")
