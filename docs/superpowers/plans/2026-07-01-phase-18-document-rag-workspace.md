# Phase 18 Document And RAG Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn document status and grounded Q&A into interactive live frontend workspaces backed by Spring Boot APIs.

**Architecture:** Add backend decision-support endpoints for document workspace summaries and grounded claim Q&A using existing claim, document, coverage, triage, and timeline data. Extend the frontend claim API/repository to load live document intelligence and submit RAG questions through `/api`. Keep demo mode backed by the original demo data.

**Tech Stack:** Java 21, Spring Boot 3, JPA, Testcontainers, Vue 3, TypeScript, Vue Router, Vitest, Vue Test Utils.

---

## Task 1: Add Backend Document/RAG Decision-Support Endpoints

**Files:**
- Modify: `backend/api/src/test/java/com/insureflow/api/claims/ClaimOperationsIntegrationTest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/DocumentWorkspaceResponse.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/RagQuestionRequest.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/RagQuestionResponse.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/api/dto/RagSourceResponse.java`
- Create: `backend/api/src/main/java/com/insureflow/api/claims/service/ClaimDecisionSupportService.java`
- Modify: `backend/api/src/main/java/com/insureflow/api/claims/api/ClaimController.java`

- [x] **Step 1: Write failing backend integration test**

Add a test that creates a claim, adds documents, then verifies:

- `GET /api/v1/claims/{claimNumber}/document-workspace` returns received documents, missing documents, highlights, and summary sections.
- `POST /api/v1/claims/{claimNumber}/rag-query` returns a sourced answer and confidence.

- [x] **Step 2: Run backend test and verify failure**

Run:

```bash
cd backend
mvn -pl api -Dtest=ClaimOperationsIntegrationTest test
```

Expected: fail because the endpoints do not exist.

- [x] **Step 3: Implement backend service and controller methods**

Create deterministic decision-support logic from existing persisted data. Do not approve or reject claims.

- [x] **Step 4: Run backend test and verify pass**

Run:

```bash
cd backend
mvn -pl api -Dtest=ClaimOperationsIntegrationTest test
```

Expected: pass.

## Task 2: Extend Frontend API/Repository

**Files:**
- Modify: `frontend/src/services/claimApi.test.ts`
- Modify: `frontend/src/services/claimApi.ts`
- Modify: `frontend/src/services/claimMapper.ts`
- Modify: `frontend/src/services/claimRepository.ts`
- Modify: `frontend/src/types.ts`

- [x] **Step 1: Write failing frontend service tests**

Add tests for:

- fetching document workspace
- asking a RAG question
- mapping backend responses into `DocumentIntelligenceSnapshot` and `RagAnswer`
- live `getClaim` enriching claim detail with document workspace and default RAG answer

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because frontend services do not expose document/RAG operations yet.

- [x] **Step 3: Implement frontend API, mapper, and repository operations**

Add live repository methods:

- `getDocumentWorkspace`
- `askRagQuestion`

Use demo data in demo mode.

- [x] **Step 4: Run frontend tests and verify pass**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: pass.

## Task 3: Build Interactive Document/RAG Page

**Files:**
- Modify: `frontend/src/pages/DocumentsPage.vue`
- Modify: `frontend/src/components/RagAssistant.vue`
- Modify: `frontend/src/test/App.spec.ts`

- [x] **Step 1: Write failing page test**

Add a test that opens `/documents`, selects/loads a claim document workspace, asks a RAG question, and sees a grounded answer with source text.

- [x] **Step 2: Run frontend tests and verify failure**

Run:

```bash
cd frontend
npm test -- --run
```

Expected: fail because the documents page is still static demo cards.

- [x] **Step 3: Implement page workflow**

Add:

- claim selector
- document workspace panel
- RAG question input
- answer state
- loading/error/empty states
- demo/live data mode label

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
- Modify: `docs/api/document-intelligence.md`
- Modify: `docs/api/rag-assistant.md`
- Modify: `docs/product/dynamic-claims-application-roadmap.md`
- Modify: `docs/README.md`
- Modify: `PROJECT_MEMORY.md`

- [x] **Step 1: Document Phase 18 backend facade**

Explain that Phase 18 exposes live document/RAG decision support through Spring Boot facade endpoints while the Python AI services remain available as lower-level services.

- [x] **Step 2: Update project memory**

Record branch, scope, and verification.

## Task 5: Final Verification

**Files:**
- Read changed source and docs.

- [x] **Step 1: Run backend claim operations test**

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
