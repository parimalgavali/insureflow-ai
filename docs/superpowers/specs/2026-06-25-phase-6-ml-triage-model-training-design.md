# Phase 6 ML Triage Model Training Design

## Purpose

Phase 6 adds reproducible machine-learning severity and fraud-risk scoring to InsureFlow AI. The goal is to train baseline models from the project synthetic dataset, save auditable artifacts, document model limitations, and let the existing FastAPI triage service use ML predictions while preserving the Phase 5 rule-based fallback.

This phase is portfolio-oriented and local-first. It does not require Kaggle credentials, external downloads, private data, or paid services.

## Decision

Use a synthetic-data-first implementation.

The first ML version trains from:

- `data/synthetic/claims.csv`
- `data/synthetic/policies.csv`
- `data/synthetic/ai_triage_labels.csv`

Public fraud datasets remain a later enhancement. This keeps the demo deterministic, easy to review, and suitable for GitHub CI/local verification.

## Scope

Build in this phase:

- `ml/` Python package for data loading, feature engineering, training, metrics, and artifact metadata.
- Severity model trained as multiclass classification over `LOW`, `MEDIUM`, and `HIGH`.
- Fraud-risk model trained as risk classification over `LOW`, `MEDIUM`, and `HIGH`.
- Scikit-learn pipelines with preprocessing and baseline classifiers.
- Serialized model artifacts with `joblib`.
- Metrics JSON files for severity and fraud-risk models.
- Model cards in `docs/ml/`.
- Triage service ML inference module that loads artifacts when available.
- FastAPI triage endpoint that uses ML predictions when artifacts are present and falls back to rules when they are not.
- Tests for data loading, training smoke flow, artifact loading, prediction contracts, API ML mode, and fallback mode.
- Project memory and documentation updates.

Out of scope:

- Public/Kaggle dataset download.
- XGBoost/LightGBM dependency.
- MLflow tracking.
- Frontend model display.
- Backend database schema changes.
- Replacing litigation scoring with ML. Litigation remains rule-based in this phase.

## Architecture

Phase 6 keeps the existing Java backend contract stable. The backend still calls `POST /ai/v1/triage/score` on the triage service and receives the same response shape introduced in Phase 5.

The new ML layer sits inside Python:

```text
data/synthetic/*.csv
        |
        v
ml/ training package
        |
        v
ml/artifacts/
  severity/model.joblib
  severity/metrics.json
  severity/metadata.json
  fraud/model.joblib
  fraud/metrics.json
  fraud/metadata.json
        |
        v
ai-services/triage-service
  rules.py remains fallback
  ml_models.py loads artifacts
  app.py returns ML-backed triage response when artifacts load
```

The triage service should not fail startup if artifacts are missing. Missing artifacts mean rule-based mode.

## Model Design

### Severity

Problem type: multiclass classification.

Target:

```text
severity_label: LOW | MEDIUM | HIGH
```

Candidate features:

- `claim_type`
- `estimated_damage_eur`
- `injury_reported`
- `third_party_involved`
- `police_report_available`
- `loss_report_delay_days`
- `policy_age_days`
- `prior_claims_count`
- `product_type`
- `annual_premium_eur`
- `deductible_eur`
- `coverage_limit_eur`

Primary metrics:

- macro F1
- balanced accuracy
- per-class precision/recall/F1
- confusion matrix

### Fraud Risk

Problem type: multiclass risk classification for this phase.

Target:

```text
fraud_label: LOW | MEDIUM | HIGH
```

Candidate features:

- `policy_age_days`
- `loss_report_delay_days`
- `prior_claims_count`
- `estimated_damage_eur`
- `claim_type`
- `police_report_available`
- `third_party_involved`
- `injury_reported`
- `product_type`
- `deductible_eur`
- `coverage_limit_eur`

Primary metrics:

- macro F1
- balanced accuracy
- per-class precision/recall/F1
- confusion matrix

For responsible presentation, the model output remains "fraud risk". The application must not call a claim fraudulent or confirmed fraud.

## Artifact Contract

Each model artifact directory contains:

```text
model.joblib
metrics.json
metadata.json
```

`metadata.json` includes:

- `modelName`
- `modelVersion`
- `target`
- `labels`
- `featureColumns`
- `trainedAt`
- `trainingRows`
- `sourceDataset`

The model artifact is a scikit-learn pipeline that accepts a pandas DataFrame with the feature columns listed in metadata and exposes `predict` and `predict_proba`.

## Triage Service Behavior

When both severity and fraud artifacts load:

- Severity block comes from the severity ML model.
- Fraud block comes from the fraud-risk ML model.
- Litigation block continues to come from deterministic rules.
- Recommended queue uses the existing queue logic.
- Reason codes still come from rule-derived explanations so the response remains explainable.
- `modelName` is `ml-triage`.
- `modelVersion` combines the severity and fraud model versions.

When one or both artifacts are missing or invalid:

- The service uses the existing rule-based scorer.
- `modelName` and `modelVersion` remain the rule-based values.
- API behavior remains stable.

## Training Workflow

The local training command should be:

```bash
cd ml
python3 -m pip install -e ".[test]"
python3 -m insureflow_ml.train --data-dir ../data/synthetic --artifacts-dir artifacts
```

The command should train both models, write artifacts and metrics, and be deterministic for the same input dataset and random seed.

## Documentation

Add:

- `docs/ml/severity-model-card.md`
- `docs/ml/fraud-risk-model-card.md`
- `docs/ml/model-training.md`

Update:

- `README.md`
- `docs/README.md`
- `PROJECT_MEMORY.md`
- `scripts/run-tests.sh`

## Testing

Required tests:

- ML data loading builds a feature table with required columns.
- Training smoke test writes both model artifacts and metrics files.
- Artifact loader predicts valid labels and probabilities.
- Triage service uses ML mode when test artifacts are provided.
- Triage service falls back to rule mode when artifacts are absent.
- Full project script runs backend, synthetic generator, triage service, and ML tests.

## Risks And Mitigations

- Synthetic labels are rule-generated and may overstate model quality.
  - Mitigation: model cards explicitly document this limitation.
- Class imbalance may make `HIGH` labels sparse.
  - Mitigation: use stratified split when possible and report macro metrics.
- Artifacts may not be present in a clean checkout.
  - Mitigation: rules remain the default fallback.
- Scikit-learn dependency could slow install.
  - Mitigation: keep dependencies limited to `pandas`, `scikit-learn`, `joblib`, and `pytest`.

## Done Criteria

Phase 6 is complete when:

- ML tests pass.
- Triage service tests pass in rule fallback and ML artifact mode.
- `./scripts/run-tests.sh` passes.
- Model cards and training docs are committed.
- Project memory records Phase 6 implementation and verification.
