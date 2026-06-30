# InsureFlow AI Project Memory

This file is the living memory for the InsureFlow AI project. Update it after important decisions, completed phases, repository changes, architecture choices, blockers, and handoffs.

Future Codex sessions should read this file before planning or implementing work.

## Current Project State

- **Project name:** InsureFlow AI
- **GitHub repository:** https://github.com/parimalgavali/insureflow-ai
- **Visibility:** Public
- **Local workspace:** `/Users/parimal_gavali/Documents/Guidewire`
- **Primary blueprint source:** `/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md`
- **Current branch:** `testing-quality-observability`
- **First committed artifact:** `docs/superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md`

## Project Purpose

InsureFlow AI is a Guidewire-inspired, cloud-native claims and policy intelligence portfolio project. It is designed to demonstrate insurance domain understanding, Java/Spring Boot backend engineering, AI/ML model serving, LLM/RAG document intelligence, auditability, and human-in-the-loop responsible AI.

The career positioning is:

> I may not yet have professional Guidewire implementation experience, but I understand insurance workflows around policy and claims, I can build enterprise-grade Java integrations, and I can responsibly integrate AI/ML/LLM intelligence into insurance operations.

## Execution Strategy

Use a phase-based agent approach first, then evolve into a three-agent split once foundations and contracts exist.

Recommended sequence:

1. Build Phase 0 and Phase 1 with a foundation-focused worker.
2. After backend/domain/API contracts exist, parallelize:
   - Backend agent for policy, claims, audit, security, integration APIs.
   - AI/middleware agent for synthetic data, triage, ML, LLM, RAG.
   - Frontend agent for Vue adjuster workbench.
3. The main Codex session acts as orchestrator: contracts, review, integration, tests, and GitHub coordination.

## Key Decisions

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-06-24 | Use `InsureFlow AI` as the project name. | Matches the blueprint and clearly communicates insurance workflow intelligence. |
| 2026-06-24 | Start with phase-based agents before splitting into permanent frontend/backend/AI agents. | The repo starts empty, so foundation and contracts must come before parallel feature work. |
| 2026-06-24 | Keep the GitHub repository public. | This is a professional portfolio project intended for recruiters and hiring managers. |
| 2026-06-24 | Use the master build plan as the roadmap and create detailed phase plans as work begins. | Prevents the large blueprint from becoming an unmanageable single implementation pass. |
| 2026-06-24 | Keep feature work off `main`; use feature branches. | Keeps the public portfolio branch stable while implementation work is reviewed. |
| 2026-06-25 | Use readable feature branch names without the `codex/` prefix. | The user prefers names such as `policy-claims-workflow-implementation`. |
| 2026-06-25 | Keep AI triage as a rule-based decision-support service before introducing ML models. | Phase 5 needs explainable, deterministic behavior and stable backend contracts before Phase 6 model training. |

## Completed Work

