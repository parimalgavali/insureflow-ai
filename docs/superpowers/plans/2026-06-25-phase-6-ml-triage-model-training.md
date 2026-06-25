# Phase 6 ML Triage Model Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Train reproducible severity and fraud-risk ML models from the synthetic insurance dataset, save auditable artifacts, document limitations, and let the existing triage service use ML predictions with rule-based fallback.

**Architecture:** Add a standalone `ml/` Python package for feature engineering, training, metrics, artifact metadata, and artifact loading. Extend the FastAPI triage service through a narrow `ml_models.py` adapter so `POST /ai/v1/triage/score` keeps the Phase 5 response contract and falls back to `rules.py` when artifacts are absent.

**Tech Stack:** Python 3.12+, pandas, scikit-learn, joblib, pytest, FastAPI, Pydantic, Java 21/Spring Boot unchanged for this phase.

---

## Branch

Use this branch:

```bash
ml-triage-model-training
```

## Spec

Design spec:

```text
docs/superpowers/specs/2026-06-25-phase-6-ml-triage-model-training-design.md
```

## Scope Guard

Do not add Kaggle/public dataset download in this phase. Do not add XGBoost, LightGBM, MLflow, frontend UI, or backend schema changes. Litigation scoring stays rule-based.

## File Map

### Create

- `ml/pyproject.toml` - package metadata and ML/test dependencies.
- `ml/README.md` - local training and test commands.
- `ml/insureflow_ml/__init__.py` - package marker.
- `ml/insureflow_ml/features.py` - load synthetic CSVs and build model feature table.
- `ml/insureflow_ml/training.py` - train severity and fraud-risk pipelines, compute metrics, write artifacts.
- `ml/insureflow_ml/artifacts.py` - artifact metadata structures and model loading/prediction helpers.
- `ml/insureflow_ml/train.py` - CLI entrypoint for local training.
- `ml/tests/test_features.py` - feature table tests.
- `ml/tests/test_training.py` - training smoke/artifact tests.
- `ml/tests/test_artifacts.py` - artifact loading and prediction tests.
- `ai-services/triage-service/triage_service/ml_models.py` - optional ML scoring adapter.
- `ai-services/triage-service/tests/test_ml_models.py` - ML mode and fallback tests.
- `docs/ml/model-training.md` - training workflow documentation.
- `docs/ml/severity-model-card.md` - severity model card.
- `docs/ml/fraud-risk-model-card.md` - fraud-risk model card.

### Modify

- `ai-services/triage-service/pyproject.toml` - add `joblib`, `pandas`, and `scikit-learn` dependencies needed for artifact loading.
- `ai-services/triage-service/triage_service/app.py` - call ML adapter instead of calling rules directly.
- `ai-services/triage-service/tests/test_api.py` - assert rule fallback remains default without artifacts.
- `scripts/run-tests.sh` - run `ml` tests.
- `README.md` - add Phase 6 training commands.
- `docs/README.md` - link ML docs.
- `PROJECT_MEMORY.md` - record Phase 6 start, implementation, and verification.

---

## Task 1: ML Package Foundation

**Files:**
- Create: `ml/pyproject.toml`
- Create: `ml/README.md`
- Create: `ml/insureflow_ml/__init__.py`
- Create: `ml/insureflow_ml/features.py`
- Test: `ml/tests/test_features.py`

- [ ] **Step 1: Write failing feature-table test**

Create `ml/tests/test_features.py`:

```python
from pathlib import Path

from insureflow_ml.features import FEATURE_COLUMNS, load_training_frame


def test_load_training_frame_builds_model_features():
    frame = load_training_frame(Path("../data/sample"))

    assert not frame.empty
    assert set(FEATURE_COLUMNS).issubset(frame.columns)
    assert {"severity_label", "fraud_label"}.issubset(frame.columns)
    assert set(frame["severity_label"]).issubset({"LOW", "MEDIUM", "HIGH"})
    assert set(frame["fraud_label"]).issubset({"LOW", "MEDIUM", "HIGH"})
    assert frame["loss_report_delay_days"].min() >= 0
    assert frame["policy_age_days"].min() >= 0
    assert frame["prior_claims_count"].min() >= 0
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd ml
python3 -m pytest tests/test_features.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'insureflow_ml'`.

