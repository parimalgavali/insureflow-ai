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
