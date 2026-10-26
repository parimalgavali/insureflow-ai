# Phase 11 Security, Audit, And Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JWT authentication, role-based access, correlation IDs, durable audit logging, AI decision traceability, human override enforcement, and governance registry views.

**Architecture:** Use Spring Security with a local HMAC JWT service for demo/test tokens. Add servlet filters for correlation IDs and request audit, extend AI triage persistence with input/output snapshots, add human review APIs over the existing `human_reviews` table, and expose read-only model/prompt registry views.

**Tech Stack:** Java 21, Spring Boot 3, Spring Security, Spring MVC, Bean Validation, Spring Data JPA, Flyway, PostgreSQL JSONB, Testcontainers, JUnit 5, AssertJ.

---

## File Structure

- Modify `backend/api/pom.xml`
  Add Spring Security dependency.
- Modify `backend/api/src/main/resources/application.yml`
  Add JWT secret/issuer/expiry configuration.
- Create `backend/api/src/main/resources/logback-spring.xml`
  Structured key-value logging pattern.
- Create `backend/api/src/main/resources/db/migration/V5__security_audit_governance.sql`
  Add AI triage snapshot columns, improve audit indexes, and seed model/prompt registry rows.
- Create package `com.insureflow.api.security`
  JWT service, auth filter, security config, principal model, role enum, and dev token endpoint.
- Create package `com.insureflow.api.audit`
  Audit entity/repository, correlation filter, audit filter, audit controller, and DTOs.
- Create package `com.insureflow.api.governance`
  Model/prompt registry entities, repositories, DTOs, and controller.
- Create package `com.insureflow.api.humanreview`
  Human review entity/repository/service/controller/DTOs and decision enum.
- Create package `com.insureflow.api.adjusters`
  Minimal adjuster entity/repository for reviewer references.
- Modify `ClaimTriageService` and `AiTriageResult`
  Persist input/output snapshots.
- Modify `ClaimEventType`
  Add `HUMAN_REVIEW_RECORDED`.
- Modify `ApiExceptionHandler`
  Add 401/403 handling when needed and preserve correlation ID behavior.
- Create tests:
  - `SecurityAccessIntegrationTest`
  - `CorrelationAndAuditIntegrationTest`
  - `GovernanceRegistryIntegrationTest`
  - `HumanReviewIntegrationTest`
  - update `ClaimTriageIntegrationTest`

## Tasks

### Task 1: Planning Artifacts

- [x] **Step 1: Write Phase 11 design spec**

Save `docs/superpowers/specs/2026-06-28-phase-11-security-audit-governance-design.md`.

- [x] **Step 2: Write Phase 11 implementation plan**

Save `docs/superpowers/plans/2026-06-28-phase-11-security-audit-governance.md`.

- [ ] **Step 3: Update project memory and commit docs**

Run:

```bash
git add PROJECT_MEMORY.md docs/superpowers/specs/2026-06-28-phase-11-security-audit-governance-design.md docs/superpowers/plans/2026-06-28-phase-11-security-audit-governance.md
git commit -m "docs: plan phase 11 security audit governance"
```

### Task 2: RED Security And Role Tests

- [ ] **Step 1: Write failing tests**

Create `SecurityAccessIntegrationTest` covering:

