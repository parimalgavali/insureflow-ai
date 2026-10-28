"""Train the fraud-risk model on the real Kaggle vehicle-fraud data.

    uv run python -m ml.train [--data data/raw/kaggle/carclaims.csv] [--out ml/artifacts]

Writes fraud_model.joblib (model + explanation baseline + band cut-offs) and metrics.json
(5-fold CV, held-out test, baselines). Numbers are copied into ml/model_card.md by hand.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

from ml.evaluate import evaluate
from ml.explain import baseline_row
from ml.features import CATEGORICAL, EXCLUDED, NUMERIC, SOURCE_FILE, load_frame, split_xy

SEED = 42
VERSION = "hgb-v1"


def make_model(seed: int = SEED) -> Pipeline:
    encode = ColumnTransformer(
        [
            (
                "cat",
                OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                CATEGORICAL,
            ),
            ("num", "passthrough", NUMERIC),
        ]
    )
    clf = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=300,
        max_leaf_nodes=15,
        min_samples_leaf=40,
        l2_regularization=1.0,
        categorical_features=list(range(len(CATEGORICAL))),
        early_stopping=True,
        validation_fraction=0.15,
        random_state=seed,
    )
    return Pipeline([("encode", encode), ("clf", clf)])


def make_logreg(seed: int = SEED) -> Pipeline:
    encode = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("num", "passthrough", NUMERIC),
        ]
    )
    return Pipeline(
        [("encode", encode), ("clf", LogisticRegression(max_iter=2000, C=0.5, random_state=seed))]
    )


def cross_validate(x: pd.DataFrame, y: pd.Series, seed: int = SEED, folds: int = 5) -> dict:
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    auprc, roc = [], []
    for train_idx, val_idx in skf.split(x, y):
        model = make_model(seed).fit(x.iloc[train_idx], y.iloc[train_idx])
        m = evaluate(y.iloc[val_idx], model.predict_proba(x.iloc[val_idx])[:, 1])
        auprc.append(m["auprc"])
        roc.append(m["roc_auc"])
    return {
        "folds": folds,
        "auprc_mean": round(float(np.mean(auprc)), 4),
        "auprc_std": round(float(np.std(auprc)), 4),
        "roc_auc_mean": round(float(np.mean(roc)), 4),
        "roc_auc_std": round(float(np.std(roc)), 4),
    }


def train(frame: pd.DataFrame, out: Path, seed: int = SEED, cv: bool = True) -> dict:
    assert not set(EXCLUDED) & set(frame.columns[frame.columns.isin(CATEGORICAL + NUMERIC)])
    x, y = split_xy(frame)
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.2, stratify=y, random_state=seed)

    model = make_model(seed).fit(x_tr, y_tr)
    p_te = model.predict_proba(x_te)[:, 1]
    p_tr = model.predict_proba(x_tr)[:, 1]
    test = evaluate(y_te, p_te)

    baselines = {
        "majority_class": evaluate(
            y_te, DummyClassifier(strategy="prior").fit(x_tr, y_tr).predict_proba(x_te)[:, 1]
        ),
        "logistic_regression": evaluate(
            y_te, make_logreg(seed).fit(x_tr, y_tr).predict_proba(x_te)[:, 1]
        ),
    }
    bands = {
        "medium": round(float(np.quantile(p_tr, 0.80)), 4),
        "high": round(float(np.quantile(p_tr, 0.95)), 4),
    }
    metrics = {
        "version": VERSION,
        "rows": int(len(frame)),
        "positive_rate": round(float(y.mean()), 4),
        "features": list(x.columns),
        "excluded": EXCLUDED,
        "cv": cross_validate(x_tr, y_tr, seed) if cv else None,
        "test": test,
        "baselines": baselines,
        "bands": bands,
    }
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "baseline": baseline_row(x_tr), "bands": bands, "version": VERSION},
        out / "fraud_model.joblib",
    )
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=SOURCE_FILE)
    parser.add_argument("--out", default="ml/artifacts")
    parser.add_argument("--no-cv", action="store_true")
    args = parser.parse_args()
    metrics = train(load_frame(args.data), Path(args.out), cv=not args.no_cv)
    t, b = metrics["test"], metrics["baselines"]
    print(f"rows={metrics['rows']} positives={metrics['positive_rate']:.3%}")
    if metrics["cv"]:
        c = metrics["cv"]
        print(f"cv  AUPRC={c['auprc_mean']:.3f}±{c['auprc_std']:.3f}", end=" ")
        print(f"ROC-AUC={c['roc_auc_mean']:.3f}±{c['roc_auc_std']:.3f}")
    print(f"test AUPRC={t['auprc']:.3f} ROC-AUC={t['roc_auc']:.3f}", end=" ")
    print(f"recall@P>=0.5={t['recall_at_precision_0.5']:.3f} thr={t['threshold']}")
    print(f"logreg AUPRC={b['logistic_regression']['auprc']:.3f}", end=" ")
    print(f"majority AUPRC={b['majority_class']['auprc']:.3f}")
    print(f"bands={metrics['bands']}")


if __name__ == "__main__":
    main()
