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

Each artifact folder contains:

- `model.joblib`
- `metadata.json`
- `metrics.json`

`ml/artifacts/` is generated locally and intentionally ignored by Git. Re-run the training command to recreate the artifacts for local demo or manual inspection.

The triage service loads artifacts from `ml/artifacts` when they exist. If one or both model artifacts are missing or invalid, the service falls back to the Phase 5 rule-based scorer and keeps the same API response contract.

These models are decision-support demos trained on synthetic, rule-labeled data. They are not production models and must not be used for real claim approval, denial, fraud accusation, legal advice, or medical advice.
