# InsureFlow ML

Local-first ML training package for InsureFlow AI severity and fraud-risk models.

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m insureflow_ml.train --data-dir ../data/synthetic --artifacts-dir artifacts
```

The initial Phase 6 models train from synthetic project data. They are decision-support demos, not production insurance models.
