# Phase 19 Governance And Audit Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live governance and audit dashboard where reviewers can inspect model versions, prompt versions, audit events, and AI decision evidence.

**Architecture:** Extend the Spring Boot audit API with a small filtered search endpoint while preserving the existing entity-specific audit endpoint. Add typed frontend governance API and repository methods that run in demo mode from local claim data and in live mode through Spring Boot. Replace the static `/governance` page with a filterable operational dashboard.

**Tech Stack:** Java 21, Spring Boot 3, JPA, Testcontainers, Vue 3, TypeScript, Vue Router, Vitest, Vue Test Utils.

---

## File Structure

- Modify `backend/api/src/test/java/com/insureflow/api/audit/CorrelationAndAuditIntegrationTest.java`
  - Add red coverage for `GET /api/v1/audit/events` filters by actor, entity type, and correlation ID.
- Modify `backend/api/src/main/java/com/insureflow/api/audit/AuditLogRepository.java`
  - Add a JPA query method for filtered audit search with a result limit.
- Modify `backend/api/src/main/java/com/insureflow/api/audit/AuditLogController.java`
  - Add `GET /events` with optional request parameters.
- Modify `frontend/src/types.ts`
  - Add governance dashboard view-model types.
- Modify `frontend/src/services/claimApi.ts`
  - Add backend governance and audit DTOs plus API methods.
- Modify `frontend/src/services/claimApi.test.ts`
  - Add failing tests for API calls, mapping, and repository behavior.
- Modify `frontend/src/services/claimMapper.ts`
  - Add mapping from backend governance/audit DTOs to frontend view models.
- Modify `frontend/src/services/claimRepository.ts`
  - Add `getGovernanceDashboard(filters)` with demo and live implementations.
- Modify `frontend/src/pages/GovernancePage.vue`
  - Replace static demo audit cards with live/demo dashboard widgets and filters.
- Modify `frontend/src/test/App.spec.ts`
  - Add a route test for governance dashboard filtering.
- Modify docs:
  - `docs/api/security-audit-governance.md`
  - `docs/frontend/adjuster-workbench.md`
  - `docs/product/dynamic-claims-application-roadmap.md`
  - `docs/README.md`
  - `PROJECT_MEMORY.md`

## Task 1: Add Filtered Audit Search API

- [x] **Step 1: Write failing backend integration test**

Add a test to `CorrelationAndAuditIntegrationTest`:

```java
@Test
void auditorCanSearchAuditEventsByActorEntityAndCorrelationId() {
    String adjusterToken = token("phase-19-adjuster", "ADJUSTER");
    String auditorToken = token("phase-19-auditor", "AUDITOR");
    HttpHeaders headers = new HttpHeaders();
    headers.setBearerAuth(adjusterToken);
    headers.set("X-Correlation-Id", "corr-phase-19-001");

    restTemplate.exchange(
            baseUrl + "/claims/CLM-PHASE-19-MISSING",
            HttpMethod.GET,
            new HttpEntity<>(headers),
            MAP_RESPONSE);

    ResponseEntity<List<Map<String, Object>>> response = restTemplate.exchange(
            baseUrl + "/audit/events?entityType=CLAIMS&actorId=phase-19-adjuster&correlationId=corr-phase-19-001&limit=10",
            HttpMethod.GET,
            authEntity(auditorToken),
            LIST_RESPONSE);

    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    assertThat(response.getBody())
            .anySatisfy(log -> {
                assertThat(log).containsEntry("actorId", "phase-19-adjuster");
                assertThat(log).containsEntry("entityType", "CLAIMS");
                assertThat(log).containsEntry("correlationId", "corr-phase-19-001");
            });
}
```

- [x] **Step 2: Run backend test and verify failure**

Run:

```bash
cd backend
mvn -pl api -Dtest=CorrelationAndAuditIntegrationTest test
```

Expected: fail because `/api/v1/audit/events` does not exist yet.

