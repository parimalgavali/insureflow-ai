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
