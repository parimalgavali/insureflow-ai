"""Claim frequency × severity on freMTPL2 (OpenML 41214/41215) → expected claim cost for a profile.

    uv run python -m ml.severity   # train, print metrics, write ml/artifacts/severity_model.joblib

Frequency: ClaimNb per policy-year (Poisson). Severity: ClaimAmount per claim (Gamma).
Pure premium = frequency × severity. Shown in the claim card as *context* for the adjuster,
never as a decision. GLM baselines (PoissonRegressor / GammaRegressor) vs HistGradientBoosting
with the same loss, same features.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import GammaRegressor, PoissonRegressor
from sklearn.metrics import mean_gamma_deviance, mean_poisson_deviance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from api.agent.schemas import CostContext

FREQ_FILE = "data/processed/freMTPL2freq.parquet"
SEV_FILE = "data/processed/freMTPL2sev.parquet"
ARTIFACT = Path(__file__).parent / "artifacts" / "severity_model.joblib"
VERSION = "fremtpl2-v1"
SEED = 42

# Observable from PolicyContext → live; the rest are fixed at the portfolio median (documented).
LIVE = ["VehPower", "VehAge", "DrivAge", "BonusMalus"]
FIXED = ["AreaCode", "LogDensity", "Diesel"]
FEATURES = LIVE + FIXED
SEV_CAP = 100_000.0  # a handful of >100k claims dominate the Gamma fit; capped, not dropped


def load(freq_path: str = FREQ_FILE, sev_path: str = SEV_FILE) -> tuple[pd.DataFrame, pd.DataFrame]:
    freq = pd.read_parquet(freq_path)
    sev = pd.read_parquet(sev_path)
    return freq, sev


def prepare(freq: pd.DataFrame) -> pd.DataFrame:
    x = pd.DataFrame(index=freq.index)
    x["VehPower"] = freq["VehPower"].astype(float)
    x["VehAge"] = freq["VehAge"].astype(float).clip(upper=30)
    x["DrivAge"] = freq["DrivAge"].astype(float)
    x["BonusMalus"] = freq["BonusMalus"].astype(float).clip(upper=150)
    x["AreaCode"] = (
        freq["Area"].astype(str).map({c: i for i, c in enumerate("ABCDEF", 1)}).astype(float)
    )
    x["LogDensity"] = np.log1p(freq["Density"].astype(float))
    x["Diesel"] = (freq["VehGas"].astype(str) == "Diesel").astype(float)
    return x[FEATURES]


def _hgb(loss: str) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss=loss,
        learning_rate=0.05,
        max_iter=400,
        max_leaf_nodes=15,
        min_samples_leaf=200,
        l2_regularization=1.0,
        early_stopping=True,
        random_state=SEED,
    )


def train(freq: pd.DataFrame, sev: pd.DataFrame, out: Path) -> dict[str, Any]:
    freq = freq[freq["Exposure"] > 0].copy()
    freq["Exposure"] = freq["Exposure"].clip(upper=1.0)
    freq["ClaimNb"] = freq["ClaimNb"].astype(float).clip(upper=4)
    x = prepare(freq)
    rate = freq["ClaimNb"] / freq["Exposure"]
    w = freq["Exposure"]
    idx_tr, idx_te = train_test_split(np.arange(len(freq)), test_size=0.2, random_state=SEED)

    freq_glm = make_pipeline(StandardScaler(), PoissonRegressor(alpha=1e-4, max_iter=500))
    freq_glm.fit(x.iloc[idx_tr], rate.iloc[idx_tr], poissonregressor__sample_weight=w.iloc[idx_tr])
    freq_hgb = _hgb("poisson").fit(x.iloc[idx_tr], rate.iloc[idx_tr], sample_weight=w.iloc[idx_tr])
    f_metrics = {
        name: round(
            float(
                mean_poisson_deviance(
                    rate.iloc[idx_te], m.predict(x.iloc[idx_te]), sample_weight=w.iloc[idx_te]
                )
            ),
            4,
        )
        for name, m in {"glm": freq_glm, "hgb": freq_hgb}.items()
    }
    f_metrics["null"] = round(
        float(
            mean_poisson_deviance(
                rate.iloc[idx_te],
                np.full(len(idx_te), np.average(rate.iloc[idx_tr], weights=w.iloc[idx_tr])),
                sample_weight=w.iloc[idx_te],
            )
        ),
        4,
    )

    claims = sev.merge(freq[["IDpol"]].assign(_row=np.arange(len(freq))), on="IDpol", how="inner")
    claims = claims[claims["ClaimAmount"] > 0]
    xs = x.iloc[claims["_row"].to_numpy()].reset_index(drop=True)
    ys = claims["ClaimAmount"].clip(upper=SEV_CAP).to_numpy()
    in_train = np.isin(claims["_row"].to_numpy(), idx_tr)
    sev_glm = make_pipeline(StandardScaler(), GammaRegressor(alpha=1e-3, max_iter=500))
    sev_glm.fit(xs[in_train], ys[in_train])
    sev_hgb = _hgb("gamma").fit(xs[in_train], ys[in_train])
    s_metrics = {
        name: round(float(mean_gamma_deviance(ys[~in_train], m.predict(xs[~in_train]))), 4)
        for name, m in {"glm": sev_glm, "hgb": sev_hgb}.items()
    }
    s_metrics["null"] = round(
        float(mean_gamma_deviance(ys[~in_train], np.full((~in_train).sum(), ys[in_train].mean()))),
        4,
    )

    # Calibration on held-out policies: predicted vs observed cost per policy-year, by decile.
    freq_model = freq_hgb if f_metrics["hgb"] <= f_metrics["glm"] else freq_glm
    sev_model = sev_hgb if s_metrics["hgb"] <= s_metrics["glm"] else sev_glm
    te = freq.iloc[idx_te]
    pred_cost = freq_model.predict(x.iloc[idx_te]) * sev_model.predict(x.iloc[idx_te])
    observed = claims.groupby("_row")["ClaimAmount"].sum().reindex(idx_te).fillna(0.0).to_numpy()
    dec = pd.qcut(pred_cost, 10, labels=False, duplicates="drop")
    cal = (
        pd.DataFrame(
            {
                "dec": dec,
                "pred": pred_cost * te["Exposure"].to_numpy(),
                "obs": observed,
                "exp": te["Exposure"].to_numpy(),
            }
        )
        .groupby("dec")
        .agg(
            n=("exp", "size"),
            predicted=("pred", "sum"),
            observed=("obs", "sum"),
            exposure=("exp", "sum"),
        )
    )
    cal["predicted_per_year"] = (cal["predicted"] / cal["exposure"]).round(1)
    cal["observed_per_year"] = (cal["observed"] / cal["exposure"]).round(1)
    calibration = (
        cal[["n", "predicted_per_year", "observed_per_year"]]
        .reset_index()
        .to_dict(orient="records")
    )

    defaults = {c: float(x[c].median()) for c in FIXED}
    metrics = {
        "version": VERSION,
        "policies": int(len(freq)),
        "claims": int(len(claims)),
        "features_live": LIVE,
        "features_fixed_at_median": defaults,
        "frequency_poisson_deviance": f_metrics,
        "severity_gamma_deviance": s_metrics,
        "chosen": {"frequency": type(freq_model).__name__, "severity": type(sev_model).__name__},
        "pure_premium_calibration_by_decile": calibration,
        "portfolio_claim_eur": round(float(ys.mean()), 2),
    }
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "freq": freq_model,
            "sev": sev_model,
            "defaults": defaults,
            "version": VERSION,
            "portfolio_claim_eur": metrics["portfolio_claim_eur"],
        },
        out / "severity_model.joblib",
    )
    (out / "severity_metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


class CostEstimator:
    def __init__(self, bundle: dict[str, Any]):
        self.freq, self.sev = bundle["freq"], bundle["sev"]
        self.defaults, self.version = bundle["defaults"], bundle["version"]
        self.portfolio_claim_eur = bundle["portfolio_claim_eur"]

    def row(self, policy: Any) -> pd.DataFrame:
        r = dict(self.defaults)
        r["VehPower"] = float(getattr(policy, "vehicle_power", None) or 6)
        r["VehAge"] = float(min(getattr(policy, "vehicle_age_years", None) or 5, 30))
        r["DrivAge"] = float(getattr(policy, "driver_age", None) or 45)
        r["BonusMalus"] = float(min(getattr(policy, "bonus_malus", None) or 50, 150))
        return pd.DataFrame([r], columns=FEATURES)

    def estimate(self, policy: Any) -> CostContext:
        row = self.row(policy)
        f = float(self.freq.predict(row)[0])
        s = float(self.sev.predict(row)[0])
        return CostContext(
            claims_per_year=round(f, 4),
            claim_eur=round(s, 2),
            annual_cost_eur=round(f * s, 2),
            portfolio_claim_eur=self.portfolio_claim_eur,
            basis=f"freMTPL2 (French motor TPL, 2004–2005), {self.version}",
        )


def load_estimator(path: Path = ARTIFACT) -> CostEstimator:
    return CostEstimator(joblib.load(path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="ml/artifacts")
    args = parser.parse_args()
    m = train(*load(), Path(args.out))
    print(f"policies={m['policies']} claims={m['claims']}")
    print("frequency Poisson deviance:", m["frequency_poisson_deviance"])
    print("severity  Gamma deviance:  ", m["severity_gamma_deviance"])
    print("chosen:", m["chosen"], " portfolio claim €", m["portfolio_claim_eur"])
    for r in m["pure_premium_calibration_by_decile"]:
        print(f"  decile {r['dec']}: n={r['n']} predicted €{r['predicted_per_year']}", end=" ")
        print(f"observed €{r['observed_per_year']} per policy-year")


if __name__ == "__main__":
    main()
