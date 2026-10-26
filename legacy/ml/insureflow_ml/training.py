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
from sklearn.metrics import classification_report, confusion_matrix, f1_score, recall_score
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
        "balancedAccuracy": round(float(recall_score(y_test, predictions, labels=LABELS, average="macro", zero_division=0)), 4),
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
