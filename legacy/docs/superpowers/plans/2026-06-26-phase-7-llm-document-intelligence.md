# Phase 7 LLM Document Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a document intelligence FastAPI service that extracts claim/document fields, generates adjuster summaries, detects missing documents, validates LLM-style JSON, retries invalid output once, and audits prompts/responses.

**Architecture:** Add a new Python FastAPI service under `ai-services/document-intelligence-service`. The service uses Pydantic API schemas, a prompt registry, a deterministic local provider that emits JSON strings, a service layer that validates/retries responses, and an in-memory audit store. This keeps Phase 7 offline and testable while preserving a provider boundary for future OpenAI/Azure OpenAI integration.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pytest, httpx, uvicorn.

---

## File Structure

- Create `ai-services/document-intelligence-service/pyproject.toml`
  Defines package metadata and test dependencies.
- Create `ai-services/document-intelligence-service/README.md`
  Explains local run commands, endpoints, offline provider, and limitations.
- Create `ai-services/document-intelligence-service/document_intelligence/__init__.py`
  Package marker.
- Create `ai-services/document-intelligence-service/document_intelligence/schemas.py`
  Pydantic request/response models, enums, and extraction schemas.
- Create `ai-services/document-intelligence-service/document_intelligence/prompts.py`
  Prompt template registry and prompt rendering.
- Create `ai-services/document-intelligence-service/document_intelligence/audit.py`
  In-memory audit store and audit record model.
- Create `ai-services/document-intelligence-service/document_intelligence/provider.py`
  Provider protocol, deterministic provider, and test providers.
- Create `ai-services/document-intelligence-service/document_intelligence/service.py`
  Extraction, missing-check, summary, validation, retry, and audit orchestration.
- Create `ai-services/document-intelligence-service/document_intelligence/app.py`
  FastAPI app and route handlers.
- Create `ai-services/document-intelligence-service/tests/test_api.py`
  API contract tests.
- Create `ai-services/document-intelligence-service/tests/test_service.py`
  Service-layer retry and audit tests.
- Modify `scripts/run-tests.sh`
  Include document intelligence service tests.
- Create `docs/api/document-intelligence.md`
  Public API contract and examples.
- Modify `README.md`, `docs/README.md`, `ai-services/README.md`, and `PROJECT_MEMORY.md`
  Link docs and record Phase 7 progress.

## Task 1: Documentation Foundation

**Files:**
- Create: `docs/superpowers/specs/2026-06-26-phase-7-llm-document-intelligence-design.md`
- Create: `docs/superpowers/plans/2026-06-26-phase-7-llm-document-intelligence.md`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Confirm branch**

Run: `git status --short --branch`

Expected: branch is `llm-document-intelligence` with no unrelated changes.

- [ ] **Step 2: Write design and plan docs**

Create the design and plan documents with the architecture, API contract, prompt registry, audit behavior, test strategy, and done criteria.

- [ ] **Step 3: Update project memory**

Add a row:

```markdown
| 2026-06-26 | Started Phase 7 LLM document intelligence. | Branch `llm-document-intelligence`; design and implementation plan created for the document intelligence FastAPI service. |
```

- [ ] **Step 4: Commit documentation**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-phase-7-llm-document-intelligence-design.md docs/superpowers/plans/2026-06-26-phase-7-llm-document-intelligence.md PROJECT_MEMORY.md
git commit -m "docs: design phase 7 document intelligence"
```

## Task 2: Service Scaffold And API Tests

**Files:**
- Create: `ai-services/document-intelligence-service/pyproject.toml`
- Create: `ai-services/document-intelligence-service/document_intelligence/__init__.py`
- Create: `ai-services/document-intelligence-service/document_intelligence/app.py`
- Create: `ai-services/document-intelligence-service/document_intelligence/schemas.py`
- Create: `ai-services/document-intelligence-service/tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/test_api.py` with tests for `/health`, `/ai/v1/documents/health`, and the shape of extract/missing-check/summarize responses.

Run:

```bash
cd ai-services/document-intelligence-service
../../.venv/bin/python -m pytest tests/test_api.py -q
```

Expected: fails because the service package does not exist.

- [ ] **Step 2: Add minimal service scaffold**

Create `pyproject.toml`, package marker, basic schemas, and app routes. Initial route handlers may return deterministic placeholder values only if they satisfy the tests.

- [ ] **Step 3: Run API tests**

Run:

```bash
cd ai-services/document-intelligence-service
../../.venv/bin/python -m pytest tests/test_api.py -q
```

Expected: health and API shape tests pass.

- [ ] **Step 4: Commit**

Run:

```bash
git add ai-services/document-intelligence-service
git commit -m "feat: scaffold document intelligence service"
```

## Task 3: Prompt Registry, Provider, Validation, Retry, And Audit

**Files:**
- Create: `ai-services/document-intelligence-service/document_intelligence/prompts.py`
- Create: `ai-services/document-intelligence-service/document_intelligence/audit.py`
- Create: `ai-services/document-intelligence-service/document_intelligence/provider.py`
- Create: `ai-services/document-intelligence-service/document_intelligence/service.py`
- Modify: `ai-services/document-intelligence-service/document_intelligence/app.py`
- Test: `ai-services/document-intelligence-service/tests/test_service.py`

- [ ] **Step 1: Write failing service tests**

Create tests that prove:

- invalid JSON retries once and then succeeds;
- invalid JSON after both attempts raises a validation failure;
- audit records contain prompt name, version, raw response, parsed output, and validation status.

Run:

```bash
cd ai-services/document-intelligence-service
../../.venv/bin/python -m pytest tests/test_service.py -q
```

Expected: fails because registry, provider, service, and audit do not exist.

- [ ] **Step 2: Implement prompt registry**

Add prompt templates for:

- `claim_description_extraction` `v1`
- `repair_invoice_extraction` `v1`
- `missing_documents` `v1`
- `claim_summary` `v1`

- [ ] **Step 3: Implement provider and audit**

Add a provider protocol that returns JSON strings, a deterministic local provider, and an in-memory audit store.

- [ ] **Step 4: Implement service retry**

In the service layer, parse provider JSON into the correct Pydantic schema, retry once on parsing or validation failure, and audit both success and failure.

- [ ] **Step 5: Run service tests**

Run:

```bash
cd ai-services/document-intelligence-service
../../.venv/bin/python -m pytest tests/test_service.py -q
```

Expected: retry and audit tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add ai-services/document-intelligence-service
git commit -m "feat: add document prompt validation and audit"
```