- [ ] **Step 3: Add package metadata**

Create `ml/pyproject.toml`:

```toml
[project]
name = "insureflow-ml"
version = "0.1.0"
description = "ML training utilities for InsureFlow AI triage models"
requires-python = ">=3.12"
dependencies = [
  "joblib>=1.4.0",
  "pandas>=2.2.0",
  "scikit-learn>=1.5.0",
]

[project.optional-dependencies]
test = [
  "pytest>=8.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

Create `ml/README.md`:

```markdown
# InsureFlow ML

Local-first ML training package for InsureFlow AI severity and fraud-risk models.

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m insureflow_ml.train --data-dir ../data/synthetic --artifacts-dir artifacts
```

The initial Phase 6 models train from synthetic project data. They are decision-support demos, not production insurance models.
```

Create `ml/insureflow_ml/__init__.py`:

```python
"""ML training utilities for InsureFlow AI."""
```

- [ ] **Step 4: Implement feature loading**

Create `ml/insureflow_ml/features.py`:

```python
from __future__ import annotations

from pathlib import Path

import pandas as pd


LABELS = ["LOW", "MEDIUM", "HIGH"]

FEATURE_COLUMNS = [
    "claim_type",
    "estimated_damage_eur",
    "injury_reported",
    "third_party_involved",
    "police_report_available",
    "loss_report_delay_days",
    "policy_age_days",
    "prior_claims_count",
    "product_type",
    "annual_premium_eur",
    "deductible_eur",
    "coverage_limit_eur",
]

CATEGORICAL_FEATURES = ["claim_type", "product_type"]
NUMERIC_FEATURES = [column for column in FEATURE_COLUMNS if column not in CATEGORICAL_FEATURES]


def load_training_frame(data_dir: Path) -> pd.DataFrame:
    claims = pd.read_csv(data_dir / "claims.csv")
    policies = pd.read_csv(data_dir / "policies.csv")
    labels = pd.read_csv(data_dir / "ai_triage_labels.csv")

    frame = claims.merge(policies, on="policy_id", how="inner").merge(labels, on="claim_id", how="inner")
    frame["loss_date"] = pd.to_datetime(frame["loss_date"])
    frame["reported_date"] = pd.to_datetime(frame["reported_date"])
    frame["start_date"] = pd.to_datetime(frame["start_date"])
    frame["loss_report_delay_days"] = (frame["reported_date"] - frame["loss_date"]).dt.days.clip(lower=0)
    frame["policy_age_days"] = (frame["loss_date"] - frame["start_date"]).dt.days.clip(lower=0)
    frame["prior_claims_count"] = _prior_claims_count(frame)

    for column in ["injury_reported", "third_party_involved", "police_report_available"]:
        frame[column] = frame[column].astype(bool)

    selected = frame[FEATURE_COLUMNS + ["severity_label", "fraud_label"]].copy()
    selected["severity_label"] = pd.Categorical(selected["severity_label"], categories=LABELS, ordered=True)
    selected["fraud_label"] = pd.Categorical(selected["fraud_label"], categories=LABELS, ordered=True)
    return selected


def _prior_claims_count(frame: pd.DataFrame) -> pd.Series:
    ordered = frame.sort_values(["customer_id", "reported_date", "claim_id"]).copy()
    ordered["prior_claims_count"] = ordered.groupby("customer_id").cumcount()
    return ordered.sort_index()["prior_claims_count"]
```

- [ ] **Step 5: Run test and verify it passes**

Run:

```bash
cd ml
python3 -m pytest tests/test_features.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add ml/pyproject.toml ml/README.md ml/insureflow_ml/__init__.py ml/insureflow_ml/features.py ml/tests/test_features.py
git commit -m "feat: add ml feature table foundation"
```

---

## Task 2: Training And Artifact Writing

**Files:**
- Create: `ml/insureflow_ml/training.py`
- Create: `ml/insureflow_ml/train.py`
- Test: `ml/tests/test_training.py`

