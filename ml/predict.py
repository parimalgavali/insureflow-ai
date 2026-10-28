"""`load_scorer()` -> object with `.score(facts, policy) -> RiskSignal`; used by api/state.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from api.agent.schemas import RiskSignal
from ml.explain import top_reasons
from ml.features import facts_to_features, row_frame

ARTIFACT = Path(__file__).parent / "artifacts" / "fraud_model.joblib"


class FraudScorer:
    def __init__(self, bundle: dict[str, Any]):
        self.model = bundle["model"]
        self.baseline = bundle["baseline"]
        self.bands = bundle["bands"]  # {"medium": p80, "high": p95} score cut-offs
        self.version = bundle["version"]

    def band(self, score: float) -> str:
        if score >= self.bands["high"]:
            return "high"
        if score >= self.bands["medium"]:
            return "medium"
        return "low"

    def score(self, facts: Any, policy: Any) -> RiskSignal:
        row = row_frame(facts_to_features(facts, policy))
        p = float(self.model.predict_proba(row)[0, 1])
        return RiskSignal(
            score=round(p, 4),
            band=self.band(p),
            reasons=top_reasons(self.model, row, self.baseline),
            model_version=self.version,
        )


def load_scorer(path: Path = ARTIFACT) -> FraudScorer:
    return FraudScorer(joblib.load(path))
