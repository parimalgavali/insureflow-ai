"""Metrics for an imbalanced binary classifier (6% positives)."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)

MIN_PRECISION = 0.5


def recall_at_precision(y: np.ndarray, p: np.ndarray, min_precision: float = MIN_PRECISION):
    """Highest recall reachable while precision >= min_precision, and the threshold doing it."""
    precision, recall, thresholds = precision_recall_curve(y, p)
    ok = precision[:-1] >= min_precision
    if not ok.any():
        return 0.0, None
    idx = int(np.argmax(np.where(ok, recall[:-1], -1.0)))
    return float(recall[idx]), float(thresholds[idx])


def calibration_bins(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> list[dict]:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        mask = (p >= lo) & (p < hi if hi < 1.0 else p <= hi)
        if mask.sum() == 0:
            continue
        out.append(
            {
                "bin": f"{lo:.1f}-{hi:.1f}",
                "n": int(mask.sum()),
                "mean_predicted": round(float(p[mask].mean()), 4),
                "observed_rate": round(float(y[mask].mean()), 4),
            }
        )
    return out


def evaluate(y, p, threshold: float | None = None) -> dict:
    y = np.asarray(y)
    p = np.asarray(p)
    rec, thr = recall_at_precision(y, p)
    threshold = threshold if threshold is not None else (thr if thr is not None else 0.5)
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "n": int(len(y)),
        "positives": int(y.sum()),
        "auprc": round(float(average_precision_score(y, p)), 4),
        "roc_auc": round(float(roc_auc_score(y, p)), 4),
        "recall_at_precision_0.5": round(rec, 4),
        "threshold": round(float(threshold), 4),
        "confusion_at_threshold": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "precision_at_threshold": round(float(tp / (tp + fp)) if tp + fp else 0.0, 4),
        "calibration": calibration_bins(y, p),
    }
