# InsureFlow AI Master Build Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build InsureFlow AI from an empty repository into a polished Guidewire-inspired insurance technology portfolio platform.

**Architecture:** Build a working vertical product in layers: local infrastructure, Spring Boot insurance domain services, synthetic data, claim workflow, AI triage, ML training, LLM document intelligence, RAG, Vue adjuster UI, integration APIs, governance, deployment, and portfolio packaging. Start with a modular monolith plus separate Python AI services, then split only where the project benefits.

**Tech Stack:** Java 21, Spring Boot 3, Maven, PostgreSQL, Flyway, Testcontainers, Python 3.11/3.12, FastAPI, Pydantic, scikit-learn/XGBoost, pgvector, Vue 3, Vite, TypeScript, Docker Compose, GitHub Actions, Azure or AWS.

---

## Planning Rule

This is the master build plan. Each major phase should get its own detailed implementation plan before code is written for that phase. The detailed phase plans should live in `docs/superpowers/plans/` and should include exact files, tests, commands, and commit points.

Do not attempt to build all phases in one coding pass. The project is large enough that each phase should produce a working, demonstrable increment.

## Phase 0: Repository And Development Setup

**Goal:** Create the professional repository foundation.

**Create:**
- `README.md`
- `PROJECT_BLUEPRINT.md`
- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `docs/architecture/system-context.md`
- `docs/architecture/service-architecture.md`
- `docs/domain/insurance-glossary.md`
- `backend/`
- `ai-services/`
- `frontend/`
- `synthetic-data-generator/`
- `scripts/`

**Build:**
- Docker Compose with PostgreSQL and RabbitMQ.
- Initial README with project purpose, tech stack, responsible AI note, and local setup.
- Empty service folders with README files explaining ownership.
- CI skeleton that checks repo structure.

**Verify:**
- `docker compose up -d postgres rabbitmq`
- `docker compose ps`
- CI workflow syntax is valid.

**Commit:** `chore: initialize insureflow ai repository`

## Phase 1: Backend Skeleton, Domain Model, And Database

**Goal:** Create the Spring Boot backend foundation and relational insurance model.

**Build:**
- Maven multi-module backend.
- Spring Boot application module for the initial API.
- Flyway migrations for customers, policies, coverages, claims, claim documents, claim events, adjusters, AI triage results, human reviews, audit logs, model versions, and prompt versions.
- JPA entities, repositories, DTOs, validation, and shared error response.
- Swagger/OpenAPI setup.

**Test:**
- Flyway migration test with Testcontainers PostgreSQL.
- Repository smoke tests.
- Validation tests for required fields and enum constraints.

**Verify:**
- `cd backend && mvn clean test`
- Swagger UI starts locally.
- Database schema can be created from scratch.

**Commit:** `feat: add insurance domain schema and backend skeleton`

## Phase 2: Synthetic Data Generator

**Goal:** Generate realistic synthetic insurance data with valid relationships.

**Build:**
- Python generator package.
- CSV/JSON outputs for customers, policies, coverages, claims, documents, notes, events, adjusters, payments, AI labels, and audit logs.
- Severity, fraud, and litigation label rules.
- Synthetic document templates for FNOL, invoices, police reports, medical notes, policy documents, emails, and adjuster notes.
- Loader script for PostgreSQL.

**Test:**
- Referential integrity tests.
- Distribution tests for claim severity, fraud risk, policy status, and claim types.
- No-real-PII test using fake domains and synthetic names.

**Verify:**
- `cd synthetic-data-generator && pytest`
- `python -m generator.generate --customers 5000 --policies 6500 --claims 2000`
- `./scripts/load-sample-data.sh`

**Commit:** `feat: add synthetic insurance data generator`

## Phase 3: Policy Service

**Goal:** Implement customer, policy, coverage, and coverage validation behavior.

**Build:**
- Customer CRUD endpoints.
- Policy CRUD endpoints.
- Coverage CRUD endpoints.
- Policy activate, cancel, expire, and renew transitions.
- Coverage-check endpoint.
- Policy lifecycle events.

**Business Rules:**
- Policy must exist.
- Policy must be active on loss date.
- Claim type must map to included coverage.
- Estimated loss must be compared with coverage limit.
- Deductible and exclusions must be returned.

**Test:**
- Active policy covered claim.
- Expired policy.
- Cancelled policy.
- Missing coverage.
- Excluded claim type.
- Over-limit claim.

**Verify:**
- `cd backend && mvn test`
- Swagger documents all policy endpoints.

**Commit:** `feat: implement policy and coverage validation`

## Phase 4: Claims Service And FNOL

**Goal:** Let a customer submit a claim and move it through the first workflow states.

**Build:**
- FNOL endpoint.
- Claim number generation.
- Claim persistence.
- Policy lookup by policy number.
- Coverage validation integration.
- Claim timeline events.
- Claim status transition rules.
- Claim notes and document metadata endpoints.

**Test:**
- Successful FNOL creates claim.
- Unknown policy returns clear error.
- Inactive policy creates coverage issue.
- Claim timeline records submission and validation.
- Invalid status transitions fail.

