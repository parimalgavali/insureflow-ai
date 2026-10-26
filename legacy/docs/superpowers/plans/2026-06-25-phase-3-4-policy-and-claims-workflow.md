# Phase 3/4 Policy And Claims Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first end-to-end insurance workflow: policy and coverage management plus FNOL claim intake with coverage validation, timeline events, notes, and document metadata.

**Architecture:** Keep this phase inside the existing Spring Boot API module so the domain contracts stabilize before frontend and AI services are added. Split code by business capability under `policy`, `claims`, and `shared`, with service-layer transaction boundaries and controller-level request/response DTOs. Use the existing Flyway schema as the storage contract and add only narrow migrations when the workflow requires stronger constraints or extra columns.

**Tech Stack:** Java 21, Spring Boot 3.3, Spring Web, Spring Data JPA, Bean Validation, Flyway, PostgreSQL, Testcontainers, JUnit 5, AssertJ.

---

## Branch

Use this branch name:

```bash
policy-claims-workflow
```

This branch is currently stacked on top of Phase 2 until the Phase 0/1 and Phase 2 pull requests are merged. After those merge, rebase this branch onto `main` before opening the Phase 3/4 PR.

## Agent Ownership

- **Policy agent:** customer, policy, coverage entities, repositories, lifecycle transitions, coverage validation.
- **Claims agent:** FNOL intake, claim number generation, claim events, notes, document metadata, claim status transitions.
- **Orchestrator:** database migration review, API consistency, integration tests, docs, memory updates, final verification, GitHub coordination.

## File Map

### Create

- `backend/api/src/main/java/com/insureflow/api/shared/domain/BaseEntity.java` - shared UUID and timestamp mapped superclass.
- `backend/api/src/main/java/com/insureflow/api/shared/api/ApiExceptionHandler.java` - maps validation, not-found, and business-rule failures into `ApiErrorResponse`.
- `backend/api/src/main/java/com/insureflow/api/shared/error/BusinessRuleViolationException.java` - 422-style domain failure.
- `backend/api/src/main/java/com/insureflow/api/shared/error/ResourceNotFoundException.java` - 404-style missing resource failure.
- `backend/api/src/main/java/com/insureflow/api/policy/domain/*.java` - customer, policy, coverage entities and enums.
- `backend/api/src/main/java/com/insureflow/api/policy/repository/*.java` - Spring Data repositories.
- `backend/api/src/main/java/com/insureflow/api/policy/api/*.java` - policy-facing controllers and DTO records.
- `backend/api/src/main/java/com/insureflow/api/policy/service/*.java` - policy lifecycle and coverage validation services.
- `backend/api/src/main/java/com/insureflow/api/claims/domain/*.java` - claim, event, note, document entities and enums.
- `backend/api/src/main/java/com/insureflow/api/claims/repository/*.java` - Spring Data repositories.
- `backend/api/src/main/java/com/insureflow/api/claims/api/*.java` - FNOL, claim, note, document, and transition controllers plus DTO records.
- `backend/api/src/main/java/com/insureflow/api/claims/service/*.java` - claim intake, number generation, timeline, notes, documents, transitions.
- `backend/api/src/main/resources/db/migration/V2__policy_claims_workflow_constraints.sql` - adds `claim_notes` table and helpful workflow constraints/indexes.
- `backend/api/src/test/java/com/insureflow/api/support/ApiIntegrationTest.java` - shared Testcontainers integration-test base.
- `backend/api/src/test/java/com/insureflow/api/policy/*.java` - policy and coverage tests.
- `backend/api/src/test/java/com/insureflow/api/claims/*.java` - FNOL and claims workflow tests.
- `docs/api/policy-claims-workflow.md` - API and workflow guide.

### Modify

- `backend/api/src/main/resources/db/migration/V1__create_core_insurance_schema.sql` only if a constraint must be adjusted before V2 can be expressed cleanly.
- `backend/api/src/test/java/com/insureflow/api/database/FlywayMigrationTest.java` to include `claim_notes`.
- `PROJECT_MEMORY.md` after the plan is created, implementation starts, reviews complete, and the branch is pushed.
- `README.md` to include a short backend workflow verification command once implementation is complete.