- [ ] **Step 1: Write failing training smoke test**

Create `ml/tests/test_training.py`:

```python
import json
from pathlib import Path

from insureflow_ml.features import load_training_frame
from insureflow_ml.training import train_all


def test_train_all_writes_model_artifacts(tmp_path):
    frame = load_training_frame(Path("../data/sample"))

    results = train_all(frame, tmp_path, random_state=7)

    assert {result.target for result in results} == {"severity_label", "fraud_label"}
    for model_dir in [tmp_path / "severity", tmp_path / "fraud"]:
        assert (model_dir / "model.joblib").is_file()
        assert (model_dir / "metrics.json").is_file()
        assert (model_dir / "metadata.json").is_file()
        metrics = json.loads((model_dir / "metrics.json").read_text())
        assert "macroF1" in metrics
        assert "balancedAccuracy" in metrics
        assert "confusionMatrix" in metrics
        metadata = json.loads((model_dir / "metadata.json").read_text())
        assert metadata["labels"] == ["LOW", "MEDIUM", "HIGH"]
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd ml
python3 -m pytest tests/test_training.py -q
```

Expected: FAIL because `insureflow_ml.training` does not exist.

- [ ] **Step 3: Implement training module**

Create `ml/insureflow_ml/training.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from insureflow_ml.features import CATEGORICAL_FEATURES, FEATURE_COLUMNS, LABELS, NUMERIC_FEATURES


@dataclass(frozen=True)
class TrainingResult:
    target: str
    artifact_dir: Path
    macro_f1: float
    balanced_accuracy: float


def train_all(frame: pd.DataFrame, artifacts_dir: Path, random_state: int = 42) -> list[TrainingResult]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return [
        train_model(
            frame,
            target="severity_label",
            model_name="severity-random-forest",
            model_version="severity-synthetic-v1",
            artifact_dir=artifacts_dir / "severity",
            random_state=random_state,
        ),
        train_model(
            frame,
            target="fraud_label",
            model_name="fraud-risk-random-forest",
            model_version="fraud-risk-synthetic-v1",
            artifact_dir=artifacts_dir / "fraud",
            random_state=random_state,
        ),
    ]


def train_model(
    frame: pd.DataFrame,
    *,
    target: str,
    model_name: str,
    model_version: str,
    artifact_dir: Path,
    random_state: int,
) -> TrainingResult:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    x = frame[FEATURE_COLUMNS]
    y = frame[target].astype(str)
    stratify = y if y.value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=random_state,
        stratify=stratify,
    )

    pipeline = _pipeline(random_state)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    metrics = {
        "macroF1": round(float(f1_score(y_test, predictions, average="macro", zero_division=0)), 4),
        "balancedAccuracy": round(float(balanced_accuracy_score(y_test, predictions)), 4),
        "classificationReport": classification_report(
            y_test,
            predictions,
            labels=LABELS,
            zero_division=0,
            output_dict=True,
        ),
        "confusionMatrix": confusion_matrix(y_test, predictions, labels=LABELS).tolist(),
    }
    metadata = {
        "modelName": model_name,
        "modelVersion": model_version,
        "target": target,
        "labels": LABELS,
        "featureColumns": FEATURE_COLUMNS,
        "trainedAt": datetime.now(UTC).isoformat(),
        "trainingRows": int(len(frame)),
        "sourceDataset": "data/synthetic",
    }

    joblib.dump(pipeline, artifact_dir / "model.joblib")
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    return TrainingResult(
        target=target,
        artifact_dir=artifact_dir,
        macro_f1=metrics["macroF1"],
        balanced_accuracy=metrics["balancedAccuracy"],
    )


def _pipeline(random_state: int) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]), NUMERIC_FEATURES),
        ]
    )
    classifier = RandomForestClassifier(
        n_estimators=120,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_state,
    )
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])
```

- [ ] **Step 4: Add CLI entrypoint**