- [x] **Step 3: Implement repository query and controller endpoint**

Add a limited filtered query:

```java
@Query("""
        select log from AuditLog log
        where (:entityType is null or log.entityType = :entityType)
          and (:actorId is null or log.actorId = :actorId)
          and (:action is null or log.action like concat('%', :action, '%'))
          and (:correlationId is null or log.correlationId = :correlationId)
        order by log.createdAt desc
        """)
List<AuditLog> search(
        @Param("entityType") String entityType,
        @Param("actorId") String actorId,
        @Param("action") String action,
        @Param("correlationId") String correlationId,
        Pageable pageable);
```

Add `GET /api/v1/audit/events` to `AuditLogController` with optional `entityType`, `actorId`, `action`, `correlationId`, and `limit` request parameters.

- [x] **Step 4: Run backend test and verify pass**

Run:

```bash
cd backend
mvn -pl api -Dtest=CorrelationAndAuditIntegrationTest test
```

Expected: pass.

## Task 2: Add Frontend Governance API And Repository

- [x] **Step 1: Write failing frontend service tests**

Add tests in `frontend/src/services/claimApi.test.ts` that assert:

- `fetchModelVersions()` calls `/api/v1/governance/model-versions`
- `fetchPromptVersions()` calls `/api/v1/governance/prompt-versions`
- `fetchAuditEvents({ entityType: "CLAIMS", actorId: "demo-adjuster" })` calls `/api/v1/audit/events?entityType=CLAIMS&actorId=demo-adjuster`
- `createClaimRepository({ mode: "live" }).getGovernanceDashboard(filters)` returns mapped models, prompts, audit events, and AI evidence
- `createClaimRepository({ mode: "demo" }).getGovernanceDashboard(filters)` returns demo evidence without live API calls

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because governance API/repository methods are not implemented.

- [x] **Step 3: Implement frontend types, API, mappers, and repository**

Add:

```ts
export interface GovernanceDashboard {
  modelVersions: GovernanceModelVersion[];
  promptVersions: GovernancePromptVersion[];
  auditEvents: GovernanceAuditEvent[];
  aiEvidence: GovernanceAiEvidence[];
}
```

Use demo claims to derive demo AI evidence from triage, RAG sources, and audit entries. Use live API methods for model, prompt, and audit data in live mode.

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 3: Build Interactive Governance Page

- [x] **Step 1: Write failing route test**

Add an app test that opens `/governance`, verifies model/prompt/audit/evidence sections, enters an actor filter, submits the filter form, and still sees audit evidence.

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because `/governance` is still static demo audit cards.

- [x] **Step 3: Implement dashboard UI**

Replace `GovernancePage.vue` with:

- dashboard summary counts
- model version table/cards
- prompt version cards
- audit filter form
- audit event cards with correlation IDs
- AI evidence cards linking claim, severity, reason codes, RAG source count, and human review flag
- loading, error, and empty states

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 4: Update Documentation And Memory

- [x] **Step 1: Document Phase 19 API and frontend behavior**

Update:

- `docs/api/security-audit-governance.md`
- `docs/frontend/adjuster-workbench.md`
- `docs/product/dynamic-claims-application-roadmap.md`
- `docs/README.md`

- [x] **Step 2: Update project memory**

Record the Phase 19 branch, scope, and verification in `PROJECT_MEMORY.md`.

## Task 5: Final Verification

- [x] **Step 1: Run backend audit test**

```bash
cd backend
mvn -pl api -Dtest=CorrelationAndAuditIntegrationTest test
```

- [x] **Step 2: Run governance registry test**

```bash
cd backend
mvn -pl api -Dtest=GovernanceRegistryIntegrationTest test
```

- [x] **Step 3: Run frontend tests**

```bash
cd frontend
npm test -- --run
```

- [x] **Step 4: Run frontend build**

```bash
cd frontend
npm run build
```

- [x] **Step 5: Run whitespace check**

```bash
git diff --check
```

Expected: all commands pass.