| Date | Work | Evidence |
| --- | --- | --- |
| 2026-06-24 | Read and summarized the full project blueprint. | Blueprint reviewed from `/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md`. |
| 2026-06-24 | Created the master build plan. | `docs/superpowers/plans/2026-06-24-insureflow-ai-master-build-plan.md` |
| 2026-06-24 | Connected the project to GitHub. | `https://github.com/parimalgavali/insureflow-ai` |
| 2026-06-24 | Confirmed master build plan exists on GitHub. | `main` contains commit `f68ed27`. |
| 2026-06-24 | Created feature branch for memory and Phase 0/1 planning. | Branch `codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Created detailed Phase 0/1 implementation plan. | `docs/superpowers/plans/2026-06-24-phase-0-1-repository-and-domain-foundation.md` |
| 2026-06-24 | Pushed memory and Phase 0/1 planning branch to GitHub. | Remote branch `origin/codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Started Phase 0/1 foundation branch. | Branch `codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Completed Phase 0/1 repository and backend foundation. | Local infra, backend skeleton, Flyway schema, CI, and tests added on `codex/project-memory-and-phase-plans`. |
| 2026-06-24 | Verified Phase 0/1 foundation locally. | Docker Compose PostgreSQL/RabbitMQ healthy; `mvn test` and `./scripts/run-tests.sh` passed with 2 backend tests. |
| 2026-06-24 | Completed spec and quality review for Phase 0/1. | Spec compliant after push; quality review passed with no blocking issues. |
| 2026-06-24 | Started Phase 2 synthetic data generator branch. | Branch `codex/phase-2-synthetic-data-generator`, stacked on Phase 0/1 foundation until that PR merges. |
| 2026-06-24 | Completed Phase 2 synthetic data generator. | Generator creates relational CSVs, synthetic documents, labels, tests, and documentation. |
| 2026-06-24 | Verified Phase 2 locally. | Python generator tests passed; sample and default datasets generated successfully; backend tests still passed. |
| 2026-06-25 | Fixed Phase 2 review findings. | Added regression coverage so generated police/medical documents cannot contradict claim facts; updated root README Python commands. |
| 2026-06-25 | Re-verified Phase 2 after fixes. | `./scripts/run-tests.sh` passed: backend 2 tests and generator 10 tests. |
| 2026-06-25 | Pushed Phase 2 synthetic data generator branch to GitHub. | Remote branch `origin/codex/phase-2-synthetic-data-generator`. |
| 2026-06-25 | Created Phase 3/4 planning branch. | Branch `policy-claims-workflow`, stacked on Phase 2 until earlier PRs merge. |
| 2026-06-25 | Created detailed Phase 3/4 implementation plan. | `docs/superpowers/plans/2026-06-25-phase-3-4-policy-and-claims-workflow.md` |
| 2026-06-25 | Started Phase 3/4 implementation branch. | Branch `policy-claims-workflow-implementation`, created from updated `main` after Phase 0/1, Phase 2, and planning PRs merged. |
| 2026-06-25 | Implemented Phase 3/4 policy and claims workflow. | Customer/policy/coverage APIs, lifecycle transitions, coverage validation, FNOL, claim timeline, status transitions, notes, document metadata, and integration tests. |
| 2026-06-25 | Addressed Phase 3/4 review findings. | Added claim-number collision retry through a fresh transaction attempt service, persisted FNOL coverage snapshots on claim reads, coverage effective-date validation, and 422 handling for database constraint violations. |
| 2026-06-25 | Verified Phase 3/4 review fixes locally. | `./scripts/run-tests.sh` passed with 24 backend tests and 10 synthetic generator tests; `git diff --check` passed. |
| 2026-06-25 | Started Phase 5 rule-based triage planning. | Branch `rule-based-triage-service`; detailed implementation plan created at `docs/superpowers/plans/2026-06-25-phase-5-rule-based-ai-triage-service.md`. |
| 2026-06-25 | Implemented Phase 5 rule-based AI triage service foundation. | FastAPI service under `ai-services/triage-service` with health and `POST /ai/v1/triage/score` endpoints, deterministic scoring rules, reason codes, and tests. |
| 2026-06-25 | Persisted AI triage results in the backend. | Added `ai_triage_results`, Flyway V3, JPA entity/repository, label backfill behavior, and deterministic latest-result ordering. |
| 2026-06-25 | Integrated backend claim triage workflow. | Added `POST /api/v1/claims/{claimNumber}/triage`, `GET /api/v1/claims/{claimNumber}/triage`, feature assembly, timeline event `TRIAGE_COMPLETED`, and outage handling with HTTP 503. |
| 2026-06-25 | Documented Phase 5 AI triage contracts. | `docs/api/ai-triage.md`, README links, docs index updates, triage service README updates, and `scripts/run-tests.sh` now includes triage service tests. |
| 2026-06-25 | Verified Phase 5 locally. | `./scripts/run-tests.sh` passed: backend 31 tests, synthetic generator 10 tests, triage service 8 tests. |
| 2026-06-25 | Started Phase 6 ML triage model training. | Branch `ml-triage-model-training`; synthetic-data-first design spec created at `docs/superpowers/specs/2026-06-25-phase-6-ml-triage-model-training-design.md` and implementation plan created at `docs/superpowers/plans/2026-06-25-phase-6-ml-triage-model-training.md`. |
| 2026-06-25 | Implemented Phase 6 ML training and triage serving. | Added `ml/` package, severity/fraud-risk training workflow, model artifact loader, ML model cards, and triage service ML fallback behavior. |
| 2026-06-25 | Verified Phase 6 locally. | `./scripts/run-tests.sh` passed: backend 31 tests, synthetic generator 10 tests, triage service 10 tests, and ML package 3 tests. Local `ml/artifacts/` output is ignored by Git and can be regenerated. |
| 2026-06-25 | Opened Phase 6 pull request. | PR #6: `https://github.com/parimalgavali/insureflow-ai/pull/6` from `ml-triage-model-training` into `main`. |
| 2026-06-26 | Started Phase 7 LLM document intelligence. | Branch `llm-document-intelligence`; design and implementation plan created for the document intelligence FastAPI service. |
| 2026-06-26 | Implemented Phase 7 document intelligence service. | Added `ai-services/document-intelligence-service` with extraction, missing-document checks, summaries, prompt registry, retry-on-invalid-JSON, in-memory audit, tests, and API docs. |
| 2026-06-26 | Verified Phase 7 locally. | `./scripts/run-tests.sh` passed: backend 31 tests, synthetic generator 10 tests, triage service 10 tests, document intelligence service 7 tests, and ML package 3 tests. |
| 2026-06-26 | Opened Phase 7 pull request. | PR #7: `https://github.com/parimalgavali/insureflow-ai/pull/7` from `llm-document-intelligence` into `main`. |
| 2026-06-26 | Started Phase 8 RAG adjuster assistant. | Branch `rag-adjuster-assistant`; design and implementation plan created for the offline RAG service. |
| 2026-06-26 | Implemented Phase 8 RAG adjuster assistant service. | Added `ai-services/rag-service` with ingestion, chunking, in-memory retrieval, grounded answers, source references, missing-evidence behavior, audit, tests, and API docs. |
| 2026-06-26 | Verified Phase 8 locally. | `./scripts/run-tests.sh` passed: backend 31 tests, synthetic generator 10 tests, triage service 10 tests, document intelligence service 7 tests, RAG service 5 tests, and ML package 3 tests. |
| 2026-06-26 | Opened Phase 8 pull request. | PR #8: `https://github.com/parimalgavali/insureflow-ai/pull/8` from `rag-adjuster-assistant` into `main`. |
| 2026-06-26 | Started Phase 9 adjuster workbench frontend. | Branch `adjuster-workbench-frontend`; design and implementation plan created for the Vue workbench. |
| 2026-06-26 | Implemented Phase 9 adjuster workbench frontend. | Added Vue 3/Vite/TypeScript frontend with claim queue, claim detail workspace, AI triage, document intelligence, RAG assistant, timeline, audit, human review modal, component tests, and frontend docs. |
| 2026-06-26 | Verified Phase 9 locally. | `./scripts/run-tests.sh` passed: backend 31 tests, synthetic generator 10 tests, triage service 10 tests, document intelligence service 7 tests, RAG service 5 tests, ML package 3 tests, frontend 6 tests, and frontend production build. |
| 2026-06-26 | Opened Phase 9 pull request. | PR #9: `https://github.com/parimalgavali/insureflow-ai/pull/9` from `adjuster-workbench-frontend` into `main`. |
| 2026-06-26 | Started Phase 10 Guidewire-inspired integration APIs. | Branch `integration-apis`; design and implementation plan created for `/integration/v1` policy sync, claim create, status update, reserve update, claim lookup, and webhook simulation. |
| 2026-06-26 | Implemented Phase 10 Guidewire-inspired integration APIs. | Added `/integration/v1` Spring Boot facade, `integration_events`, `claim_reserves`, policy sync, claim create, claim lookup, claim status update, reserve update, claim-triaged webhook simulation, API docs, and HTTP collection. |
| 2026-06-26 | Verified Phase 10 locally. | `./scripts/run-tests.sh` passed: backend 33 tests, synthetic generator 10 tests, triage service 10 tests, document intelligence service 7 tests, RAG service 5 tests, ML package 3 tests, frontend 6 tests, and frontend production build. `git diff --check` passed. |
| 2026-06-26 | Opened Phase 10 pull request. | PR #10: `https://github.com/parimalgavali/insureflow-ai/pull/10` from `integration-apis` into `main`. |
| 2026-06-28 | Started Phase 11 security, audit, and governance. | Branch `security-audit-governance`; design and implementation plan created for JWT roles, audit logging, correlation IDs, AI decision snapshots, human review override enforcement, and governance registry views. |
| 2026-06-28 | Implemented Phase 11 security, audit, and governance controls. | Added JWT auth/RBAC, correlation IDs, audit logs, AI triage input/output snapshots, governance registry endpoints, human review override enforcement, structured logging, tests, and `docs/api/security-audit-governance.md`. |
| 2026-06-28 | Opened Phase 11 pull request. | PR #11: `https://github.com/parimalgavali/insureflow-ai/pull/11` from `security-audit-governance` into `main`. |
| 2026-06-28 | Started Phase 12 cloud deployment readiness. | Branch `cloud-deployment`; design and implementation plan created for Docker packaging, local app Compose, Azure Container Apps templates, deployment validation, and runbook docs. |
| 2026-06-28 | Implemented Phase 12 cloud deployment readiness. | Added Dockerfiles, `.dockerignore` files, app-profile Compose services, smoke tests, Azure Container Apps Bicep templates, GitHub deployment validation workflow, and cloud deployment runbook. |
| 2026-06-28 | Verified Phase 12 locally. | `./scripts/run-tests.sh`, `docker compose --profile app config`, `bash -n scripts/smoke-test-containers.sh`, `docker compose --profile app build`, real app-profile container smoke checks, and `git diff --check` passed. Azure Bicep build was skipped locally because Azure CLI is not installed. |
| 2026-06-28 | Opened Phase 12 pull request. | PR #12: `https://github.com/parimalgavali/insureflow-ai/pull/12` from `cloud-deployment` into `main`. |
| 2026-06-29 | Started Phase 13 testing, quality, and observability. | Branch `testing-quality-observability`; design and implementation plan created for coverage reporting, quality gates, security scanning, local Prometheus/Grafana observability, and load-smoke validation. |
| 2026-06-29 | Implemented Phase 13 testing, quality, and observability. | Added backend/Python/frontend coverage, local quality gates, CI/security workflows, Spring Actuator Prometheus metrics, Prometheus/Grafana Compose profile, load-smoke validation, and quality runbook docs. |
| 2026-06-29 | Verified Phase 13 locally. | `./scripts/run-coverage.sh`, `./scripts/run-quality-gates.sh`, `./scripts/load-smoke-test.sh`, `docker compose --profile app --profile observability ps`, API `/actuator/prometheus`, Prometheus readiness/query, Grafana health, and `git diff --check` passed. Local Trivy scan was skipped because `trivy` is not installed. |
| 2026-06-29 | Opened Phase 13 pull request. | PR #13: `https://github.com/parimalgavali/insureflow-ai/pull/13` from `testing-quality-observability` into `main`. |
| 2026-06-29 | Fixed Phase 13 CI failures. | Updated Trivy action to resolvable `aquasecurity/trivy-action@v0.36.0` and made triage/ML tests resolve sample data by file location so repo-root CI pytest commands pass. |
| 2026-06-29 | Hardened Phase 13 CI fixes. | Removed ML test dependency on untracked local `data/sample/*.csv` files by generating deterministic test fixtures, and upgraded vulnerable backend dependencies reported by Trivy. |
| 2026-06-30 | Started Phase 14 portfolio packaging. | Branch `portfolio-packaging`, created from updated `main` after Phase 13 merged. |
| 2026-06-30 | Designed Phase 14 portfolio package. | Spec created at `docs/superpowers/specs/2026-06-30-phase-14-portfolio-packaging-design.md`; scope is recruiter-ready docs, demo script, portfolio narrative, resume bullets, and responsible AI statement. |
| 2026-06-30 | Implemented Phase 14 portfolio docs. | Added polished README, docs index, `docs/demo/`, `docs/portfolio/`, `docs/ai/responsible-ai-statement.md`, and implementation plan. |
| 2026-06-30 | Verified Phase 14 locally. | `git diff --check`, Phase 14 path sanity checks, and `./scripts/run-quality-gates.sh` passed. First sandboxed quality-gate run failed because Testcontainers could not access Docker; rerun with Docker access passed. |

