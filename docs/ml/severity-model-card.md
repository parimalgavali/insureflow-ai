# Severity Model Card

## Model

- Name: `severity-random-forest`
- Version: `severity-synthetic-v1`
- Type: multiclass severity classifier
- Labels: `LOW`, `MEDIUM`, `HIGH`

## Intended Use

Decision support for routing synthetic claims in the InsureFlow AI portfolio demo.

## Not Intended For

Real insurance claim approval, denial, reserve setting, legal advice, medical advice, or fully automated decisions.

## Training Data

Synthetic claims, policies, and rule-generated triage labels from `data/synthetic`.

## Features

Claim type, estimated damage, injury flag, third-party flag, police report availability, FNOL delay, policy age, prior claims count, product type, premium, deductible, and coverage limit.

## Metrics

Metrics are generated during training in `ml/artifacts/severity/metrics.json`.

## Limitations

Labels are generated from deterministic rules, so model performance reflects the synthetic label logic rather than real claim outcomes.
