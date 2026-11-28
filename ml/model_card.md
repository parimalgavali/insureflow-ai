# Model card — ClaimPilot fraud-risk signal (`hgb-v1`)

## Intended use
Decision support only. `ml.predict.load_scorer().score(facts, policy)` returns a
`RiskSignal(score, band, reasons)` (or `None` when minimum inputs are missing). The claim card
shows the signal as one input for human review. It never denies, approves, or accuses; the UI labels it as a signal and the agent
prompts forbid repeating it to the policyholder as a verdict. It is a portfolio demonstration of
honest, explainable tabular ML on real data — not a production fraud system.

## Data
Kaggle "Vehicle Insurance Fraud Detection" (`khusheekapoor/vehicle-insurance-fraud-detection`,
CC0): 15,420 US motor claims from 1994–1996, 923 labelled fraud (5.99%), 33 columns, no missing
values. Fetched by `scripts/fetch_data.py kaggle`; see `data/README.md` and `ml/eda_summary.md`.

## Features (14)
`Month`, `DayOfWeek`, `AccidentArea`, `Fault`, `VehicleCategory`, `VehiclePrice`,
`Days:Policy-Accident`, `Days:Policy-Claim`, `PastNumberOfClaims`, `AgeOfVehicle`,
`PoliceReportFiled`, `WitnessPresent`, `BasePolicy`, `Deductible`.

Some features use live claim and policy inputs; others remain documented assumptions.
Mapping (`ml/features.py::facts_to_features`): incident date → `Month`/`DayOfWeek`;
`event_type`/third-party facts → `Fault`; `police_report_filed` → `PoliceReportFiled`;
`witnesses` → `WitnessPresent`; `policy.product` → `BasePolicy`
(haftpflicht→Liability, vollkasko→All Perils, teilkasko→Collision — nearest category, not an
exact equivalent); `deductible_eur` → nearest of {300,400,500,700}; `vehicle_age_years` →
`AgeOfVehicle`.

## Minimum inputs and availability
`ml/risk_inputs.py` gates both the scorer and agent before prediction. Required: a valid
ISO incident date, a known incident type, explicit yes/no answers for third-party involvement,
police reporting and witnesses, a known policy product, and a finite nonnegative deductible.
A collision involving another party also needs a yes/no answer for whether that party is known.
“No” is a known answer; missing is not “No”. Missing inputs produce no score or band. The card
shows “Not enough information” and names the needed details, including on saved legacy cards.
A scoring service failure is separately labelled unavailable. Coverage guidance and human review
can proceed when the risk inputs are incomplete.

This is an operational minimum, not a statistical guarantee of reliability. Mapping still uses
`DEFAULTS` for area, vehicle category/price, policy timing and past claims, and for vehicle age
when absent. Incident/third-party categories are proxies for fault, not findings of liability.
Policy categories and deductible rounding are approximate. The minimum-input gate does not
resolve these limitations or the data mismatch described below.

## Excluded columns and why
- Fairness / protected attributes: `Sex`, `MaritalStatus`, `Age`, `AgeOfPolicyHolder`.
- Identifiers: `PolicyNumber`, `RepNumber`.
- Not observable in the conversation (would be constants at inference, i.e. fake signal):
  `Make`, `Year`, `PolicyType`, `AgentType`, `NumberOfSuppliments`, `AddressChange-Claim`,
  `NumberOfCars`, `DriverRating`. Note `AddressChange-Claim` is the single strongest predictor in
  this dataset (fraud rate 5%–75% across values); dropping it costs a lot of AUPRC and is deliberate.
- Claim-filing calendar fields (`WeekOfMonth`, `WeekOfMonthClaimed`, `DayOfWeekClaimed`,
  `MonthClaimed`): no plausible causal story, produced noise explanations ("reported on a Wednesday").

## Model
`HistGradientBoostingClassifier` (lr 0.05, ≤300 iters with early stopping, 15 leaves,
min 40 samples/leaf, L2 1.0, native categorical splits) behind an `OrdinalEncoder`; no class
re-weighting so `predict_proba` stays a usable probability. Seed 42. Trained on an 80% stratified
split; 20% held out.

## Results (held-out test, n = 3,084, 185 positives)

| model | AUPRC | ROC-AUC |
|---|---|---|
| majority class | 0.060 | 0.500 |
| logistic regression (one-hot) | 0.167 | 0.805 |
| **hgb-v1** | **0.205** | **0.813** |

5-fold CV on the training split: AUPRC 0.206 ± 0.035, ROC-AUC 0.814 ± 0.013.
Recall at precision ≥ 0.5 is only 0.022 (threshold 0.317): with the observable features alone
the model cannot isolate fraud with high precision — ranking (ROC-AUC 0.81) is useful, hard
classification is not. Calibration bins are in `ml/artifacts/metrics.json`.

## Bands
Cut-offs are score quantiles of the training set: `medium` ≥ 80th percentile (0.116),
`high` ≥ 95th percentile (0.188). They mean "top 20% / top 5% of claims by model score",
not "probably fraud". The base rate is 6%, so even a `high` claim is more likely legitimate.

## Explanations
`ml/explain.py`: for each feature, replace its value with the training baseline (mode/median)
and record the probability drop; the top three features with a drop ≥ 0.005 are phrased with a
fixed template map. This is a local sensitivity analysis, not Shapley values, and says nothing
about causality.

## Limitations
- 1990s US data applied to a German motor-claim conversation: covers, prices and reporting
  habits differ; `BasePolicy` mapping is approximate.
- Several inputs are defaults at inference (`AccidentArea`, `VehiclePrice`, `VehicleCategory`,
  `Days:Policy-*`, `PastNumberOfClaims`), so the model effectively uses ~7 live features.
- Small positive class → CV fold variance of ±0.035 AUPRC; treat differences < 0.04 as noise.
- Labels are "fraud found", i.e. detected fraud — undetected fraud is labelled legitimate.

## Reproduce
```
uv run python scripts/fetch_data.py kaggle   # needs KAGGLE_USERNAME / KAGGLE_KEY
uv run python -m ml.train                    # ~1 min CPU → ml/artifacts/{fraud_model.joblib,metrics.json}
uv run python -m ml.eda > ml/eda_summary.md
```