## Known Issues And Caveats

- `gh auth status` previously reported an invalid token even though the first project commit reached GitHub. Recheck GitHub CLI auth before future push/PR workflows.
- The local workspace now contains the Phase 0/1 project scaffold, backend Maven skeleton, and Flyway schema foundation.
- The blueprint file has been copied into the repo as `PROJECT_BLUEPRINT.md`; the original source remains `/Users/parimal_gavali/Developer/Guidewire/InsureFlow_AI_Complete_Project_Blueprint.md`.
- Maven was installed with Homebrew during Phase 0/1 verification and is now available as Maven 3.9.16.
- Docker Desktop was started during Phase 0/1 verification and local Compose/Testcontainers verification passed.
- Local Java is currently OpenJDK 26. The project is configured for Java 21 compatibility, and CI uses Temurin 21.
- GitHub connector could not create a PR for this repository, returning `403 Resource not accessible by integration`; create the PR manually or fix GitHub app write permissions if this recurs.
- Local commits have used the auto-detected Git identity `Parimal Gavali <parimal_gavali@MacBookPro.fritz.box>`. Configure `git config user.name` and `git config user.email` if a different public identity is desired before future commits.
- Phase 9 frontend browser automation was limited locally: Playwright had no bundled browser installed, and system Chrome aborted under automation. Frontend unit tests and production build passed.
- Phase 12 Azure Bicep syntax was not locally compiled because Azure CLI is not installed in this workspace. The deployment validation workflow skips Bicep compilation when `az` is unavailable.

## Near-Term Next Steps

1. Verify Phase 14 portfolio packaging and open the pull request from `portfolio-packaging`.
2. After Phase 14 merges, optionally capture screenshots listed in `docs/demo/screenshot-checklist.md`.
3. Prepare a final public GitHub project description using `docs/portfolio/project-narrative.md`.

## Memory Update Rules

Update this file whenever:

- A phase starts or finishes.
- A major architecture or technology decision is made.
- A GitHub branch, PR, commit, or release is created.
- A blocker appears or is resolved.
- Agent ownership changes.
- A contract between backend, AI, and frontend changes.
- A deployment, demo, or portfolio artifact is published.

Keep entries concise and dated. Prefer links to documents, commits, PRs, and local files instead of long explanations.
