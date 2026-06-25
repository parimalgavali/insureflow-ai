# InsureFlow AI Triage Service

FastAPI foundation for the Phase 5 rule-based AI triage service. This service is intended to provide decision support for claim triage workflows; outputs should assist human reviewers and should not be treated as fully automated claim decisions.

## Local Setup

Install runtime and test dependencies in a Python 3.12+ environment:

```bash
python3 -m pip install -e ".[test]"
```

Run the service tests:

```bash
python3 -m pytest
```

Run the development server:

```bash
python3 -m uvicorn triage_service.app:app --reload
```

The service exposes:

- `GET /health` for a lightweight readiness check.
- `POST /ai/v1/triage/score` for rule-based severity, fraud, and litigation triage scoring.

The backend workflow contract is documented in `../../docs/api/ai-triage.md`.
