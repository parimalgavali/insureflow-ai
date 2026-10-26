# Phase 10 Guidewire Integration APIs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Guidewire-inspired `/integration/v1` APIs for policy sync, claim creation, claim lookup, claim status updates, reserve updates, and claim-triaged webhook simulation.

**Architecture:** Add a Spring Boot integration facade that delegates to existing policy and claim workflow services, then records lightweight integration events. Add claim reserve persistence because Phase 10 explicitly needs reserve update integration.

**Tech Stack:** Java 21, Spring Boot, Spring MVC, Bean Validation, Spring Data JPA, PostgreSQL/Flyway, Testcontainers, JUnit 5, AssertJ.

---

## File Structure

- Create `backend/api/src/main/resources/db/migration/V4__integration_api_contract.sql`
  Defines `integration_events` and `claim_reserves`.
- Create `backend/api/src/main/java/com/insureflow/api/integration/domain/IntegrationEvent.java`
  JPA entity for integration operational events.
- Create `backend/api/src/main/java/com/insureflow/api/integration/domain/IntegrationEventStatus.java`
  Event status enum.
- Create `backend/api/src/main/java/com/insureflow/api/integration/repository/IntegrationEventRepository.java`
  Repository for integration events.
- Create `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimReserve.java`
  JPA entity for claim reserve updates.
- Create `backend/api/src/main/java/com/insureflow/api/claims/repository/ClaimReserveRepository.java`
  Repository for claim reserves.
- Modify `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimEventType.java`
  Add `RESERVE_UPDATED`.
- Create `backend/api/src/main/java/com/insureflow/api/integration/api/dto/*.java`
  Request and response records for integration APIs.
- Create `backend/api/src/main/java/com/insureflow/api/integration/service/IntegrationEventService.java`
  Small service for event recording.
- Create `backend/api/src/main/java/com/insureflow/api/integration/service/IntegrationApiService.java`
  Orchestrates policy sync, claim create, status update, reserve update, and webhook acknowledgement.
- Create `backend/api/src/main/java/com/insureflow/api/integration/api/IntegrationController.java`
  REST controller under `/integration/v1`.
- Create `backend/api/src/test/java/com/insureflow/api/integration/IntegrationApiIntegrationTest.java`
  End-to-end integration API tests.
- Create `docs/api/integration-apis.md`
  Phase 10 API documentation.
- Create `docs/api/collections/phase-10-integration-apis.http`
  Replayable HTTP collection.
- Modify `README.md`, `docs/README.md`, and `PROJECT_MEMORY.md`
  Link docs and record phase state.

## Tasks

### Task 1: Documentation Baseline

- [x] **Step 1: Write design spec**

Save the approved design at `docs/superpowers/specs/2026-06-26-phase-10-guidewire-integration-apis-design.md`.

- [x] **Step 2: Write implementation plan**

Save this plan at `docs/superpowers/plans/2026-06-26-phase-10-guidewire-integration-apis.md`.

- [ ] **Step 3: Commit planning artifacts**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-phase-10-guidewire-integration-apis-design.md docs/superpowers/plans/2026-06-26-phase-10-guidewire-integration-apis.md PROJECT_MEMORY.md
git commit -m "docs: plan phase 10 integration apis"
```

### Task 2: RED Integration API Tests

- [ ] **Step 1: Create failing integration test**

Create `backend/api/src/test/java/com/insureflow/api/integration/IntegrationApiIntegrationTest.java` with tests for:

- `POST /integration/v1/policies/sync`
- `POST /integration/v1/claims`
- `GET /integration/v1/claims/{claimNumber}`
- `POST /integration/v1/claims/{claimNumber}/status`
- `POST /integration/v1/claims/{claimNumber}/reserves`
- `POST /integration/v1/webhooks/claim-triaged`
- validation failure on bad policy sync payload

- [ ] **Step 2: Verify RED**

Run:

```bash
cd backend && mvn -pl api test -Dtest=IntegrationApiIntegrationTest
```

Expected: tests fail because `/integration/v1` endpoints do not exist yet.

### Task 3: Database And Domain

- [ ] **Step 1: Add Flyway migration**

Add `V4__integration_api_contract.sql` with `integration_events` and `claim_reserves` tables, foreign key from reserves to claims, and useful indexes.

- [ ] **Step 2: Add entities and repositories**

Add `IntegrationEvent`, `IntegrationEventStatus`, `IntegrationEventRepository`, `ClaimReserve`, and `ClaimReserveRepository`.

- [ ] **Step 3: Add timeline enum**

Add `RESERVE_UPDATED` to `ClaimEventType`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
cd backend && mvn -pl api test -Dtest=FlywayMigrationTest
```

Expected: migration tests pass.

### Task 4: Integration Services And Controller

- [ ] **Step 1: Add DTO records**

Add request/response records under `com.insureflow.api.integration.api.dto`.

- [ ] **Step 2: Add event recorder**

Create `IntegrationEventService.recordAccepted(...)` and `IntegrationEventService.recordCompleted(...)` helpers.

- [ ] **Step 3: Add orchestration service**

Create `IntegrationApiService` methods:

- `syncPolicy(PolicySyncRequest request)`
- `createClaim(IntegrationClaimCreateRequest request)`
- `getClaim(String claimNumber)`
- `changeClaimStatus(String claimNumber, IntegrationClaimStatusUpdateRequest request)`
- `updateReserve(String claimNumber, ReserveUpdateRequest request)`
- `acknowledgeClaimTriaged(ClaimTriagedWebhookRequest request)`

- [ ] **Step 4: Add controller**

Expose `/integration/v1` endpoints in `IntegrationController`.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd backend && mvn -pl api test -Dtest=IntegrationApiIntegrationTest
```

Expected: Phase 10 integration tests pass.

### Task 5: API Documentation And Collection

- [ ] **Step 1: Write API docs**

Create `docs/api/integration-apis.md` with endpoint descriptions, request examples, response examples, and local verification commands.

- [ ] **Step 2: Add HTTP collection**

Create `docs/api/collections/phase-10-integration-apis.http` with sequential requests using variables for customer, policy, and claim numbers.

- [ ] **Step 3: Link docs**

Update `README.md` and `docs/README.md` with Phase 10 links.

### Task 6: Verification, Memory, And PR

- [ ] **Step 1: Run full verification**

Run:

```bash
./scripts/run-tests.sh
git diff --check
```

Expected: all checks pass and whitespace check is clean.

- [ ] **Step 2: Update project memory**

Record Phase 10 implementation, verification evidence, branch, and PR details in `PROJECT_MEMORY.md`.

- [ ] **Step 3: Commit implementation**

Run:

```bash
git add backend docs README.md PROJECT_MEMORY.md
git commit -m "feat: add guidewire integration apis"
```

- [ ] **Step 4: Push branch and open pull request**

Run:

```bash
git push -u origin integration-apis
gh pr create --base main --head integration-apis --title "Phase 10: Guidewire integration APIs" --body-file /tmp/phase-10-pr-body.md
```

## Self-Review

- Spec coverage: the plan covers integration namespace, policy sync, claim create, status update, reserve update, webhook simulation, docs, collection, and tests.
- Placeholder scan: no `TBD` or deferred implementation placeholders remain.
- Type consistency: DTO, service, repository, and endpoint names are stable across tasks.
