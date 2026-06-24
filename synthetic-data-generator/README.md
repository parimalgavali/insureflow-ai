# Synthetic Data Generator

Synthetic insurance data generation for InsureFlow AI.

The generator creates deterministic, relational P&C motor insurance demo data for local development, portfolio demos, and future AI/ML experiments.

## Privacy

All generated records are synthetic. They must not be treated as real customer, policy, claim, medical, legal, or fraud data.

## Setup

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install 'pytest>=8.0'
```

## Test

```bash
cd synthetic-data-generator
../.venv/bin/python -m pytest
```

## Generate Demo Data

```bash
cd synthetic-data-generator
../.venv/bin/python -m generator --customers 500 --policies 650 --claims 200 --adjusters 25 --seed 42 --output-dir ../data/synthetic
```

Or from the repository root:

```bash
./scripts/generate-demo-data.sh
```

## Output Files

- `customers.csv`
- `policies.csv`
- `coverages.csv`
- `claims.csv`
- `claim_documents.csv`
- `claim_notes.csv`
- `claim_events.csv`
- `adjusters.csv`
- `payments.csv`
- `ai_triage_labels.csv`
- `documents.jsonl`
- `generation_summary.json`