Create `ml/insureflow_ml/train.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from insureflow_ml.features import load_training_frame
from insureflow_ml.training import train_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Train InsureFlow AI triage ML models.")
    parser.add_argument("--data-dir", type=Path, default=Path("../data/synthetic"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    frame = load_training_frame(args.data_dir)
    results = train_all(frame, args.artifacts_dir, random_state=args.random_state)
    for result in results:
        print(
            f"{result.target}: macroF1={result.macro_f1:.4f} "
            f"balancedAccuracy={result.balanced_accuracy:.4f} "
            f"artifactDir={result.artifact_dir}"
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests and CLI**

Run:

```bash
cd ml
python3 -m pytest tests/test_training.py -q
python3 -m insureflow_ml.train --data-dir ../data/sample --artifacts-dir /tmp/insureflow-ml-artifacts
```

Expected: tests PASS and CLI prints one line for `severity_label` and one for `fraud_label`.

- [ ] **Step 6: Commit**

Run:

```bash
git add ml/insureflow_ml/training.py ml/insureflow_ml/train.py ml/tests/test_training.py
git commit -m "feat: train ml triage models"
```

---

## Task 3: Artifact Loading And Prediction Contract

**Files:**
- Create: `ml/insureflow_ml/artifacts.py`
- Test: `ml/tests/test_artifacts.py`

- [ ] **Step 1: Write failing artifact prediction test**

Create `ml/tests/test_artifacts.py`:

```python
from pathlib import Path

from insureflow_ml.artifacts import load_model_artifact
from insureflow_ml.features import load_training_frame
from insureflow_ml.training import train_all


def test_loaded_artifact_predicts_label_and_probabilities(tmp_path):
    frame = load_training_frame(Path("../data/sample"))
    train_all(frame, tmp_path, random_state=11)
    artifact = load_model_artifact(tmp_path / "severity")

    prediction = artifact.predict(frame.iloc[[0]])

    assert prediction.label in {"LOW", "MEDIUM", "HIGH"}
    assert 0.0 <= prediction.score <= 1.0
    assert set(prediction.class_probabilities) == {"LOW", "MEDIUM", "HIGH"}
    assert abs(sum(prediction.class_probabilities.values()) - 1.0) < 0.0001
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd ml
python3 -m pytest tests/test_artifacts.py -q
```

Expected: FAIL because `insureflow_ml.artifacts` does not exist.

- [ ] **Step 3: Implement artifact loader**

Create `ml/insureflow_ml/artifacts.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd


@dataclass(frozen=True)
class ModelPrediction:
    label: str
    score: float
    class_probabilities: dict[str, float]


@dataclass(frozen=True)
class ModelArtifact:
    model_name: str
    model_version: str
    target: str
    labels: list[str]
    feature_columns: list[str]
    pipeline: object

    def predict(self, frame: pd.DataFrame) -> ModelPrediction:
        features = frame[self.feature_columns]
        label = str(self.pipeline.predict(features)[0])
        probabilities = self.pipeline.predict_proba(features)[0]
        classes = [str(value) for value in self.pipeline.classes_]
        probability_by_class = {label: 0.0 for label in self.labels}
        probability_by_class.update(
            {class_label: round(float(probability), 4) for class_label, probability in zip(classes, probabilities)}
        )
        score = probability_by_class[label]
        return ModelPrediction(label=label, score=score, class_probabilities=probability_by_class)


def load_model_artifact(artifact_dir: Path) -> ModelArtifact:
    metadata = json.loads((artifact_dir / "metadata.json").read_text())
    pipeline = joblib.load(artifact_dir / "model.joblib")
    return ModelArtifact(
        model_name=metadata["modelName"],
        model_version=metadata["modelVersion"],
        target=metadata["target"],
        labels=list(metadata["labels"]),
        feature_columns=list(metadata["featureColumns"]),
        pipeline=pipeline,
    )
