# Phase 17 Human Review Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist human review decisions from the routed frontend through the live backend API and show review history on the claim review page.

**Architecture:** Reuse the existing Spring Boot human-review API under `/api/v1/claims/{claimNumber}/human-reviews`. Extend frontend API/repository services with create/list review operations, align review form values with backend decisions, and keep demo mode usable with local in-memory review state.

**Tech Stack:** Java 21, Spring Boot 3, Testcontainers, Vue 3, TypeScript, Vue Router, Vitest, Vue Test Utils.

---

## Task 1: Strengthen Backend Human Review Regression Coverage

**Files:**
- Modify: `backend/api/src/test/java/com/insureflow/api/humanreview/HumanReviewIntegrationTest.java`

- [x] **Step 1: Write backend timeline assertion**

Extend the existing human review integration test to verify that submitting a human review creates a `HUMAN_REVIEW_RECORDED` claim timeline event.

- [x] **Step 2: Run backend test**

Run:

```bash
cd backend
mvn -pl api -Dtest=HumanReviewIntegrationTest test
```

Expected: pass, because the backend already records the event.

## Task 2: Add Frontend Human Review API Tests

**Files:**
- Modify: `frontend/src/services/claimApi.test.ts`
- Modify: `frontend/src/services/claimApi.ts`
- Modify: `frontend/src/services/claimRepository.ts`
- Modify: `frontend/src/types.ts`

- [x] **Step 1: Write failing API/repository tests**

Add tests for:

- `fetchHumanReviews` calls `GET /claims/{claimNumber}/human-reviews`.
- `createHumanReview` posts reviewer ID, decision, override reason, and notes.
- Live repository submits and reloads human review history.
- Demo repository records human reviews in memory.

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because review operations do not exist yet.

- [x] **Step 3: Implement review service methods**

Add backend DTOs and repository methods for human review create/list operations.

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 3: Wire Human Review Page To Repository

**Files:**
- Modify: `frontend/src/components/HumanReviewModal.vue`
- Modify: `frontend/src/pages/HumanReviewPage.vue`
- Modify: `frontend/src/test/App.spec.ts`
- Modify: `frontend/src/test/components.spec.ts`

- [x] **Step 1: Write failing page/form tests**

Add tests for:

- review form emits backend decision values
- route-backed review page shows submitted live/demo review history
- submission errors are displayed

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because the page still stores only local submitted state and modal values are old frontend-only actions.

- [x] **Step 3: Implement page persistence**

Use the repository to load claim context, list reviews, submit reviews, show loading/error/success states, and render review history.

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 4: Update Documentation And Memory

**Files:**
- Modify: `docs/frontend/adjuster-workbench.md`
- Modify: `docs/api/security-audit-governance.md`
- Modify: `docs/product/dynamic-claims-application-roadmap.md`
- Modify: `docs/README.md`
- Modify: `PROJECT_MEMORY.md`

- [x] **Step 1: Document live review behavior**

Explain that Phase 17 makes human review submission/listing live through the backend in `VITE_DATA_MODE=live`, and note the required `VITE_REVIEWER_ADJUSTER_ID` for live submission.

- [x] **Step 2: Update memory**

Record Phase 17 branch, implementation scope, and verification.

## Task 5: Final Verification

**Files:**
- Read changed source and docs.

- [x] **Step 1: Run backend human review test**

Run:

```bash
cd backend
mvn -pl api -Dtest=HumanReviewIntegrationTest test
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
