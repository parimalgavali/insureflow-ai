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