## API Shape

Base path: `/api/v1`

Policy endpoints:

- `POST /customers`
- `GET /customers/{customerNumber}`
- `POST /policies`
- `GET /policies/{policyNumber}`
- `POST /policies/{policyNumber}/coverages`
- `POST /policies/{policyNumber}/activate`
- `POST /policies/{policyNumber}/cancel`
- `POST /policies/{policyNumber}/expire`
- `POST /policies/{policyNumber}/renew`
- `POST /policies/{policyNumber}/coverage-check`

Claims endpoints:

- `POST /claims/fnol`
- `GET /claims/{claimNumber}`
- `POST /claims/{claimNumber}/status`
- `GET /claims/{claimNumber}/events`
- `POST /claims/{claimNumber}/notes`
- `GET /claims/{claimNumber}/notes`
- `POST /claims/{claimNumber}/documents`
- `GET /claims/{claimNumber}/documents`

## Domain Rules

- A policy must belong to an existing customer.
- `effectiveDate` must be before `expirationDate`.
- Only `DRAFT` policies can be activated.
- `ACTIVE` policies can be cancelled, expired, or renewed.
- Coverage validation succeeds only when the policy is active on `lossDate`.
- Claim type must map to an included coverage type.
- Estimated loss over the coverage limit returns a warning, not a hard rejection.
- Deductible and exclusions are always returned in the coverage validation response when coverage exists.
- FNOL can create a claim with a coverage issue, but the issue must be visible on the claim response and timeline.
- Invalid claim status transitions fail with a business-rule error.

## Claim Type To Coverage Mapping

| Claim Type | Required Coverage Type |
| --- | --- |
| `AUTO_COLLISION` | `COLLISION` |
| `AUTO_COMPREHENSIVE` | `COMPREHENSIVE` |
| `BODILY_INJURY` | `BODILY_INJURY` |
| `PROPERTY_DAMAGE` | `PROPERTY_DAMAGE` |
| `HOME_WATER_DAMAGE` | `WATER_DAMAGE` |
| `HOME_FIRE` | `FIRE` |
| `THEFT` | `THEFT` |

## Claim Status Transitions

| From | Allowed To |
| --- | --- |
| `SUBMITTED` | `UNDER_REVIEW`, `CLOSED` |
| `UNDER_REVIEW` | `PENDING_DOCUMENTS`, `APPROVED`, `DENIED`, `CLOSED` |
| `PENDING_DOCUMENTS` | `UNDER_REVIEW`, `CLOSED` |
| `APPROVED` | `PAYMENT_PENDING`, `CLOSED` |
| `PAYMENT_PENDING` | `PAID`, `CLOSED` |
| `PAID` | `CLOSED` |
| `DENIED` | `CLOSED` |
| `CLOSED` | no transitions |

---

## Task 1: Shared API Errors And Integration Test Harness

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/shared/error/BusinessRuleViolationException.java`
- Create: `backend/api/src/main/java/com/insureflow/api/shared/error/ResourceNotFoundException.java`
- Create: `backend/api/src/main/java/com/insureflow/api/shared/api/ApiExceptionHandler.java`
- Create: `backend/api/src/test/java/com/insureflow/api/support/ApiIntegrationTest.java`
- Test: `backend/api/src/test/java/com/insureflow/api/shared/ApiExceptionHandlerTest.java`

- [ ] **Step 1: Write failing controller error tests**

Create `ApiExceptionHandlerTest` with a test-only controller that throws `ResourceNotFoundException` and `BusinessRuleViolationException`. Verify 404 and 422 responses contain `message`, `path`, and `timestamp`.

- [ ] **Step 2: Run the failing test**

```bash
cd backend
mvn -pl api test -Dtest=ApiExceptionHandlerTest
```

Expected: compilation fails because the shared error classes and handler do not exist.

- [ ] **Step 3: Implement shared errors and handler**

Implement runtime exceptions with a `String message` constructor. Implement `@RestControllerAdvice` that returns the existing `ApiErrorResponse` record for not-found, business-rule, validation, and unexpected failures.

- [ ] **Step 4: Add Testcontainers integration base**

Create `ApiIntegrationTest` with `@SpringBootTest(webEnvironment = RANDOM_PORT)`, a static PostgreSQL 16 container, `@DynamicPropertySource`, and a `TestRestTemplate`.

- [ ] **Step 5: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=ApiExceptionHandlerTest
git add backend/api/src/main/java/com/insureflow/api/shared backend/api/src/test/java/com/insureflow/api/shared backend/api/src/test/java/com/insureflow/api/support
git commit -m "feat: add shared api error handling"
```

