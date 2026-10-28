"""Short EDA of the Kaggle vehicle-fraud data; output is committed as ml/eda_summary.md."""

from __future__ import annotations

import pandas as pd

from ml.features import EXCLUDED, FEATURES, TARGET, load_frame


def summarise(frame: pd.DataFrame) -> str:
    y = frame[TARGET] == "Yes"
    lines = [
        "# EDA summary — Kaggle vehicle insurance fraud (carclaims.csv)",
        "",
        f"- rows: {len(frame):,}; columns: {frame.shape[1]}",
        f"- fraud rate: {y.mean():.2%} ({y.sum():,} positives)",
        f"- years: {sorted(frame['Year'].unique())}",
        f"- missing values: {int(frame.isna().sum().sum())}",
        f"- `PolicyNumber` unique per row: {frame['PolicyNumber'].is_unique} (id → excluded)",
        "",
        "## Fraud rate by feature value (used features only)",
        "",
    ]
    for col in FEATURES:
        rates = (
            frame.groupby(col)[TARGET]
            .apply(lambda s: (s == "Yes").mean())
            .sort_values(ascending=False)
        )
        top = ", ".join(f"{k}: {v:.1%}" for k, v in rates.head(4).items())
        lines.append(f"- **{col}** ({frame[col].nunique()} values) — {top}")
    lines += [
        "",
        "## Excluded columns and their fraud-rate spread (why they are tempting but not used)",
        "",
    ]
    for col in EXCLUDED:
        if col in ("PolicyNumber",):
            continue
        rates = frame.groupby(col)[TARGET].apply(lambda s: (s == "Yes").mean())
        lines.append(f"- **{col}** — spread {rates.min():.1%} … {rates.max():.1%}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(summarise(load_frame()), end="")