**Verify:**
- `cd backend && mvn test`
- Submit FNOL through Swagger or HTTP request.

**Commit:** `feat: add fnol claim intake workflow`

## Phase 5: Rule-Based AI Triage Service

**Goal:** Add explainable AI-style triage before training ML models.

**Build:**
- FastAPI triage service.
- Pydantic request/response schemas.
- Rule-based severity scoring.
- Rule-based fraud risk scoring.
- Rule-based litigation scoring.
- Reason code mapping.
- Claims service integration with triage endpoint.
- Store `AITriageResult` in PostgreSQL.

**Test:**
- Pydantic schema validation.
- High severity due to injury and high damage.
- Medium/high fraud risk due to recent policy, late FNOL, missing police report.
- Litigation risk due to injury, third party, and legal keywords.
- Java integration handles AI service success and failure.

**Verify:**
- `cd ai-services && pytest`
- `cd backend && mvn test`
- Submit claim and run triage.

**Commit:** `feat: add rule-based claim triage service`

## Phase 6: ML Model Training And Serving

**Goal:** Replace or augment rules with trained fraud and severity models.

**Build:**
- Dataset source documentation.
- Preprocessing pipeline.
- Fraud baseline model.
- Severity model using synthetic labels.
- XGBoost or LightGBM candidate.
- Metrics report.
- Model cards.
- Serialized model artifacts.
- FastAPI inference path using saved artifacts.

**Test:**
- Feature schema validation.
- Model artifact load test.
- Inference response contract test.
- Metrics file exists and contains AUROC/AUPRC or macro F1 as appropriate.

**Verify:**
- `cd ml && pytest`
- `cd ai-services && pytest`
- Model card documents limitations and intended use.

**Commit:** `feat: train and serve claim risk models`

## Phase 7: LLM Document Intelligence

**Goal:** Add structured extraction and summaries from claim text and documents.

**Build:**
- Document intelligence FastAPI service.
- Prompt templates and prompt version registry.
- Claim description extraction.
- Repair invoice extraction.
- Missing document detection.
- Claim file summary generation.
- JSON schema validation and retry-on-invalid-output.
- Audit storage for prompt, response, prompt version, and parsed output.

**Test:**
- Valid extraction from synthetic claim description.
- Invalid JSON handling.
- Missing police report detection.
- Summary includes required sections.
- Prompt response is audited.

**Verify:**
- `cd ai-services && pytest`
- Manual request against sample synthetic document.

**Commit:** `feat: add llm document intelligence service`

## Phase 8: RAG Adjuster Assistant

**Goal:** Let adjusters ask grounded questions over claim, policy, and guideline documents.

**Build:**
- Enable pgvector.
- `document_chunks` schema.
- Document ingestion endpoint.
- Text chunking with metadata.
- Embedding generation.
- Retrieval query.
- Grounded answer generation.
- Source citation response.
- “Not enough evidence” behavior.

**Test:**
- Chunking preserves metadata.
- Retrieval returns relevant chunks.
- Answer includes source references.
- Unsupported question returns insufficient-evidence response.
- Prompt injection text does not override system constraints.

**Verify:**
- `cd ai-services && pytest`
- Ask: “Is this loss covered?” and receive sourced answer.

**Commit:** `feat: add rag adjuster assistant`

## Phase 9: Vue Adjuster Workbench

**Goal:** Build a recruiter-friendly UI that makes the platform understandable quickly.

**Build:**
- Vue 3/Vite/TypeScript app.
- Claim queue.
- Claim detail.
- Policy panel.
- AI triage panel.
- Document panel.
- Timeline.
- RAG assistant panel.
- Human review and override modal.
- Audit view.

**Design Rules:**
- First screen should be the usable claim queue, not a marketing landing page.
- Use dense, professional dashboard layout.
- Show AI outputs as decision-support signals, not final decisions.
- Make human override visible.

**Test:**
- Component tests for queue and claim detail.
- API mock tests.
- Browser verification on desktop and mobile viewports.

**Verify:**
- `cd frontend && npm test`
- `cd frontend && npm run build`
- Claim demo scenario is visible end-to-end.

**Commit:** `feat: add adjuster workbench frontend`

## Phase 10: Guidewire-Inspired Integration APIs

**Goal:** Demonstrate system-to-system integration thinking.

**Build:**
- Integration API namespace under `/integration/v1`.
- Policy sync endpoint.
- Claim create endpoint.
- Claim status update endpoint.
- Reserve update endpoint.
- Claim lookup endpoint.
- Claim triaged event webhook simulation.
- OpenAPI documentation.
- Postman or HTTP collection.

**Test:**
- Integration role can access integration APIs.
- Bad payloads return consistent errors.
- Claim status update creates timeline and audit entries.

**Verify:**
- `cd backend && mvn test`
- OpenAPI shows integration endpoints separately.

**Commit:** `feat: add guidewire-inspired integration apis`

## Phase 11: Security, Audit, And Governance

