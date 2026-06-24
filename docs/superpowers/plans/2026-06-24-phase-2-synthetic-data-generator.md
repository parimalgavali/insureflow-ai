# Phase 2 Synthetic Data Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python synthetic data generator that creates realistic, relational P&C insurance data and synthetic document text for InsureFlow AI.

**Architecture:** Implement a self-contained Python package under `synthetic-data-generator/` that generates deterministic CSV and JSONL outputs from typed dataclasses and configurable counts. Keep the generator independent of the backend runtime, but align output names and relationships with the Phase 0/1 database schema and the full project blueprint.

**Tech Stack:** Python 3.11+, standard library, pytest, ruff optional later. Use deterministic pseudo-random generation with a seed. Do not add pandas or faker in Phase 2; keep the first generator lightweight and dependency-minimal.

---

## Working Branch

Use branch:

```bash
codex/phase-2-synthetic-data-generator
```

This branch is stacked on:

```bash
codex/project-memory-and-phase-plans
```

until the Phase 0/1 PR merges into `main`.

Before implementing, verify:

```bash
git status -sb
git branch --show-current
```

Expected branch:

```text
codex/phase-2-synthetic-data-generator
```

## Phase Boundaries

Build only Phase 2.

Do not build:

- Backend policy CRUD endpoints.
- FNOL workflow.
- AI triage service.
- ML training pipeline.
- LLM/RAG services.
- Frontend app.
- Cloud deployment.

## File Structure To Create Or Modify

```text
synthetic-data-generator/
├── README.md
├── pyproject.toml
├── generator/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── reference_data.py
│   ├── rules.py
│   ├── documents.py
│   ├── writer.py
│   └── generate.py
└── tests/
    ├── test_cli.py
    ├── test_generation_integrity.py
    ├── test_label_rules.py
    └── test_writer.py

data/
├── synthetic/
│   └── .gitkeep
└── sample/
    └── .gitkeep

scripts/
└── generate-demo-data.sh
```

Modify:

```text
PROJECT_MEMORY.md
README.md
docs/data/synthetic-data-generation.md
docs/data/data-dictionary.md
```

## Output Files

The generator must create these files in the selected output directory:

```text
customers.csv
policies.csv
coverages.csv
claims.csv
claim_documents.csv
claim_notes.csv
claim_events.csv
adjusters.csv
payments.csv
ai_triage_labels.csv
documents.jsonl
generation_summary.json
```

## Data Volume Defaults

Default CLI counts:

```text
customers: 500
policies: 650
claims: 200
adjusters: 25
seed: 42
```

The generator must support smaller counts for tests.

## Task 1: Python Package Skeleton

**Files:**
- Create: `synthetic-data-generator/pyproject.toml`
- Create: `synthetic-data-generator/generator/__init__.py`
- Create: `synthetic-data-generator/generator/__main__.py`
- Create: `synthetic-data-generator/generator/config.py`
- Create: `synthetic-data-generator/tests/test_cli.py`

- [ ] **Step 1: Write failing CLI smoke test**

Create `test_cli.py` that calls:

```bash
python -m generator --customers 5 --policies 6 --claims 4 --adjusters 3 --seed 7 --output-dir <tmpdir>
```

Expected files:

```python
[
    "customers.csv",
    "policies.csv",
    "coverages.csv",
    "claims.csv",
    "claim_documents.csv",
    "claim_notes.csv",
    "claim_events.csv",
    "adjusters.csv",
    "payments.csv",
    "ai_triage_labels.csv",
    "documents.jsonl",
    "generation_summary.json",
]
```

- [ ] **Step 2: Run test and confirm red**

Run:

```bash
cd synthetic-data-generator
python -m pytest tests/test_cli.py -q
```

Expected: fails because package/CLI is not implemented yet.

- [ ] **Step 3: Create `pyproject.toml`**

Use project name:

```text
insureflow-synthetic-data-generator
```

Dependencies:

```toml
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

- [ ] **Step 4: Create config dataclass**

`config.py` must define:

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class GeneratorConfig:
    customers: int = 500
    policies: int = 650
    claims: int = 200
    adjusters: int = 25
    seed: int = 42
    output_dir: Path = Path("data/synthetic")
```

- [ ] **Step 5: Create CLI entrypoint**

`__main__.py` must call `generator.cli.main`.

`cli.py` must parse:

```text
--customers
--policies
--claims
--adjusters
--seed
--output-dir
```

and call `generate_dataset(config)`.

