# Phase 13 Testing, Quality, And Observability Design

## Goal

Phase 13 adds repeatable quality gates and local observability to InsureFlow AI so the portfolio demo can show not only working insurance workflows, but also disciplined engineering practices around coverage, dependency risk, metrics, and smoke-load validation.

## Scope

This phase focuses on local and CI validation assets. It does not add a production monitoring platform, hosted dashboards, alert routing, synthetic browser testing, or full benchmark suites. Those would be useful later, but the immediate goal is a reliable quality layer that can run on a laptop and in GitHub Actions.

## Recommended Approach

Use a lightweight, local-first implementation:

- Backend coverage through JaCoCo during Maven `verify`.
- Python coverage through `pytest-cov` for the generator, AI services, and ML package.
- Frontend coverage through Vitest coverage.
- Backend runtime metrics through Spring Boot Actuator and Micrometer Prometheus.
- Local observability through a Docker Compose `observability` profile with Prometheus and Grafana.
- Dependency and image risk checks through GitHub Actions security scanning plus local command wrappers where tools are available.
- A shell-based load smoke script that exercises the API, triage service, and RAG service with configurable low iteration counts.

This keeps Phase 13 useful without turning the project into a platform operations project.

## Architecture

The backend exposes `/actuator/prometheus` and `/actuator/health` in addition to the existing `/api/v1/health` endpoint. Security permits those actuator endpoints because Prometheus must scrape them without a JWT in the local Compose network. Core business APIs remain protected by the Phase 11 JWT rules.

Prometheus runs as an optional Compose service and scrapes the backend API container. Grafana runs in the same profile with a provisioned Prometheus data source and a small dashboard for request counts, latency, JVM memory, and process CPU. The existing app profile remains the way to start the product; the observability profile layers on top of it.

Coverage and quality gates live in scripts rather than scattered README commands:

- `scripts/run-tests.sh` remains the main regression command.
- `scripts/run-coverage.sh` creates backend, Python, and frontend coverage reports.
- `scripts/run-quality-gates.sh` runs the full local gate set.
- `scripts/load-smoke-test.sh` sends small, repeatable traffic to core endpoints.

## Load Smoke Behavior

The load smoke script is intentionally small. It validates that:

- the backend health endpoint is reachable,
- a local dev JWT can be minted,
- customer, policy, coverage, activation, and FNOL requests succeed,
- the triage service can score deterministic requests,
- the RAG service can ingest evidence and answer a grounded query.

The script defaults to a low iteration count so it can run during demos. Environment variables allow higher counts without changing the file.

## CI And Security

The main CI workflow should cover backend, Python, ML, and frontend tests instead of only the backend. A separate security workflow should run dependency and filesystem scanning on pull requests and manual dispatch. Local scripts should stay useful even if optional tools such as Trivy are not installed locally.

## Error Handling

Quality scripts should fail fast when required project commands fail. Optional local scanners should print an explicit skip message when the tool is missing. Load smoke checks should include retries for app startup and produce clear endpoint-specific failure messages.

## Documentation

Add a quality and observability runbook under `docs/quality/testing-quality-observability.md`. It should explain how to run coverage, quality gates, observability, and load smoke checks, and where generated reports are written.

## Verification

Phase 13 is complete when these pass locally:

```bash
./scripts/run-tests.sh
./scripts/run-coverage.sh
./scripts/run-quality-gates.sh
docker compose --profile app --profile observability config
bash -n scripts/load-smoke-test.sh
git diff --check
```

If Docker app containers are running, `./scripts/load-smoke-test.sh` should also pass against localhost.