**Goal:** Make the project feel enterprise-ready.

**Build:**
- JWT authentication.
- Role-based authorization.
- Audit logging interceptor/aspect.
- AI decision audit.
- Human override reason requirement.
- Correlation IDs.
- Structured JSON logs.
- Model and prompt version registry views.

**Test:**
- Unauthorized request is rejected.
- Role-specific endpoint access.
- Override without reason fails.
- AI triage stores model version, input, output, and reason codes.
- Correlation ID appears in logs and error responses.

**Verify:**
- `cd backend && mvn test`
- Manual role-based API smoke test.

**Commit:** `feat: add security audit and ai governance`

## Phase 12: Cloud Deployment

**Goal:** Deploy a public or semi-public demo.

**Recommended Path:** Azure first for European enterprise positioning.

**Build:**
- Container images for backend, AI services, and frontend.
- Azure Container Apps or App Service deployment.
- Azure Database for PostgreSQL.
- Azure Blob Storage or equivalent object storage.
- Key Vault secrets.
- GitHub Actions deployment workflow.
- Application Insights or Azure Monitor.

**Test:**
- Deployment workflow dry run where possible.
- Health checks.
- Smoke tests against deployed APIs.
- Frontend loads deployed backend config.

**Verify:**
- Demo URL available.
- Health endpoints pass.
- Sample FNOL works in deployed environment.

**Commit:** `chore: add cloud deployment configuration`

## Phase 13: Testing, Quality, And Observability

**Goal:** Raise trust in the project and make regressions visible.

**Build:**
- Test coverage reporting.
- Backend unit and integration coverage target.
- AI schema and inference test suite.
- Frontend build and component tests.
- k6 or JMeter load tests.
- Prometheus/Grafana local observability.
- Trivy or dependency scanning.

**Test:**
- FNOL load test.
- Triage load test.
- Claim queue load test.
- RAG query smoke/load test.

**Verify:**
- `./scripts/run-tests.sh`
- `docker compose up` starts observability stack.
- CI runs backend, AI, and frontend checks.

**Commit:** `test: add project quality gates and observability`

## Phase 14: Documentation And Portfolio Packaging

**Goal:** Make the project easy to evaluate in five minutes and discuss for forty-five minutes.

**Build:**
- Polished README.
- Architecture diagram.
- ER diagram.
- Claim workflow diagram.
- AI triage flow diagram.
- RAG pipeline diagram.
- Dataset strategy.
- Model cards.
- Responsible AI statement.
- Deployment guide.
- Demo script.
- Recruiter walkthrough.
- Screenshots and demo video/GIF.
- Resume bullets.

**Test:**
- Fresh clone setup instructions work.
- Demo script can be followed without improvising.
- README clearly says Guidewire-inspired, not official Guidewire product.

**Verify:**
- New local run from README.
- Five-minute demo scenario works.

**Commit:** `docs: package insureflow ai portfolio demo`

## Recommended Execution Order

1. Finish Phase 0 and Phase 1 before touching AI.
2. Build Phase 2 immediately after the database so the whole system has realistic data.
3. Build Phase 3 and Phase 4 together as the first real business workflow.
4. Build Phase 5 before Phase 6 so AI is integrated into claims before ML complexity arrives.
5. Build Phase 7 and Phase 8 only after the claim/document model is stable.
6. Build frontend after core backend and AI contracts exist.
7. Add security/audit before deployment.
8. Polish documentation continuously, then heavily at the end.

## Success Milestones

- **Milestone 1:** Local infra and backend schema run.
- **Milestone 2:** Synthetic data loads into PostgreSQL.
- **Milestone 3:** FNOL creates a claim and validates coverage.
- **Milestone 4:** AI triage scores a claim and stores reason codes.
- **Milestone 5:** ML model artifacts serve real inference.
- **Milestone 6:** LLM extracts and summarizes claim documents.
- **Milestone 7:** RAG answers adjuster questions with sources.
- **Milestone 8:** Vue workbench shows the full claim intelligence story.
- **Milestone 9:** Security, audit, and integration APIs make it enterprise-grade.
- **Milestone 10:** Cloud demo and portfolio package are ready for recruiters.

## Phase Planning Backlog

Create these detailed plans as the project progresses:

- `2026-06-24-phase-0-1-repository-and-domain-foundation.md`
- `2026-06-24-phase-2-synthetic-data-generator.md`
- `2026-06-24-phase-3-4-policy-and-claims-workflow.md`
- `2026-06-24-phase-5-rule-based-ai-triage.md`
- `2026-06-24-phase-6-ml-training-and-serving.md`
- `2026-06-24-phase-7-llm-document-intelligence.md`
- `2026-06-24-phase-8-rag-adjuster-assistant.md`
- `2026-06-24-phase-9-adjuster-workbench.md`
- `2026-06-24-phase-10-integration-apis.md`
- `2026-06-24-phase-11-security-audit-governance.md`
- `2026-06-24-phase-12-cloud-deployment.md`
- `2026-06-24-phase-13-14-quality-and-portfolio-packaging.md`