## Task 2: Policy Domain, Repositories, And Migration

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/shared/domain/BaseEntity.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/domain/Customer.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/domain/Policy.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/domain/Coverage.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/domain/PolicyStatus.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/domain/PolicyType.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/domain/CoverageType.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/repository/CustomerRepository.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/repository/PolicyRepository.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/repository/CoverageRepository.java`
- Create: `backend/api/src/main/resources/db/migration/V2__policy_claims_workflow_constraints.sql`
- Modify: `backend/api/src/test/java/com/insureflow/api/database/FlywayMigrationTest.java`
- Test: `backend/api/src/test/java/com/insureflow/api/policy/PolicyRepositoryTest.java`

- [ ] **Step 1: Write failing repository test**

Test that saving a customer, policy, and coverage can be queried by `customerNumber`, `policyNumber`, and `(policy, coverageType)`.

- [ ] **Step 2: Run the failing test**

```bash
cd backend
mvn -pl api test -Dtest=PolicyRepositoryTest
```

Expected: compilation fails because policy entities and repositories do not exist.

- [ ] **Step 3: Implement policy entities**

Use the existing tables: `customers`, `policies`, and `coverages`. Map UUID ids, timestamps, enums as strings, dates as `LocalDate`, money as `BigDecimal`, and coverage exclusions as a `String` JSON column for this phase.

- [ ] **Step 4: Implement repositories**

Add repository methods:

```java
Optional<Customer> findByCustomerNumber(String customerNumber);
Optional<Policy> findByPolicyNumber(String policyNumber);
List<Coverage> findByPolicyPolicyNumber(String policyNumber);
Optional<Coverage> findByPolicyAndCoverageType(Policy policy, CoverageType coverageType);
```

- [ ] **Step 5: Add V2 migration**

Create `claim_notes` and indexes:

```sql
CREATE TABLE claim_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    adjuster_id UUID REFERENCES adjusters(id),
    note_type VARCHAR(80) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_claim_notes_claim_id_created_at ON claim_notes(claim_id, created_at);
CREATE INDEX idx_coverages_policy_type ON coverages(policy_id, coverage_type);
```

- [ ] **Step 6: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=PolicyRepositoryTest,FlywayMigrationTest
git add backend/api/src/main/java/com/insureflow/api/shared/domain backend/api/src/main/java/com/insureflow/api/policy backend/api/src/main/resources/db/migration/V2__policy_claims_workflow_constraints.sql backend/api/src/test/java/com/insureflow/api/database backend/api/src/test/java/com/insureflow/api/policy
git commit -m "feat: map policy domain persistence"
```