```

- [ ] **Step 4: Run artifact and ML tests**

Run:

```bash
cd ml
python3 -m pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add ml/insureflow_ml/artifacts.py ml/tests/test_artifacts.py
git commit -m "feat: load ml model artifacts"
```

---

## Task 4: Triage Service ML Adapter With Rule Fallback

**Files:**
- Modify: `ai-services/triage-service/pyproject.toml`
- Create: `ai-services/triage-service/triage_service/ml_models.py`
- Modify: `ai-services/triage-service/triage_service/app.py`
- Modify: `ai-services/triage-service/tests/test_api.py`
- Test: `ai-services/triage-service/tests/test_ml_models.py`

- [ ] **Step 1: Write failing fallback and ML-mode tests**

Create `ai-services/triage-service/tests/test_ml_models.py`:

```python
from triage_service.ml_models import score_with_optional_ml
from triage_service.schemas import (
    ClaimFeatures,
    PolicyFeatures,
    TextFeatures,
    TriageScoreRequest,
)


def make_request() -> TriageScoreRequest:
    return TriageScoreRequest(
        claim_id="11111111-1111-1111-1111-111111111111",
        claim_number="CLM-20260625-000001",
        policy_features=PolicyFeatures(
            policy_type="PERSONAL_AUTO",
            policy_age_days=12,
            coverage_limit_amount=25000.0,
            deductible_amount=500.0,
            coverage_valid=True,
            coverage_reasons=[],
        ),
        claim_features=ClaimFeatures(
            claim_type="AUTO_COLLISION",
            estimated_loss_amount=30000.0,
            injury_reported=True,
            third_party_involved=True,
            police_report_available=False,
            loss_report_delay_days=25,
            prior_claims_count=0,
        ),
        text_features=TextFeatures(loss_description="Attorney contacted after injury collision."),
    )


def test_score_with_optional_ml_falls_back_when_artifacts_are_missing(tmp_path):
    result = score_with_optional_ml(make_request(), artifacts_dir=tmp_path / "missing")

    assert result.model_name == "rule-based-triage"
    assert result.model_version == "rules-v1"
    assert result.severity.label == "HIGH"


def test_score_with_optional_ml_uses_loaded_artifacts(tmp_path):
    from pathlib import Path
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[3] / "ml"))
    from insureflow_ml.features import load_training_frame
    from insureflow_ml.training import train_all

    frame = load_training_frame(Path("../../../data/sample"))
    train_all(frame, tmp_path, random_state=13)

    result = score_with_optional_ml(make_request(), artifacts_dir=tmp_path)

    assert result.model_name == "ml-triage"
    assert "severity-synthetic-v1" in result.model_version
    assert "fraud-risk-synthetic-v1" in result.model_version
    assert result.severity.label in {"LOW", "MEDIUM", "HIGH"}
    assert result.fraud.label in {"LOW", "MEDIUM", "HIGH"}
    assert result.litigation.reason_codes
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd ai-services/triage-service
python3 -m pytest tests/test_ml_models.py -q
```

Expected: FAIL because `triage_service.ml_models` does not exist.

- [ ] **Step 3: Add triage service ML dependencies**

Modify `ai-services/triage-service/pyproject.toml` dependencies to include:

```toml
  "joblib>=1.4.0",
  "pandas>=2.2.0",
  "scikit-learn>=1.5.0",
```

- [ ] **Step 4: Implement ML adapter**

Create `ai-services/triage-service/triage_service/ml_models.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd

from triage_service.rules import score_triage
from triage_service.schemas import RiskLabel, ScoreBlock, TriageScoreRequest, TriageScoreResponse


DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "ml" / "artifacts"
LABELS = ["LOW", "MEDIUM", "HIGH"]
FEATURE_COLUMNS = [
    "claim_type",
    "estimated_damage_eur",
    "injury_reported",
    "third_party_involved",
    "police_report_available",
    "loss_report_delay_days",
    "policy_age_days",
    "prior_claims_count",
    "product_type",
    "annual_premium_eur",
    "deductible_eur",
    "coverage_limit_eur",
]


@dataclass(frozen=True)
class LoadedModel:
    model_name: str
    model_version: str
    pipeline: object
    feature_columns: list[str]