- no token rejects protected `/api/v1/claims/anything` with 401;
- adjuster token can call standard `/api/v1/**` workflow endpoints;
- integration token can call `/integration/v1/**`;
- integration token cannot call `/api/v1/governance/model-versions`;
- auditor token can call governance/audit endpoints;
- admin token can call all protected namespaces.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd backend && mvn -pl api test -Dtest=SecurityAccessIntegrationTest
```

Expected: tests fail because security config and token generation do not exist yet.

### Task 3: JWT Security Implementation

- [ ] **Step 1: Add dependency and config**

Add `spring-boot-starter-security` and `insureflow.security.jwt` settings.

- [ ] **Step 2: Implement JWT service and auth filter**

Create HMAC SHA-256 token creation/validation, principal extraction, role parsing, and `Authorization: Bearer` filter behavior.

- [ ] **Step 3: Implement role authorization**

Configure:

- public health/swagger/dev-token;
- `/integration/v1/**` requires `INTEGRATION` or `ADMIN`;
- `/api/v1/audit/**` and `/api/v1/governance/**` require `AUDITOR` or `ADMIN`;
- all other `/api/v1/**` requires `ADJUSTER` or `ADMIN`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd backend && mvn -pl api test -Dtest=SecurityAccessIntegrationTest
```

Expected: security access tests pass.

### Task 4: Correlation And Request Audit

- [ ] **Step 1: Write failing tests**

Create `CorrelationAndAuditIntegrationTest` covering response correlation headers, error correlation IDs, and audit row creation for protected requests.

- [ ] **Step 2: Implement correlation filter**

Generate or preserve `X-Correlation-Id`, put it in MDC, response headers, and request attributes.

- [ ] **Step 3: Implement audit entity/repository/filter/controller**

Map existing `audit_logs`, write records after protected requests, and expose:

- `GET /api/v1/audit/entity/{entityType}/{entityId}`
- `GET /api/v1/audit/claims/{claimNumber}`

- [ ] **Step 4: Verify**

Run:

```bash
cd backend && mvn -pl api test -Dtest=CorrelationAndAuditIntegrationTest
```

Expected: correlation and audit tests pass.

### Task 5: AI Decision Audit Snapshots

- [ ] **Step 1: Write failing test**

Update `ClaimTriageIntegrationTest` or add `AiDecisionAuditIntegrationTest` to assert persisted triage rows contain input and output snapshots.

- [ ] **Step 2: Add migration and entity fields**

Add `input_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb` and `output_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb` to `ai_triage_results`.

- [ ] **Step 3: Persist snapshots**

Capture the assembled triage request before calling the triage client and the score response after the client returns.

- [ ] **Step 4: Verify**

Run:

```bash
cd backend && mvn -pl api test -Dtest=ClaimTriageIntegrationTest,AiTriageResultRepositoryTest
```

Expected: AI triage and repository tests pass.

### Task 6: Human Review Override Enforcement

- [ ] **Step 1: Write failing tests**

Create `HumanReviewIntegrationTest` covering:

- override without reason returns 400;
- override with reason creates a human review;
- accepted AI recommendation can omit override reason;
- list endpoint returns reviews.

- [ ] **Step 2: Implement adjuster and human review persistence**

Map `adjusters` and `human_reviews`, add repositories, DTOs, service, controller, and `HUMAN_REVIEW_RECORDED` timeline event.

- [ ] **Step 3: Verify**

Run:

```bash
cd backend && mvn -pl api test -Dtest=HumanReviewIntegrationTest
```

Expected: human review tests pass.

### Task 7: Governance Registry Views

- [ ] **Step 1: Write failing tests**

Create `GovernanceRegistryIntegrationTest` covering model and prompt registry endpoints with auditor access.

- [ ] **Step 2: Implement entities/repositories/controller**

Map `model_versions` and `prompt_versions`, add DTOs, expose read-only endpoints, and seed local registry rows in V5.

- [ ] **Step 3: Verify**

Run:

```bash
cd backend && mvn -pl api test -Dtest=GovernanceRegistryIntegrationTest
```

Expected: governance registry tests pass.

### Task 8: Documentation And Final Verification

- [ ] **Step 1: Write API documentation**

Create `docs/api/security-audit-governance.md` with role matrix, token examples, protected endpoints, audit behavior, governance endpoints, and smoke tests.

- [ ] **Step 2: Link docs**

Update `README.md` and `docs/README.md`.

- [ ] **Step 3: Run verification**

Run:

```bash
./scripts/run-tests.sh
git diff --check
```

Expected: all project checks pass.

- [ ] **Step 4: Update memory, commit, push, PR**

Update `PROJECT_MEMORY.md`, commit implementation, push `security-audit-governance`, and open a PR into `main`.

## Self-Review

- Spec coverage: authentication, authorization, audit, correlation IDs, AI audit, human override enforcement, registry views, structured logs, docs, and tests are covered.
- Placeholder scan: no unresolved placeholders or deferred requirements remain.
- Type consistency: role, endpoint, table, and DTO names are consistent across tasks.
