# Phase 8 RAG Adjuster Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline RAG assistant service that ingests claim/policy/guideline text, chunks it, retrieves relevant evidence for adjuster questions, returns grounded answers with sources, and refuses to answer when evidence is missing.

**Architecture:** Add `ai-services/rag-service` as a separate FastAPI service. The service uses Pydantic schemas, deterministic chunking, an in-memory chunk store, lexical retrieval, safe answer generation, and in-memory audit. The metadata and interfaces are designed so pgvector and hosted embeddings can replace the local store/retriever in a later phase.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pytest, httpx, uvicorn.

---

## File Structure

- Create `ai-services/rag-service/pyproject.toml`
- Create `ai-services/rag-service/README.md`
- Create `ai-services/rag-service/rag_service/__init__.py`
- Create `ai-services/rag-service/rag_service/schemas.py`
- Create `ai-services/rag-service/rag_service/chunking.py`
- Create `ai-services/rag-service/rag_service/store.py`
- Create `ai-services/rag-service/rag_service/retrieval.py`
- Create `ai-services/rag-service/rag_service/answering.py`
- Create `ai-services/rag-service/rag_service/audit.py`
- Create `ai-services/rag-service/rag_service/service.py`
- Create `ai-services/rag-service/rag_service/app.py`
- Create `ai-services/rag-service/tests/test_api.py`
- Create `ai-services/rag-service/tests/test_retrieval.py`
- Create `docs/api/rag-assistant.md`
- Modify `scripts/run-tests.sh`
- Modify `README.md`, `docs/README.md`, `ai-services/README.md`, and `PROJECT_MEMORY.md`

## Task 1: Documentation Foundation

**Files:**
- Create: `docs/superpowers/specs/2026-06-26-phase-8-rag-adjuster-assistant-design.md`
- Create: `docs/superpowers/plans/2026-06-26-phase-8-rag-adjuster-assistant.md`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Confirm branch**

Run: `git status --short --branch`

Expected: branch is `rag-adjuster-assistant`.

- [ ] **Step 2: Write design and plan docs**

Document scope, API contract, local retrieval approach, source-citation behavior, audit, tests, and done criteria.

- [ ] **Step 3: Update project memory**

Add:

```markdown
| 2026-06-26 | Started Phase 8 RAG adjuster assistant. | Branch `rag-adjuster-assistant`; design and implementation plan created for the offline RAG service. |
```

- [ ] **Step 4: Commit documentation**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-phase-8-rag-adjuster-assistant-design.md docs/superpowers/plans/2026-06-26-phase-8-rag-adjuster-assistant.md PROJECT_MEMORY.md
git commit -m "docs: design phase 8 rag assistant"
```

## Task 2: Service Scaffold And API Tests

**Files:**
- Create: `ai-services/rag-service/pyproject.toml`
- Create: `ai-services/rag-service/rag_service/__init__.py`
- Create: `ai-services/rag-service/rag_service/app.py`
- Create: `ai-services/rag-service/rag_service/schemas.py`
- Test: `ai-services/rag-service/tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create tests for health, ingest, query with sources, query with missing evidence, and chunk listing.

Run:

```bash
cd ai-services/rag-service
../../.venv/bin/python -m pytest tests/test_api.py -q
```

Expected: fails because `rag_service` does not exist.

- [ ] **Step 2: Implement minimal app and schemas**

Create Pydantic models for ingest, query, source references, chunk responses, and answer responses. Add FastAPI route functions that delegate to a service object.

- [ ] **Step 3: Run API tests**

Run:

```bash
cd ai-services/rag-service
../../.venv/bin/python -m pytest tests/test_api.py -q
```

Expected: API tests pass after service implementation tasks are complete.

- [ ] **Step 4: Commit**

Run:

```bash
git add ai-services/rag-service
git commit -m "feat: scaffold rag assistant service"
```

