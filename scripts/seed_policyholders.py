"""Sample a small, deterministic set of realistic policyholders from freMTPL2freq.

The sample feeds the demo: driver age, vehicle age/power, bonus-malus and region
for the policyholder persona in a conversation. Run after `fetch_data.py openml`.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FREQ_PARQUET = REPO_ROOT / "data" / "processed" / "freMTPL2freq.parquet"
SEED_CSV = REPO_ROOT / "data" / "processed" / "seed_policyholders.csv"

SEED_COLUMNS = [
    "IDpol",
    "DrivAge",
    "VehAge",
    "VehPower",
    "BonusMalus",
    "VehBrand",
    "VehGas",
    "Area",
    "Region",
    "Density",
    "Exposure",
    "ClaimNb",
]
DEFAULT_N = 50
DEFAULT_SEED = 42


def sample_seed(frame, n: int = DEFAULT_N, seed: int = DEFAULT_SEED):
    """Return *n* rows with the seed columns, sorted by IDpol, reproducible for a given seed.

    Only full-year-ish policies (Exposure >= 0.5) with plausible driver ages are kept so the
    personas read naturally in a demo.
    """
    missing = [c for c in SEED_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"freMTPL2freq is missing columns: {missing}")
    eligible = frame[(frame["Exposure"] >= 0.5) & (frame["DrivAge"].between(18, 85))]
    if len(eligible) < n:
        raise ValueError(f"Only {len(eligible)} eligible rows, need {n}")
    sample = eligible.sample(n=n, random_state=seed)[SEED_COLUMNS]
    sample = sample.sort_values("IDpol").reset_index(drop=True)
    sample["IDpol"] = sample["IDpol"].astype("int64")
    return sample


def write_seed(
    freq_parquet: Path = FREQ_PARQUET,
    out_csv: Path = SEED_CSV,
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
) -> Path:
    import pandas as pd

    if not freq_parquet.exists():
        raise FileNotFoundError(
            f"{freq_parquet} not found; run `python scripts/fetch_data.py openml` first"
        )
    frame = pd.read_parquet(freq_parquet)
    sample = sample_seed(frame, n=n, seed=seed)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(out_csv, index=False)
    print(f"[seed] {len(sample)} policyholders -> {out_csv}")
    return out_csv


if __name__ == "__main__":
    try:
        write_seed()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
