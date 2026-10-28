"""Per-prediction top-k reasons.

Contribution of a feature = probability drop when that feature is replaced by its training-set
baseline (mode for categoricals, median for numerics). Model-agnostic, cheap for 18 features, and
honest about what it is: a local sensitivity, not a Shapley value.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ml.features import CATEGORICAL, FEATURES

REASONS: dict[str, dict[str, str] | str] = {
    "Fault": {
        "Policy Holder": "policyholder recorded as at fault",
        "Third Party": "third party recorded as at fault",
    },
    "BasePolicy": {
        "All Perils": "all-perils (Vollkasko-type) cover",
        "Collision": "collision-type cover",
        "Liability": "liability-only cover",
    },
    "PoliceReportFiled": {"No": "no police report filed", "Yes": "police report filed"},
    "WitnessPresent": {"No": "no witness present", "Yes": "witness present"},
    "AgeOfVehicle": "vehicle age ({value})",
    "VehiclePrice": "vehicle price band {value}",
    "VehicleCategory": "vehicle category {value}",
    "Deductible": "deductible of {value}",
    "Days:Policy-Accident": "accident {value} days after policy start",
    "Days:Policy-Claim": "claim {value} days after policy start",
    "PastNumberOfClaims": "{value} past claims",
    "AccidentArea": "{value} accident area",
    "Month": "incident month {value}",
    "DayOfWeek": "incident on a {value}",
}

MIN_DELTA = 0.005  # ignore features that move the probability by less than half a point


def baseline_row(x_train: pd.DataFrame) -> dict[str, Any]:
    base = {}
    for col in FEATURES:
        if col in CATEGORICAL:
            base[col] = str(x_train[col].mode().iloc[0])
        else:
            base[col] = float(x_train[col].median())
    return base


def phrase(feature: str, value: Any) -> str:
    template = REASONS.get(feature, "{feature} = {value}")
    if isinstance(template, dict):
        return template.get(str(value), f"{feature} = {value}")
    return template.format(value=value, feature=feature)


def contributions(model, row: pd.DataFrame, baseline: dict[str, Any]) -> list[tuple[str, float]]:
    p0 = float(model.predict_proba(row)[0, 1])
    out = []
    for col in FEATURES:
        if str(row.iloc[0][col]) == str(baseline[col]):
            continue
        alt = row.copy()
        alt.loc[alt.index[0], col] = baseline[col]
        delta = p0 - float(model.predict_proba(alt)[0, 1])
        out.append((col, delta))
    out.sort(key=lambda t: -t[1])
    return out


def top_reasons(model, row: pd.DataFrame, baseline: dict[str, Any], k: int = 3) -> list[str]:
    """Plain-language reasons for the features that pushed the score *up* the most."""
    reasons = []
    for col, delta in contributions(model, row, baseline):
        if delta < MIN_DELTA or len(reasons) >= k:
            break
        reasons.append(phrase(col, row.iloc[0][col]))
    return reasons
