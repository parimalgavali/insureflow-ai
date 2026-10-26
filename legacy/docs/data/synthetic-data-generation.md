# Synthetic Data Generation

InsureFlow AI uses synthetic data so the portfolio can demonstrate realistic insurance workflows without storing real customer PII, real claims, or insurer-confidential records.

## Relationship Graph

The generator creates a small relational insurance universe:

```text
customers -> policies -> coverages
customers -> claims
policies  -> claims
claims    -> claim_documents -> documents.jsonl
claims    -> claim_notes
claims    -> claim_events
claims    -> payments
claims    -> ai_triage_labels
adjusters -> claims
adjusters -> claim_notes
```

Every generated child row references an existing parent id. IDs are deterministic UUID-form strings derived from the configured seed.

## Label Rules

AI triage labels are rule-based placeholders for later ML work. They produce severity, fraud, and litigation scores with `LOW`, `MEDIUM`, or `HIGH` labels.

Current reason codes include:

- `HIGH_ESTIMATED_DAMAGE`
- `INJURY_REPORTED`
- `THIRD_PARTY_INVOLVED`
- `LATE_FNOL`
- `MISSING_POLICE_REPORT`
- `POLICY_RECENTLY_STARTED`
- `PRIOR_CLAIMS_HIGH`
- `LEGAL_KEYWORDS_DETECTED`

These labels are decision-support signals only and are not real insurance, legal, medical, or fraud determinations.

## Document Templates

`documents.jsonl` contains one JSON object per synthetic claim document. Template types are:

- `FNOL_STATEMENT`
- `REPAIR_INVOICE`
- `POLICE_REPORT`
- `MEDICAL_REPORT`
- `CUSTOMER_EMAIL`
- `ADJUSTER_NOTE`

Generated text includes claim-specific values such as loss city, loss date, estimated damage, injury flag, third-party flag, and police report availability.

## Default Volumes

The demo generation command uses:

```text
customers: 500
policies: 650
claims: 200
adjusters: 25
seed: 42
```

Run:

```bash
./scripts/generate-demo-data.sh
```