def score_with_optional_ml(
    request: TriageScoreRequest,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
) -> TriageScoreResponse:
    base = score_triage(request)
    severity = _load_model(artifacts_dir / "severity")
    fraud = _load_model(artifacts_dir / "fraud")
    if severity is None or fraud is None:
        return base

    features = _feature_frame(request)
    severity_block = _predict_block(severity, features, base.severity.reason_codes)
    fraud_block = _predict_block(fraud, features, base.fraud.reason_codes)
    recommended_queue = _recommended_queue(severity_block.label, fraud_block.label, base.litigation.label)
    human_review_required = (
        RiskLabel.HIGH in {severity_block.label, fraud_block.label, base.litigation.label}
        or not request.policy_features.coverage_valid
        or recommended_queue != "STANDARD_CLAIMS"
    )
    return TriageScoreResponse(
        claim_id=request.claim_id,
        claim_number=request.claim_number,
        model_name="ml-triage",
        model_version=f"{severity.model_version}+{fraud.model_version}",
        severity=severity_block,
        fraud=fraud_block,
        litigation=base.litigation,
        recommended_queue=recommended_queue,
        human_review_required=human_review_required,
        explanation=(
            "ML triage assigned severity and fraud-risk labels with rule-based reason codes; "
            "litigation scoring remains rule-based. Signals are decision-support only."
        ),
    )


def _load_model(model_dir: Path) -> LoadedModel | None:
    try:
        metadata = json.loads((model_dir / "metadata.json").read_text())
        pipeline = joblib.load(model_dir / "model.joblib")
    except (FileNotFoundError, OSError, ValueError, KeyError):
        return None
    return LoadedModel(
        model_name=metadata["modelName"],
        model_version=metadata["modelVersion"],
        pipeline=pipeline,
        feature_columns=list(metadata["featureColumns"]),
    )


def _feature_frame(request: TriageScoreRequest) -> pd.DataFrame:
    return pd.DataFrame([{
        "claim_type": request.claim_features.claim_type,
        "estimated_damage_eur": request.claim_features.estimated_loss_amount,
        "injury_reported": request.claim_features.injury_reported,
        "third_party_involved": request.claim_features.third_party_involved,
        "police_report_available": request.claim_features.police_report_available,
        "loss_report_delay_days": request.claim_features.loss_report_delay_days,
        "policy_age_days": request.policy_features.policy_age_days,
        "prior_claims_count": request.claim_features.prior_claims_count,
        "product_type": request.policy_features.policy_type,
        "annual_premium_eur": 0,
        "deductible_eur": request.policy_features.deductible_amount,
        "coverage_limit_eur": request.policy_features.coverage_limit_amount,
    }])


def _predict_block(model: LoadedModel, features: pd.DataFrame, reason_codes: list[str]) -> ScoreBlock:
    label = str(model.pipeline.predict(features[model.feature_columns])[0])
    probabilities = model.pipeline.predict_proba(features[model.feature_columns])[0]
    classes = [str(value) for value in model.pipeline.classes_]
    probability_by_class = {risk_label: 0.0 for risk_label in LABELS}
    probability_by_class.update(
        {class_label: float(probability) for class_label, probability in zip(classes, probabilities)}
    )
    return ScoreBlock(
        label=RiskLabel(label),
        score=round(probability_by_class[label], 4),
        reason_codes=reason_codes,
    )


def _recommended_queue(severity: RiskLabel, fraud: RiskLabel, litigation: RiskLabel) -> str:
    if fraud == RiskLabel.HIGH:
        return "SIU_REVIEW"
    if severity == RiskLabel.HIGH or litigation == RiskLabel.HIGH:
        return "COMPLEX_CLAIMS"
    return "STANDARD_CLAIMS"
```

- [ ] **Step 5: Wire API to optional ML adapter**

Modify `ai-services/triage-service/triage_service/app.py`:

```python
from fastapi import FastAPI

from triage_service.ml_models import score_with_optional_ml
from triage_service.schemas import TriageScoreRequest, TriageScoreResponse