- [ ] **Step 6: Verify CLI test reaches generation function**

Run:

```bash
cd synthetic-data-generator
python -m pytest tests/test_cli.py -q
```

Expected: still fails until generation and writing are implemented.

## Task 2: Domain Models And Reference Data

**Files:**
- Create: `synthetic-data-generator/generator/models.py`
- Create: `synthetic-data-generator/generator/reference_data.py`
- Create: `synthetic-data-generator/tests/test_generation_integrity.py`

- [ ] **Step 1: Write failing relationship test**

Test `generate_dataset` with:

```text
customers=10
policies=14
claims=8
adjusters=4
seed=11
```

Assert:

- Every policy has a valid customer id.
- Every coverage has a valid policy id.
- Every claim has a valid policy id and customer id.
- Every claim document has a valid claim id.
- Every claim event has a valid claim id.
- Every AI triage label has a valid claim id.
- Every payment has a valid claim id.

- [ ] **Step 2: Define dataclasses**

`models.py` must define dataclasses for:

- `Customer`
- `Policy`
- `Coverage`
- `Claim`
- `ClaimDocument`
- `ClaimNote`
- `ClaimEvent`
- `Adjuster`
- `Payment`
- `AITriageLabel`
- `SyntheticDocument`
- `GeneratedDataset`

Use string UUIDs generated with `uuid.uuid4()`.

- [ ] **Step 3: Define reference data**

`reference_data.py` must include:

- German and nearby European cities:
  - `Bielefeld`
  - `Berlin`
  - `Munich`
  - `Hamburg`
  - `Cologne`
  - `Frankfurt`
  - `Dusseldorf`
  - `Stuttgart`
  - `Dortmund`
  - `Leipzig`
- Product type: `MOTOR`
- Claim types:
  - `MOTOR_COLLISION`
  - `THEFT`
  - `FIRE`
  - `GLASS_DAMAGE`
  - `BODILY_INJURY`
- Coverage types:
  - `COLLISION`
  - `COMPREHENSIVE`
  - `THIRD_PARTY_LIABILITY`
  - `PERSONAL_INJURY`
  - `THEFT`

## Task 3: Generation Rules

**Files:**
- Create: `synthetic-data-generator/generator/generate.py`
- Create: `synthetic-data-generator/generator/rules.py`
- Create: `synthetic-data-generator/tests/test_label_rules.py`

- [ ] **Step 1: Write failing label rule tests**

Create tests for:

- High severity when estimated damage is above 25,000 EUR and injury is reported.
- Medium or high fraud risk when policy age is under 30 days and FNOL delay is above 21 days.
- Medium or high litigation risk when injury is reported and legal keywords appear in description.

- [ ] **Step 2: Implement label rules**

`rules.py` must expose:

```python
score_severity(...)
score_fraud(...)
score_litigation(...)
```

Each function returns:

```python
{
    "score": int,
    "label": "LOW" | "MEDIUM" | "HIGH",
    "reason_codes": list[str],
}
```

Reason codes must include values from:

```text
HIGH_ESTIMATED_DAMAGE
INJURY_REPORTED
THIRD_PARTY_INVOLVED
LATE_FNOL
MISSING_POLICE_REPORT
POLICY_RECENTLY_STARTED
PRIOR_CLAIMS_HIGH
LEGAL_KEYWORDS_DETECTED
```

- [ ] **Step 3: Implement deterministic generator**

`generate_dataset(config)` must:

- Use `random.Random(config.seed)`.
- Generate requested number of customers.
- Generate requested number of policies.
- Generate 2 to 4 coverages per policy.
- Generate requested number of claims.
- Generate 1 to 3 claim documents per claim.
- Generate 1 to 4 claim events per claim.
- Generate 0 to 2 payments for approved or paid claims.
- Generate one AI triage label per claim.
- Generate synthetic document text for each claim document.

## Task 4: Synthetic Documents

**Files:**
- Create: `synthetic-data-generator/generator/documents.py`
- Modify: `synthetic-data-generator/tests/test_generation_integrity.py`

- [ ] **Step 1: Write failing document test**

Assert `documents.jsonl` contains one JSON object per synthetic document with:

```text
document_id
claim_id
document_type
text
```

Assert text is non-empty.

- [ ] **Step 2: Implement document templates**

Support document types:

- `FNOL_STATEMENT`
- `REPAIR_INVOICE`
- `POLICE_REPORT`
- `MEDICAL_REPORT`
- `CUSTOMER_EMAIL`
- `ADJUSTER_NOTE`

