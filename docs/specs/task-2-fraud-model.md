# Task 2 — Fraud-risk model

**Goal:** an honest, explainable fraud-risk model trained on the real Kaggle vehicle-fraud data, served as `predict(facts) -> RiskSignal`.

**Deliverables (`ml/`)**
- `notebooks/01_eda.ipynb`: class balance (6% positive), leakage check, feature distributions. Keep it short; conclusions go in the model card.
- `features.py`: column selection and **exclusions** (`Sex`, `MaritalStatus`, `Age`, `AgeOfPolicyHolder` for fairness; `PolicyNumber`, `RepNumber` as ids), categorical handling, and `facts_to_features(ClaimFacts) -> row` mapping from the conversation schema (with documented defaults for unknowns).
- `train.py`: stratified 5-fold CV `HistGradientBoostingClassifier` with class weights; held-out test; saves `artifacts/fraud_model.joblib` + `artifacts/metrics.json`.
- `evaluate.py`: AUPRC, ROC-AUC, recall at precision ≥ 0.5, calibration bins, confusion matrix at the chosen threshold; baseline comparison (majority class, logistic regression).
- `explain.py`: per-prediction top-3 feature contributions → plain-language reasons (template map, e.g. `Days_Policy_Claim` low → "reported quickly after the accident").
- `model_card.md`: intended use (decision support only), data, excluded features and why, metrics table, limitations (1990s US data; mapping gaps), threshold rationale.
- `predict.py`: `RiskSignal(score: float, band: "low"|"medium"|"high", reasons: list[str])`.

**Tests:** training smoke on a 1,000-row sample; deterministic predictions for fixed inputs; feature mapping covers every `ClaimFacts` field; excluded columns never reach the model.

**Done when:** `python -m ml.train` produces the artifact and model card numbers; AUPRC beats logistic regression baseline; `predict()` is importable from `api/`.

**Risks:** over-claiming — the card must state that the score is a signal, not a decision; small positive class → report CIs or at least fold variance.