app = FastAPI(title="InsureFlow AI Triage Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "triage-service"}


@app.post("/ai/v1/triage/score", response_model=TriageScoreResponse)
def score(request: TriageScoreRequest) -> TriageScoreResponse:
    return score_with_optional_ml(request)
```

- [ ] **Step 6: Update API fallback assertion**

In `ai-services/triage-service/tests/test_api.py`, keep `test_score_endpoint_returns_rule_based_triage` and assert:

```python
assert body["modelName"] == "rule-based-triage"
assert body["modelVersion"] == "rules-v1"
```

- [ ] **Step 7: Run triage service tests**

Run:

```bash
cd ai-services/triage-service
python3 -m pytest -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

Run:

```bash
git add ai-services/triage-service/pyproject.toml ai-services/triage-service/triage_service/app.py ai-services/triage-service/triage_service/ml_models.py ai-services/triage-service/tests/test_api.py ai-services/triage-service/tests/test_ml_models.py
git commit -m "feat: serve ml triage predictions with fallback"
```

---

## Task 5: Model Documentation And Project Memory

**Files:**
- Create: `docs/ml/model-training.md`
- Create: `docs/ml/severity-model-card.md`
- Create: `docs/ml/fraud-risk-model-card.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `PROJECT_MEMORY.md`
- Modify: `scripts/run-tests.sh`

- [ ] **Step 1: Document training workflow**

Create `docs/ml/model-training.md`:

```markdown
# ML Model Training

Phase 6 trains local, reproducible severity and fraud-risk models from the synthetic dataset.

```bash
cd ml
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m insureflow_ml.train --data-dir ../data/synthetic --artifacts-dir artifacts
```

Artifacts are written under:

```text
ml/artifacts/severity/
ml/artifacts/fraud/
```

Each artifact folder contains `model.joblib`, `metadata.json`, and `metrics.json`.

These models are decision-support demos trained on synthetic, rule-labeled data. They are not production models and must not be used for real claim approval, denial, fraud accusation, legal advice, or medical advice.
```

- [ ] **Step 2: Add severity model card**

Create `docs/ml/severity-model-card.md`:

```markdown
# Severity Model Card

## Model

- Name: `severity-random-forest`
- Version: `severity-synthetic-v1`
- Type: multiclass severity classifier
- Labels: `LOW`, `MEDIUM`, `HIGH`

## Intended Use

Decision support for routing synthetic claims in the InsureFlow AI portfolio demo.

## Not Intended For

Real insurance claim approval, denial, reserve setting, legal advice, medical advice, or fully automated decisions.

## Training Data

Synthetic claims, policies, and rule-generated triage labels from `data/synthetic`.

## Features

Claim type, estimated damage, injury flag, third-party flag, police report availability, FNOL delay, policy age, prior claims count, product type, premium, deductible, and coverage limit.

## Metrics

Metrics are generated during training in `ml/artifacts/severity/metrics.json`.

## Limitations

Labels are generated from deterministic rules, so model performance reflects the synthetic label logic rather than real claim outcomes.
```

- [ ] **Step 3: Add fraud-risk model card**

Create `docs/ml/fraud-risk-model-card.md`:

```markdown
# Fraud-Risk Model Card

## Model

- Name: `fraud-risk-random-forest`
- Version: `fraud-risk-synthetic-v1`
- Type: multiclass fraud-risk classifier
- Labels: `LOW`, `MEDIUM`, `HIGH`

## Intended Use

Decision support for prioritizing synthetic claims that may need additional human review.

## Not Intended For

Fraud accusation, claim denial, legal conclusions, customer scoring, or production insurance decisions.

## Training Data

Synthetic claims, policies, and rule-generated fraud-risk labels from `data/synthetic`.

## Features

Policy age, FNOL delay, prior claims count, estimated damage, claim type, police report availability, third-party flag, injury flag, product type, deductible, and coverage limit.

## Metrics

Metrics are generated during training in `ml/artifacts/fraud/metrics.json`.

## Limitations

The model predicts fraud risk labels generated by project rules. It does not detect real fraud and must not be presented as fraud confirmation.
```

- [ ] **Step 4: Update test script**

Modify `scripts/run-tests.sh` after the triage service block:

```bash
if [ -d "$ROOT_DIR/ml" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi

  (cd "$ROOT_DIR/ml" && "$PYTHON_BIN" -m pytest)
fi
```

- [ ] **Step 5: Update README and docs index**

In `README.md`, add an `ML Training` section with:

```markdown
## ML Training

```bash
cd ml
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m insureflow_ml.train --data-dir ../data/synthetic --artifacts-dir artifacts
```

Model training is documented in [docs/ml/model-training.md](docs/ml/model-training.md).
```

In `docs/README.md`, add links to:

```markdown
- [`ml/model-training.md`](ml/model-training.md) - Phase 6 local ML training workflow.
- [`ml/severity-model-card.md`](ml/severity-model-card.md) - severity model card.
- [`ml/fraud-risk-model-card.md`](ml/fraud-risk-model-card.md) - fraud-risk model card.
```

- [ ] **Step 6: Update project memory**

In `PROJECT_MEMORY.md`, add completed-work rows:

```markdown
| 2026-06-25 | Started Phase 6 ML triage model training. | Branch `ml-triage-model-training`; synthetic-data-first design spec and implementation plan created. |
| 2026-06-25 | Implemented Phase 6 ML training and triage serving. | Added `ml/` package, trained severity/fraud-risk artifact workflow, ML model cards, and triage service ML fallback behavior. |
```

Keep final verification row for Task 6 after running the full script.

- [ ] **Step 7: Commit**

Run:

```bash
git add docs/ml/model-training.md docs/ml/severity-model-card.md docs/ml/fraud-risk-model-card.md README.md docs/README.md PROJECT_MEMORY.md scripts/run-tests.sh
git commit -m "docs: document ml triage training"
```

---

## Task 6: Full Verification, Generated Artifacts, And Push

**Files:**
- Potentially modify: `PROJECT_MEMORY.md`
- Generated but usually not committed: `ml/artifacts/**`

- [ ] **Step 1: Train artifacts locally**

Run:

```bash
cd ml
python3 -m insureflow_ml.train --data-dir ../data/synthetic --artifacts-dir artifacts
```

Expected: command prints metric summaries for `severity_label` and `fraud_label`; `ml/artifacts/severity` and `ml/artifacts/fraud` exist.

- [ ] **Step 2: Decide artifact commit policy**

Default policy: do not commit `ml/artifacts/**` unless artifacts are small and intentionally useful for demo mode. If committing artifacts, add a short note in `docs/ml/model-training.md` explaining that they are synthetic demo artifacts.

Recommended first pass: keep artifacts generated locally and ignored if they are not already ignored. Add `ml/artifacts/` to `.gitignore` if needed.

- [ ] **Step 3: Run full verification**

Run:

```bash
./scripts/run-tests.sh
git diff --check
```

Expected:

- Backend tests PASS.
- Synthetic generator tests PASS.
- Triage service tests PASS.
- ML tests PASS.
- `git diff --check` has no output.

- [ ] **Step 4: Record verification in project memory**

Add row to `PROJECT_MEMORY.md`:

```markdown
| 2026-06-25 | Verified Phase 6 locally. | `./scripts/run-tests.sh` passed: backend, synthetic generator, triage service, and ML tests. |
```

- [ ] **Step 5: Commit verification/memory cleanup**

Run:

```bash
git add PROJECT_MEMORY.md .gitignore
git commit -m "docs: record phase 6 verification"
```

If `.gitignore` was not changed, omit it from `git add`.

- [ ] **Step 6: Push branch**

Run:

```bash
git status --short --branch
git push -u origin ml-triage-model-training
```

Expected: clean working tree and remote branch pushed.

---

## Self-Review Notes

- Spec coverage: Tasks cover ML package, feature table, training, artifacts, triage service integration, fallback behavior, docs, memory, and verification.
- Scope: Public datasets, XGBoost/LightGBM, MLflow, frontend, and backend schema changes remain out of scope.
- Type consistency: Model labels stay `LOW`, `MEDIUM`, `HIGH`; triage API response keeps Phase 5 `TriageScoreResponse`.
- Responsible AI wording: Fraud outputs are always fraud-risk signals, never fraud determinations.
