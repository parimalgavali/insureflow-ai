# Testing, Quality, And Observability

Phase 13 adds repeatable quality gates, coverage reporting, local observability, and smoke-load validation for InsureFlow AI.

## Test Everything

```bash
./scripts/run-tests.sh
```

This runs backend Maven tests, Python package tests, AI service tests, ML tests, frontend unit tests, and the frontend production build.

## Coverage

```bash
./scripts/run-coverage.sh
```

Reports are written to:

| Area | Report |
| --- | --- |
| Backend | `backend/api/target/site/jacoco/index.html` |
| Python packages | `coverage/python/*.xml` |
| Frontend | `frontend/coverage/index.html` |

The backend coverage command uses the explicit Maven `coverage` profile:

```bash
cd backend
mvn clean -Pcoverage verify
```

## Quality Gates

```bash
./scripts/run-quality-gates.sh
```

The quality gate runs tests, coverage, Compose profile validation, script syntax checks, `git diff --check`, optional local Trivy scanning, and frontend `npm audit`.

If Trivy is not installed locally, the script prints a skip message. GitHub Actions still runs the Trivy filesystem scan through `.github/workflows/security-scan.yml`.

## Local Observability

Start the full app plus Prometheus and Grafana:

```bash
docker compose --profile app --profile observability up -d --build
```

Open:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Default Grafana credentials:

- user: `admin`
- password: `insureflow`

The provisioned dashboard is named `InsureFlow Overview`.

Prometheus scrapes backend metrics from:

```text
http://api:8080/actuator/prometheus
```

The backend also exposes:

```text
http://localhost:8080/actuator/health
```

## Load Smoke

With app containers running:

```bash
./scripts/load-smoke-test.sh
```

The script verifies:

- backend, triage, and RAG health checks
- dev JWT creation
- customer, policy, coverage, activation, and FNOL workflow
- direct triage scoring
- RAG evidence ingestion and grounded query

Useful environment variables:

```bash
LOAD_SMOKE_ITERATIONS=10
LOAD_SMOKE_ATTEMPTS=60
LOAD_SMOKE_DELAY_SECONDS=2
API_BASE_URL=http://localhost:8080/api/v1
TRIAGE_BASE_URL=http://localhost:8001
RAG_BASE_URL=http://localhost:8003
```

## CI

`.github/workflows/ci.yml` runs backend, Python, AI, ML, frontend, coverage, and Compose/script validation on pull requests.

`.github/workflows/security-scan.yml` runs Trivy filesystem scanning and frontend `npm audit` on pull requests and manual dispatch.
