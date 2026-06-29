# Phase 13 Testing, Quality, And Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add coverage reporting, quality gates, local observability, security scanning, and load-smoke validation for InsureFlow AI.

**Architecture:** Keep quality automation script-driven so it works locally and in CI. Expose backend Prometheus metrics through Spring Actuator, run Prometheus/Grafana through an optional Compose profile, and use small shell smoke-load checks for core workflows.

**Tech Stack:** Maven, JaCoCo, pytest-cov, Vitest coverage, Spring Boot Actuator, Micrometer Prometheus, Docker Compose, Prometheus, Grafana, GitHub Actions, Trivy.

---

## File Map

- Modify `backend/api/pom.xml`: add Actuator, Micrometer Prometheus, and JaCoCo.
- Modify `backend/api/src/main/resources/application.yml`: expose management health and Prometheus endpoints.
- Modify `backend/api/src/main/java/com/insureflow/api/security/SecurityConfig.java`: permit local metrics endpoints.
- Modify `backend/api/src/test/java/com/insureflow/api/security/SecurityAccessIntegrationTest.java`: cover public actuator access.
- Modify Python `pyproject.toml` files: add `pytest-cov` to test extras.
- Modify `frontend/package.json` and `frontend/package-lock.json`: add Vitest coverage provider and coverage script.
- Add `scripts/run-coverage.sh`: generate backend, Python, ML, and frontend coverage reports.
- Add `scripts/run-quality-gates.sh`: run tests, coverage, Compose validation, and optional local scanners.
- Add `scripts/load-smoke-test.sh`: exercise backend FNOL, triage, and RAG endpoints with configurable iterations.
- Modify `.github/workflows/ci.yml`: expand CI beyond backend-only tests.
- Add `.github/workflows/security-scan.yml`: run dependency/filesystem scanning on PRs and manual dispatch.
- Modify `docker-compose.yml`: add `observability` profile services for Prometheus and Grafana.
- Add `monitoring/prometheus/prometheus.yml`: scrape local backend metrics.
- Add `monitoring/grafana/provisioning/datasources/prometheus.yml`: provision Prometheus data source.
- Add `monitoring/grafana/provisioning/dashboards/dashboards.yml`: load local dashboards.
- Add `monitoring/grafana/dashboards/insureflow-overview.json`: overview dashboard.
- Add `docs/quality/testing-quality-observability.md`: runbook.
- Modify `README.md`, `docs/README.md`, and `PROJECT_MEMORY.md`: document Phase 13 status and links.

## Task 1: Backend Metrics And Coverage

- [ ] Write a failing security integration test that expects unauthenticated access to `/actuator/health` and `/actuator/prometheus`.
- [ ] Add Actuator and Micrometer Prometheus dependencies.
- [ ] Expose `health`, `info`, and `prometheus` management endpoints in `application.yml`.
- [ ] Permit `/actuator/health` and `/actuator/prometheus` in `SecurityConfig`.
- [x] Add JaCoCo to Maven `verify`.
- [x] Run `cd backend && mvn -pl api test` and confirm the new test passes.
- [x] Run `cd backend && mvn clean -Pcoverage verify` and confirm `backend/api/target/site/jacoco/index.html` is generated.

## Task 2: Coverage Scripts

- [x] Add `pytest-cov` to Python test extras.
- [x] Add frontend coverage support through Vitest.
- [x] Create `scripts/run-coverage.sh` to run backend JaCoCo, Python coverage, ML coverage, and frontend coverage.
- [x] Verify `bash -n scripts/run-coverage.sh`.
- [x] Run `./scripts/run-coverage.sh` and fix failures.

## Task 3: Quality Gates And CI

- [x] Create `scripts/run-quality-gates.sh` to run tests, coverage, Compose validation, script syntax checks, and optional local scanner checks.
- [x] Expand `.github/workflows/ci.yml` to run backend, Python, ML, frontend, and quality validation jobs on pull requests.
- [x] Add `.github/workflows/security-scan.yml` with Trivy filesystem scanning and npm audit.
- [x] Verify workflow YAML and script syntax locally.

## Task 4: Observability Stack

- [x] Add Prometheus and Grafana services under a Compose `observability` profile.
- [x] Add Prometheus scrape config for `api:8080/actuator/prometheus`.
- [x] Add Grafana provisioning for the Prometheus data source and dashboard folder.
- [x] Add an InsureFlow overview dashboard for request volume, latency, JVM memory, and CPU.
- [x] Run `docker compose --profile app --profile observability config`.

## Task 5: Load Smoke Script

- [x] Create `scripts/load-smoke-test.sh`.
- [x] Include startup retries for backend, triage, and RAG health checks.
- [x] Mint an adjuster token through `/api/v1/auth/dev-token`.
- [x] Create customer, policy, coverage, activate policy, and submit FNOL with unique IDs.
- [x] Score the triage service directly.
- [x] Ingest RAG evidence and query it.
- [x] Run `bash -n scripts/load-smoke-test.sh`.
- [x] If app containers are running, run `./scripts/load-smoke-test.sh`.

## Task 6: Documentation And Memory

- [x] Add `docs/quality/testing-quality-observability.md`.
- [x] Update README and docs index links.
- [x] Update `PROJECT_MEMORY.md` with Phase 13 start and implementation details.
- [x] Run full verification:

```bash
./scripts/run-tests.sh
./scripts/run-coverage.sh
./scripts/run-quality-gates.sh
docker compose --profile app --profile observability config
bash -n scripts/load-smoke-test.sh
git diff --check
```

- [ ] Commit and open a PR:

```bash
git add .
git commit -m "test: add quality gates and observability"
git push -u origin testing-quality-observability
gh pr create --base main --head testing-quality-observability --title "Phase 13: Testing, quality, and observability" --body-file /tmp/phase-13-pr-body.md
```