## Task 3: Customer, Policy, And Coverage APIs

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/policy/api/CustomerController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/api/PolicyController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/api/CoverageController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/api/dto/*.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/service/PolicyManagementService.java`
- Test: `backend/api/src/test/java/com/insureflow/api/policy/PolicyApiIntegrationTest.java`

- [ ] **Step 1: Write failing API integration tests**

Cover:

- `POST /api/v1/customers` creates a customer.
- `POST /api/v1/policies` creates a draft policy for the customer.
- `POST /api/v1/policies/{policyNumber}/coverages` adds coverage.
- `GET /api/v1/policies/{policyNumber}` returns policy and coverages.
- Unknown customer on policy creation returns 404.
- Invalid policy dates return 400.

- [ ] **Step 2: Run the failing tests**

```bash
cd backend
mvn -pl api test -Dtest=PolicyApiIntegrationTest
```

Expected: 404 because endpoints do not exist.

- [ ] **Step 3: Implement request and response records**

Use Bean Validation annotations on request records. Keep response records flat enough for Swagger and demo readability: customer summary, policy summary, and coverage summary.

- [ ] **Step 4: Implement service methods**

Add service methods:

```java
CustomerResponse createCustomer(CreateCustomerRequest request);
CustomerResponse getCustomer(String customerNumber);
PolicyResponse createPolicy(CreatePolicyRequest request);
PolicyResponse getPolicy(String policyNumber);
CoverageResponse addCoverage(String policyNumber, AddCoverageRequest request);
```

- [ ] **Step 5: Implement controllers**

Use `/api/v1` base paths and return `201 Created` for create operations. Do not expose JPA entities directly from controllers.

- [ ] **Step 6: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=PolicyApiIntegrationTest
git add backend/api/src/main/java/com/insureflow/api/policy backend/api/src/test/java/com/insureflow/api/policy
git commit -m "feat: add customer policy and coverage APIs"
```

## Task 4: Policy Lifecycle And Coverage Validation

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/policy/service/CoverageValidationService.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/api/dto/CoverageCheckRequest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/policy/api/dto/CoverageCheckResponse.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/policy/service/PolicyManagementService.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/policy/api/PolicyController.java`
- Test: `backend/api/src/test/java/com/insureflow/api/policy/PolicyLifecycleAndCoverageValidationTest.java`

- [ ] **Step 1: Write failing lifecycle and coverage tests**

Cover:

- Draft policy activates successfully.
- Cancelled policy cannot be activated.
- Active policy renews into a new draft policy number with copied coverages.
- Active policy with matching coverage returns `covered=true`.
- Expired policy returns `covered=false` with reason `POLICY_NOT_ACTIVE_ON_LOSS_DATE`.
- Missing coverage returns reason `COVERAGE_NOT_INCLUDED`.
- Over-limit claim returns `covered=true` with warning `ESTIMATED_LOSS_EXCEEDS_LIMIT`.

- [ ] **Step 2: Run the failing tests**

```bash
cd backend
mvn -pl api test -Dtest=PolicyLifecycleAndCoverageValidationTest
```

Expected: compilation fails until lifecycle and coverage validation methods exist.

- [ ] **Step 3: Implement lifecycle transitions**

Add service methods:

```java
PolicyResponse activate(String policyNumber);
PolicyResponse cancel(String policyNumber);
PolicyResponse expire(String policyNumber);
PolicyResponse renew(String policyNumber);
```

Enforce the domain rules in the service and throw `BusinessRuleViolationException` for invalid transitions.

- [ ] **Step 4: Implement coverage validation**

Add method:

```java
CoverageCheckResponse validate(String policyNumber, CoverageCheckRequest request);
```

Return a deterministic response containing `covered`, `policyStatus`, `coverageType`, `limitAmount`, `deductibleAmount`, `exclusions`, `reasons`, and `warnings`.

- [ ] **Step 5: Add controller routes**

Add lifecycle routes and `POST /api/v1/policies/{policyNumber}/coverage-check`.

- [ ] **Step 6: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=PolicyLifecycleAndCoverageValidationTest
git add backend/api/src/main/java/com/insureflow/api/policy backend/api/src/test/java/com/insureflow/api/policy
git commit -m "feat: add policy lifecycle and coverage validation"
```

## Task 5: Claims Domain And Claim Number Generation

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/claims/domain/Claim.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimEvent.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimNote.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimDocument.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimStatus.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimType.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/domain/ClaimEventType.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/repository/*.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimNumberGenerator.java`
- Test: `backend/api/src/test/java/com/insureflow/api/claims/ClaimRepositoryTest.java`
- Test: `backend/api/src/test/java/com/insureflow/api/claims/ClaimNumberGeneratorTest.java`

- [ ] **Step 1: Write failing repository and generator tests**

Verify a generated claim number matches `CLM-YYYYMMDD-000001` format and saved claims can be queried by `claimNumber`.

- [ ] **Step 2: Run the failing tests**

```bash
cd backend
mvn -pl api test -Dtest=ClaimRepositoryTest,ClaimNumberGeneratorTest
```

Expected: compilation fails because claims domain code does not exist.

- [ ] **Step 3: Implement claims entities**

Map existing tables: `claims`, `claim_events`, `claim_documents`, and new `claim_notes`. Use enum strings and UUID relationships to policy/customer/adjuster where applicable.

- [ ] **Step 4: Implement repositories**

Add methods:

```java
Optional<Claim> findByClaimNumber(String claimNumber);
List<ClaimEvent> findByClaimClaimNumberOrderByCreatedAtAsc(String claimNumber);
List<ClaimNote> findByClaimClaimNumberOrderByCreatedAtDesc(String claimNumber);
List<ClaimDocument> findByClaimClaimNumberOrderByUploadedAtDesc(String claimNumber);
```

- [ ] **Step 5: Implement claim number generator**

Use the current date and the existing claim count for that date to generate deterministic, readable claim numbers. Keep collision handling in the claim intake service by retrying once if the unique constraint is hit.

- [ ] **Step 6: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=ClaimRepositoryTest,ClaimNumberGeneratorTest
git add backend/api/src/main/java/com/insureflow/api/claims backend/api/src/test/java/com/insureflow/api/claims
git commit -m "feat: map claims domain persistence"
```

## Task 6: FNOL Claim Intake Workflow

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/ClaimIntakeController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/FnolRequest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/ClaimResponse.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimIntakeService.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimTimelineService.java`
- Test: `backend/api/src/test/java/com/insureflow/api/claims/FnolWorkflowIntegrationTest.java`

- [ ] **Step 1: Write failing FNOL tests**

Cover:

- Successful FNOL creates claim with status `SUBMITTED`.
- Unknown policy number returns 404.
- Inactive policy creates the claim but includes coverage issue `POLICY_NOT_ACTIVE_ON_LOSS_DATE`.
- Missing coverage creates the claim but includes coverage issue `COVERAGE_NOT_INCLUDED`.
- Timeline records `FNOL_SUBMITTED` and `COVERAGE_VALIDATED`.

- [ ] **Step 2: Run the failing tests**

```bash
cd backend
mvn -pl api test -Dtest=FnolWorkflowIntegrationTest
```

Expected: 404 because FNOL endpoint does not exist.

- [ ] **Step 3: Implement FNOL request**

Required fields: `policyNumber`, `claimType`, `lossDate`, `reportedAt`, `lossLocation`, `description`, and `estimatedLossAmount`.

- [ ] **Step 4: Implement claim intake service**

Look up policy by policy number, run coverage validation, persist claim, persist timeline events, and return claim response with coverage validation summary.

- [ ] **Step 5: Implement controller**

Expose `POST /api/v1/claims/fnol` and return `201 Created`.

- [ ] **Step 6: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=FnolWorkflowIntegrationTest
git add backend/api/src/main/java/com/insureflow/api/claims backend/api/src/test/java/com/insureflow/api/claims
git commit -m "feat: add fnol claim intake workflow"
```

## Task 7: Claim Status, Timeline, Notes, And Documents

**Files:**
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/ClaimController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/ClaimNoteController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/ClaimDocumentController.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/ChangeClaimStatusRequest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/CreateClaimNoteRequest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/CreateClaimDocumentRequest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimWorkflowService.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimNoteService.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimDocumentService.java`
- Test: `backend/api/src/test/java/com/insureflow/api/claims/ClaimOperationsIntegrationTest.java`

- [ ] **Step 1: Write failing claim operation tests**

Cover:

- `GET /api/v1/claims/{claimNumber}` returns the claim.
- `GET /api/v1/claims/{claimNumber}/events` returns ordered timeline.
- Valid status transition appends `STATUS_CHANGED`.
- Invalid status transition returns 422 and does not change status.
- Creating a note persists and lists newest first.
- Creating document metadata persists and lists newest first.

- [ ] **Step 2: Run the failing tests**

```bash
cd backend
mvn -pl api test -Dtest=ClaimOperationsIntegrationTest
```

Expected: 404 because operation endpoints do not exist.

- [ ] **Step 3: Implement status workflow service**

Apply the status transition table in this plan. Persist a timeline event for each successful transition.

- [ ] **Step 4: Implement timeline, note, and document services**

Return response records only. Store document `storageUri`, `fileName`, `documentType`, and `contentType`; this phase does not upload binary files.

- [ ] **Step 5: Implement controllers**

Expose claim read, event read, status transition, note, and document metadata routes under `/api/v1/claims/{claimNumber}`.

- [ ] **Step 6: Verify and commit**

```bash
cd backend
mvn -pl api test -Dtest=ClaimOperationsIntegrationTest
git add backend/api/src/main/java/com/insureflow/api/claims backend/api/src/test/java/com/insureflow/api/claims
git commit -m "feat: add claim workflow operations"
```

## Task 8: Documentation, Memory, And Full Verification

**Files:**
- Create: `docs/api/policy-claims-workflow.md`
- Modify: `README.md`
- Modify: `PROJECT_MEMORY.md`
- Modify: `docs/README.md`

- [ ] **Step 1: Write workflow documentation**

Document a runnable demo path:

1. Create customer.
2. Create policy.
3. Add coverage.
4. Activate policy.
5. Run coverage check.
6. Submit FNOL.
7. Read claim timeline.
8. Add note.
9. Add document metadata.
10. Change claim status.

- [ ] **Step 2: Update README**

Add a short backend API section with:

```bash
docker compose up -d postgres rabbitmq
cd backend
mvn test
```

Include Swagger URL: `http://localhost:8080/swagger-ui.html`.

- [ ] **Step 3: Update project memory**

Record:

- Branch `policy-claims-workflow`.
- Detailed plan file path.
- Phase 3/4 ownership model.
- Verification result after implementation.
- PR link after push.

- [ ] **Step 4: Run full verification**

```bash
./scripts/run-tests.sh
git diff --check
```

Expected: backend and synthetic-data-generator tests pass; whitespace check prints no output.

- [ ] **Step 5: Push branch**

```bash
git push -u origin policy-claims-workflow
```

- [ ] **Step 6: Open PR after prerequisites merge**

Open this branch only after Phase 0/1 and Phase 2 are merged or after rebasing onto updated `main`.

## Final Acceptance Criteria

- `./scripts/run-tests.sh` passes.
- Swagger shows policy and claims endpoints.
- Coverage validation returns explicit reasons and warnings.
- FNOL creates a claim, coverage validation summary, and timeline events.
- Invalid policy lifecycle and claim status transitions return clear business-rule errors.
- Docs and project memory are updated.
- Branch is pushed as `policy-claims-workflow`.

## Self-Review

- **Spec coverage:** Covers Phase 3 customer/policy/coverage CRUD, lifecycle, coverage validation, and Phase 4 FNOL, claim persistence, timeline, status transitions, notes, and document metadata.
- **Placeholder scan:** No intentionally deferred implementation work is left in the phase plan.
- **Type consistency:** API names, branch name, package names, endpoint paths, and status/coverage enums are consistent across tasks.

## Execution Options

Plan complete and saved to `docs/superpowers/plans/2026-06-25-phase-3-4-policy-and-claims-workflow.md`. Two execution options:

1. **Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, with review checkpoints.