Generated text must include claim-specific values such as city, loss date, estimated damage, injury flag, third party flag, and police report availability when relevant.

## Task 5: Writers And Summary

**Files:**
- Create: `synthetic-data-generator/generator/writer.py`
- Create: `synthetic-data-generator/tests/test_writer.py`

- [ ] **Step 1: Write failing writer tests**

Assert:

- CSV headers are stable.
- `documents.jsonl` has valid JSON on every line.
- `generation_summary.json` contains counts for every output file.

- [ ] **Step 2: Implement CSV writer**

Use Python standard library `csv.DictWriter`.

Do not write Python object reprs. Convert dataclasses with `dataclasses.asdict`.

- [ ] **Step 3: Implement JSONL writer**

Use one JSON object per line with `json.dumps(..., sort_keys=True)`.

- [ ] **Step 4: Implement summary writer**

`generation_summary.json` must include:

```json
{
  "customers": 0,
  "policies": 0,
  "coverages": 0,
  "claims": 0,
  "claim_documents": 0,
  "claim_notes": 0,
  "claim_events": 0,
  "adjusters": 0,
  "payments": 0,
  "ai_triage_labels": 0,
  "documents": 0,
  "seed": 42
}
```

with actual counts.

## Task 6: Scripts And Documentation

**Files:**
- Modify: `synthetic-data-generator/README.md`
- Create: `scripts/generate-demo-data.sh`
- Create: `docs/data/synthetic-data-generation.md`
- Create: `docs/data/data-dictionary.md`
- Modify: `README.md`

- [ ] **Step 1: Create script**

`scripts/generate-demo-data.sh` must run:

```bash
python -m generator --customers 500 --policies 650 --claims 200 --adjusters 25 --seed 42 --output-dir ../data/synthetic
```

from inside `synthetic-data-generator`.

- [ ] **Step 2: Update generator README**

Include:

- Purpose.
- Synthetic-only privacy statement.
- Setup command.
- Test command.
- Generation command.
- Output file list.

- [ ] **Step 3: Add docs**

`docs/data/synthetic-data-generation.md` must describe:

- Why synthetic data is used.
- Relationship graph.
- Label rule approach.
- Document template approach.
- Current default volumes.

`docs/data/data-dictionary.md` must describe each output file and key columns.

- [ ] **Step 4: Update root README**

Add a short section:

```markdown
## Synthetic Data

```bash
cd synthetic-data-generator
python -m pytest
python -m generator --customers 500 --policies 650 --claims 200 --adjusters 25 --seed 42 --output-dir ../data/synthetic
```
```

## Task 7: Verification And Memory Update

**Files:**
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Run tests**

Run:

```bash
cd synthetic-data-generator
python -m pytest
```

Expected: all generator tests pass.

- [ ] **Step 2: Generate small sample**

Run:

```bash
cd synthetic-data-generator
python -m generator --customers 10 --policies 14 --claims 8 --adjusters 4 --seed 11 --output-dir ../data/sample
```

Expected: all output files are created under `data/sample`.

- [ ] **Step 3: Generate default synthetic dataset**

Run:

```bash
cd synthetic-data-generator
python -m generator --customers 500 --policies 650 --claims 200 --adjusters 25 --seed 42 --output-dir ../data/synthetic
```

Expected: all output files are created under `data/synthetic`.

Do not commit generated CSV/JSONL files. They are ignored except `.gitkeep`.

- [ ] **Step 4: Run repository test script**

Run:

```bash
./scripts/run-tests.sh
```

Expected: backend tests still pass. If the script does not yet include Python tests, update it to run them.

- [ ] **Step 5: Update memory**

Add completed work:

```markdown
| 2026-06-24 | Completed Phase 2 synthetic data generator. | Generator creates relational CSVs, synthetic documents, labels, tests, and documentation. |
```

Add verification:

```markdown
| 2026-06-24 | Verified Phase 2 locally. | Python generator tests passed; sample and default datasets generated successfully; backend tests still passed. |
```

- [ ] **Step 6: Commit**

Run:

```bash
git add synthetic-data-generator scripts README.md docs/data data PROJECT_MEMORY.md
git commit -m "feat: add synthetic insurance data generator"
```

## Final Output From Implementer

Return:

- Branch name.
- Commit SHAs created.
- Files changed.
- Verification commands and results.
- Generated output counts from `generation_summary.json`.
- Any blockers or concerns.