## Task 3: Chunking, Store, Retrieval, Answering, And Audit

**Files:**
- Create: `ai-services/rag-service/rag_service/chunking.py`
- Create: `ai-services/rag-service/rag_service/store.py`
- Create: `ai-services/rag-service/rag_service/retrieval.py`
- Create: `ai-services/rag-service/rag_service/answering.py`
- Create: `ai-services/rag-service/rag_service/audit.py`
- Create: `ai-services/rag-service/rag_service/service.py`
- Test: `ai-services/rag-service/tests/test_retrieval.py`

- [ ] **Step 1: Write failing retrieval tests**

Create tests that prove:

- chunk IDs are stable;
- top-k limits results;
- collision coverage questions retrieve policy coverage chunks;
- unrelated questions return no sources;
- audit records include retrieved chunk IDs.

Run:

```bash
cd ai-services/rag-service
../../.venv/bin/python -m pytest tests/test_retrieval.py -q
```

Expected: fails because chunking, retrieval, service, and audit do not exist.

- [ ] **Step 2: Implement chunking**

Split text by paragraphs, preserve headings, and assign IDs like `DOC-001-CHUNK-0001`.

- [ ] **Step 3: Implement in-memory store**

Store chunks by document ID and support document-specific chunk listing plus global retrieval candidates.

- [ ] **Step 4: Implement lexical retrieval**

Normalize tokens, remove stopwords, score by overlap, apply top-k, and filter zero-score chunks.

- [ ] **Step 5: Implement answer generation**

If no chunks are retrieved, return the evidence-missing response. Otherwise answer from the top chunk and include all returned sources.

- [ ] **Step 6: Implement audit**

Record claim ID, question, prompt metadata, retrieved chunk IDs, answer, confidence, and human-review flag.

- [ ] **Step 7: Run focused tests**

Run:

```bash
cd ai-services/rag-service
../../.venv/bin/python -m pytest -q
```

Expected: all RAG service tests pass.

- [ ] **Step 8: Commit**

Run:

```bash
git add ai-services/rag-service
git commit -m "feat: add grounded rag assistant"
```

## Task 4: Documentation, Test Script, And Memory

**Files:**
- Create: `docs/api/rag-assistant.md`
- Create: `ai-services/rag-service/README.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `ai-services/README.md`
- Modify: `scripts/run-tests.sh`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Write API docs**

Document ingest, query, chunk listing, evidence-missing behavior, source references, prompt metadata, and safety boundaries.

- [ ] **Step 2: Update README indexes**

Link the RAG assistant docs from the root README, docs index, and AI services README.

- [ ] **Step 3: Update root test script**

Add a test block for `ai-services/rag-service`.

- [ ] **Step 4: Update project memory**

Record implementation progress and verification expectations.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/api/rag-assistant.md ai-services/rag-service/README.md README.md docs/README.md ai-services/README.md scripts/run-tests.sh PROJECT_MEMORY.md
git commit -m "docs: document phase 8 rag assistant"
```

## Task 5: Full Verification And Pull Request

**Files:**
- No source edits expected unless verification finds an issue.

- [ ] **Step 1: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run focused RAG tests**

Run:

```bash
cd ai-services/rag-service
../../.venv/bin/python -m pytest -q
```

Expected: all RAG service tests pass.

- [ ] **Step 3: Run full repository tests**

Run:

```bash
./scripts/run-tests.sh
```

Expected: backend, synthetic generator, triage service, document intelligence service, RAG service, and ML tests pass.

- [ ] **Step 4: Record verification and open PR**

Update `PROJECT_MEMORY.md`, commit, push `rag-adjuster-assistant`, and open a PR into `main`.

## Self-Review Checklist

- Phase 8 remains separate from Phase 7 document extraction.
- Retrieval answers include source references.
- Missing evidence produces a refusal-style answer.
- The implementation remains offline and deterministic.
- Future pgvector integration has a clear boundary.
