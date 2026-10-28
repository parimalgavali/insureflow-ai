# Model card — expected claim cost context (`fremtpl2-v1`)

## Intended use
Shows the adjuster what a claim for this policy profile *typically* costs, next to the risk
signal, so an estimate in the conversation can be read in context. It is never used to decide,
cap or flag anything, and the card labels it "context only".

## Data
OpenML `freMTPL2freq` (41214, 678,013 French motor third-party-liability policies, 2004–2005)
and `freMTPL2sev` (41215, 26,639 claim amounts), CC0. Exposure clipped to 1 year, `ClaimNb` to 4,
claim amounts capped at €100,000 for the Gamma fit (a handful of extreme claims otherwise dominate).

## Features
Live from `PolicyContext`: `vehicle_power`, `vehicle_age_years`, `driver_age`, `bonus_malus`.
Fixed at the portfolio median because the conversation cannot observe them: area code,
log population density, fuel type. Region and brand are not used (French-specific codes).

## Models (held-out 20% of policies)
Frequency — claims per policy-year, Poisson deviance (lower is better):

| model | deviance |
|---|---|
| null (portfolio mean) | 0.6274 |
| Poisson GLM | 0.6090 |
| **HistGradientBoosting (poisson)** | **0.5848** |

Severity — amount per claim, Gamma deviance:

| model | deviance |
|---|---|
| null (portfolio mean €1,864) | 1.4268 |
| **Gamma GLM** | **1.4255** |
| HistGradientBoosting (gamma) | 1.4380 |

Frequency is predictable from the profile (bonus-malus and driver age dominate); severity is
essentially not — the Gamma GLM barely beats the portfolio mean, so the per-claim figure shown is
close to €1,864 for everyone and the useful part of the context is the frequency.

Pure premium (frequency × severity) by decile of predicted cost on the held-out policies rises
from ≈ €58 to ≈ €437 observed per policy-year (predicted €72 → €679); ordering is right, the top
decile over-predicts. Full table in `ml/artifacts/severity_metrics.json`.

## Limitations
French TPL data applied to German motor claims; amounts are 2004–2005 euros without inflation
adjustment; TPL covers third-party damage while ClaimPilot's demo claims are own-damage (Kasko).
Treat the number as an order of magnitude.

## Reproduce
```
uv run python scripts/fetch_data.py openml
uv run python -m ml.severity     # ~2 min CPU → ml/artifacts/severity_model.joblib + severity_metrics.json
```
