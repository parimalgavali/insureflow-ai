# Phase 16 API Client And Live Claim Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the routed claim queue and claim detail pages to live backend claim APIs while preserving explicit demo fallback behavior.

**Architecture:** Add a small backend claim-list endpoint, a typed frontend API client, view-model mapping from backend DTOs to existing frontend `ClaimDetail` data, and page-level loading/error/empty states. The frontend should call the Spring Boot backend through `/api`, with Vite and nginx proxying that path during local and container runs.

**Tech Stack:** Java 21, Spring Boot 3, JPA, Testcontainers, Vue 3, TypeScript, Vue Router, Vite, Vitest, Vue Test Utils.

---

## Task 1: Add Backend Claim List Contract

**Files:**
- Modify: `backend/api/src/test/java/com/insureflow/api/claims/ClaimOperationsIntegrationTest.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/claims/repository/ClaimRepository.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimWorkflowService.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/claims/api/ClaimController.java`

- [x] **Step 1: Write failing backend list test**

Add an integration test that creates two submitted claims and verifies `GET /api/v1/claims` returns both claims ordered by newest reported timestamp first.

- [x] **Step 2: Run backend test and verify failure**

Run:

```bash
cd backend
mvn -pl api -Dtest=ClaimOperationsIntegrationTest test
```

Expected: fail because `GET /api/v1/claims` does not exist.

- [x] **Step 3: Add repository/service/controller list support**

Add `findAllByOrderByReportedAtDesc`, `listClaims`, and `@GetMapping` for `/api/v1/claims`.

- [x] **Step 4: Run backend test and verify pass**

Run:

```bash
cd backend
mvn -pl api -Dtest=ClaimOperationsIntegrationTest test
```

Expected: pass.

## Task 2: Add Frontend API Client And Mapping Tests

**Files:**
- Create: `frontend/src/services/claimApi.ts`
- Create: `frontend/src/services/claimMapper.ts`
- Create: `frontend/src/services/claimRepository.ts`
- Create: `frontend/src/services/claimApi.test.ts`
- Modify: `frontend/src/types.ts`

- [x] **Step 1: Write failing API/mapping tests**

Add tests for:

- API client includes bearer auth from dev-token bootstrap.
- Backend claim DTO maps into existing `ClaimDetail` shape.
- Backend event DTOs map into timeline events.
- Latest triage DTO maps into `TriageSnapshot`.
- Demo mode returns local demo claims without calling fetch.
- Live mode returns mapped backend claims.

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because services do not exist.

- [x] **Step 3: Implement API client, mapper, and repository**

Add:

- `requestDevToken`
- `fetchClaimSummaries`
- `fetchClaim`
- `fetchClaimEvents`
- `fetchClaimTriage`
- `toClaimDetail`
- `createClaimRepository`

Use `/api/v1` as the default base URL so dev/prod proxying works.

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 3: Wire Claim Pages To Repository

**Files:**
- Modify: `frontend/src/pages/ClaimsPage.vue`
- Modify: `frontend/src/pages/ClaimDetailPage.vue`
- Modify: `frontend/src/pages/SettingsPage.vue`
- Modify: `frontend/src/test/App.spec.ts`
- Modify: `frontend/src/test/components.spec.ts`

- [x] **Step 1: Write failing page-state tests**

Add tests for:

- claim queue renders live claims when repository is configured for live mode
- claim detail shows loading/error/empty state boundaries
- settings page displays current data mode

- [x] **Step 2: Run tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because pages still read `demoClaims` directly.

- [x] **Step 3: Implement page state**

Use repository methods in pages and add:

- loading state
- empty state
- error state
- demo/live mode label

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 4: Add Frontend API Proxying

**Files:**
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/nginx.conf`

- [x] **Step 1: Add dev proxy**

Proxy `/api` to `http://localhost:8080` in Vite dev server.

- [x] **Step 2: Add container proxy**

Proxy `/api` to `http://api:8080` in nginx for Docker Compose app profile.

- [x] **Step 3: Run frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: pass.

## Task 5: Update Documentation And Memory

**Files:**
- Modify: `docs/frontend/adjuster-workbench.md`
- Modify: `docs/product/dynamic-claims-application-roadmap.md`
- Modify: `PROJECT_MEMORY.md`

- [x] **Step 1: Document live/demo mode**

Explain how Phase 16 live mode works, how demo fallback works, and that richer document/RAG live behavior remains for Phase 18.

- [x] **Step 2: Update project memory**

Record Phase 16 branch, implementation scope, backend endpoint addition, frontend API client, and verification.

## Task 6: Final Verification

**Files:**
- Read changed source and docs.

- [x] **Step 1: Run focused backend test**

Run:

```bash
cd backend
mvn -pl api -Dtest=ClaimOperationsIntegrationTest test
```

Expected: pass.

- [x] **Step 2: Run frontend tests**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

- [x] **Step 3: Run frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: pass.

- [x] **Step 4: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.
