# InsureFlow AI Five-Minute Demo Script

This script is the default portfolio walkthrough. It is designed for a recruiter screen, a hiring-manager review, or the first five minutes of a technical interview.

## Setup

Primary container demo:

```bash
docker compose --profile app up --build
./scripts/smoke-test-containers.sh
```

Quality and observability proof:

```bash
./scripts/run-tests.sh
./scripts/run-quality-gates.sh
docker compose --profile app --profile observability up -d --build
```

Open these during the demo when available:

- Frontend workbench: `http://localhost:5173`
- Backend Swagger UI: `http://localhost:8080/swagger-ui.html`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

## Talk Track

### 0:00-0:45 - Project Framing

"InsureFlow AI is a Guidewire-inspired insurance technology portfolio project. It is not an official Guidewire product or connector. It uses synthetic data to show how policy, coverage, claim, AI triage, document intelligence, RAG assistance, human review, audit, integration, deployment, and observability can fit together in a modern P&C claims workflow."

Point to the README architecture diagram.

### 0:45-1:30 - Claim Operations Story

"The core workflow starts with a policyholder reporting a loss. The Spring Boot backend models customers, policies, coverages, claims, claim events, notes, documents, reserves, and audit records. FNOL intake validates policy and coverage context before the claim moves into the adjuster workflow."

Show:

- claim queue in the Vue workbench;
- claim detail view;
- timeline, notes, document metadata, and status.

### 1:30-2:15 - AI Triage

"AI triage starts with deterministic rules so the decision support is explainable. Phase 6 adds local ML model training for severity and fraud-risk labels, with model metadata and model cards. The triage service falls back to rules when ML artifacts are missing, so the workflow stays resilient."

Show:

- severity, fraud, and litigation signals;
- reason codes;
- human review requirement;
- model version and explanation.

### 2:15-3:00 - Document Intelligence And RAG

"Claims are document-heavy, so the project includes a document intelligence service for extraction, summaries, and missing-document checks. The RAG assistant ingests synthetic claim documents, chunks them, retrieves relevant evidence, and answers with source references instead of pretending it knows everything."

Show:

- document intelligence output;
- RAG answer with source references;
- missing-evidence behavior.

### 3:00-3:45 - Governance And Integration

"The project treats AI as decision support, not automation authority. It includes JWT roles, correlation IDs, audit logging, model and prompt registry views, AI input/output snapshots, human review, and override enforcement. It also exposes Guidewire-inspired integration APIs for policy sync, claim creation, status updates, reserve updates, claim lookup, and webhook simulation."

Show:

- audit/governance docs;
- integration API docs;
- Swagger endpoint groups if running.

### 3:45-4:30 - Deployment, Quality, Observability

"The system is packaged for local containers and cloud-readiness. It has Dockerfiles, a Compose app profile, Azure Container Apps Bicep templates, smoke tests, GitHub Actions, coverage reports, Trivy scans, Prometheus metrics, Grafana dashboard provisioning, and a load-smoke script."

Show:

- CI checks in GitHub;
- Grafana or Prometheus if running;
- `docs/quality/testing-quality-observability.md`.

### 4:30-5:00 - Close

"The project demonstrates insurance domain modeling, Java/Spring Boot backend engineering, Python AI service boundaries, local ML training, LLM/RAG-style decision support, responsible AI controls, frontend workflow design, integration thinking, and cloud/platform readiness. It is built to be discussed deeply, not just clicked through."

Close with:

- [responsible AI statement](../ai/responsible-ai-statement.md);
- [project narrative](../portfolio/project-narrative.md);
- [resume bullets](../portfolio/resume-bullets.md).

## Backup Demo If Containers Are Not Running

If the runtime is unavailable, use the docs-only path:

1. README architecture diagram.
2. `docs/frontend/adjuster-workbench.md`
3. `docs/api/policy-claims-workflow.md`
4. `docs/api/ai-triage.md`
5. `docs/api/document-intelligence.md`
6. `docs/api/rag-assistant.md`
7. `docs/api/security-audit-governance.md`
8. `docs/quality/testing-quality-observability.md`

This still demonstrates the system design and implementation depth.