## Task 4: Realistic Deterministic Extraction And Summaries

**Files:**
- Modify: `ai-services/document-intelligence-service/document_intelligence/provider.py`
- Modify: `ai-services/document-intelligence-service/document_intelligence/service.py`
- Modify: `ai-services/document-intelligence-service/tests/test_api.py`
- Modify: `ai-services/document-intelligence-service/tests/test_service.py`

- [ ] **Step 1: Write failing behavior tests**

Add tests proving:

- claim text with rear bumper, hit-and-run, no police report, photos, and `4500 EUR` extracts expected fields;
- repair invoice text extracts invoice number, shop, labor, parts, tax, total, and currency;
- missing-check returns `POLICE_REPORT` and `REPAIR_ESTIMATE` for third-party motor claims missing those documents;
- summary contains the nine required sections and human review warning.

Run:

```bash
cd ai-services/document-intelligence-service
../../.venv/bin/python -m pytest -q
```

Expected: fails because deterministic extraction is incomplete.

- [ ] **Step 2: Implement deterministic extraction**

Use simple text normalization and regular expressions in the deterministic provider. Keep the provider conservative and easy to replace with a hosted LLM later.

- [ ] **Step 3: Run document intelligence tests**

Run:

```bash
cd ai-services/document-intelligence-service
../../.venv/bin/python -m pytest -q
```

Expected: all document intelligence tests pass.

- [ ] **Step 4: Commit**

Run:

```bash
git add ai-services/document-intelligence-service
git commit -m "feat: extract and summarize claim documents"
```

## Task 5: Documentation, Test Script, And Memory

**Files:**
- Create: `docs/api/document-intelligence.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `ai-services/README.md`
- Modify: `scripts/run-tests.sh`
- Modify: `PROJECT_MEMORY.md`

- [ ] **Step 1: Write API documentation**

Document endpoints, examples, prompt versions, local deterministic provider behavior, audit fields, and safety boundaries.

- [ ] **Step 2: Update indexes**

Add document intelligence links to the root README, docs index, and AI services README.

- [ ] **Step 3: Update test script**

Add:

```bash
if [ -d "$ROOT_DIR/ai-services/document-intelligence-service" ]; then
  # choose PYTHON_BIN the same way as other Python services
  (cd "$ROOT_DIR/ai-services/document-intelligence-service" && "$PYTHON_BIN" -m pytest)
fi
```

- [ ] **Step 4: Update project memory**

Record Phase 7 implementation and verification expectations.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/api/document-intelligence.md README.md docs/README.md ai-services/README.md scripts/run-tests.sh PROJECT_MEMORY.md
git commit -m "docs: document phase 7 document intelligence"
```

## Task 6: Full Verification And Pull Request

**Files:**
- No source edits expected unless verification finds an issue.

- [ ] **Step 1: Run formatting/whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run focused service tests**

Run:

```bash
cd ai-services/document-intelligence-service
../../.venv/bin/python -m pytest -q
```

Expected: all document intelligence tests pass.

- [ ] **Step 3: Run full repository tests**

Run:

```bash
./scripts/run-tests.sh
```

Expected: backend, synthetic generator, triage service, document intelligence service, and ML tests pass.

- [ ] **Step 4: Record verification**

Update `PROJECT_MEMORY.md` with the final command results and commit:

```bash
git add PROJECT_MEMORY.md
git commit -m "docs: record phase 7 verification"
```

- [ ] **Step 5: Push and open PR**

Run:

```bash
git push -u origin llm-document-intelligence
gh pr create --base main --head llm-document-intelligence --title "Phase 7: LLM document intelligence" --body "<summary and validation>"
```

Expected: PR opens against `main`.

## Self-Review Checklist

- The plan keeps Phase 7 separate from Phase 8 RAG.
- The service can run without API keys.
- Prompt versioning and raw-response audit are included.
- Invalid JSON retry is included.
- Tests are written before implementation.
- Root verification includes the new service.
