# Phase 8 RAG Adjuster Assistant Design

## Context

Phase 8 adds a document-grounded adjuster assistant. Phase 7 can extract and summarize claim documents, but it does not answer adjuster questions over claim, policy, note, guideline, or document evidence. Phase 8 fills that gap with a retrieval-augmented generation service that returns answers with source references and refuses to invent evidence.

The initial implementation will be a separate FastAPI service under `ai-services/rag-service`. It will run fully offline using deterministic chunking, lexical retrieval, and grounded answer generation. This keeps the portfolio project runnable without embedding model credentials, pgvector setup, or external LLM keys. The API, metadata, and storage boundary will remain compatible with future pgvector and hosted embedding/LLM providers.

## Recommended Approach

I considered three approaches:

1. **pgvector and embeddings first:** enable pgvector, generate embeddings, and persist chunks in PostgreSQL.
   This is closest to production RAG, but the local PostgreSQL image does not currently include pgvector and would add environment fragility before the user-facing behavior is proven.

2. **Offline RAG first with pgvector-ready metadata:** implement ingestion, chunking, retrieval, grounded answering, source citations, and evidence-missing behavior using an in-memory store and deterministic lexical scoring.
   This is the recommended Phase 8 approach. It demonstrates RAG behavior clearly, runs in CI/local environments, and keeps the future vector-store boundary clean.

3. **Fold RAG into the Phase 7 document intelligence service:** reuse the existing service and add `/rag/*` endpoints there.
   This reduces one service directory, but it blurs the boundary between document extraction and retrieval/Q&A.

Phase 8 will use option 2.

## Scope

Phase 8 includes:

- A new FastAPI RAG service.
- Health endpoint.
- Document ingestion endpoint.
- Chunking with stable chunk IDs and metadata.
- In-memory chunk store.
- Deterministic lexical retriever with top-k support.
- Grounded answer generation with source references.
- Evidence-missing response when retrieved context is weak or absent.
- Prompt/version metadata for answer generation.
- In-memory RAG interaction audit.
- API documentation and README.
- Root test script integration.

Phase 8 does not include:

- Real embeddings or vector database persistence.
- pgvector extension installation.
- RAG over live backend database rows.
- Frontend chat UI.
- Hosted LLM calls.
- Long-term audit persistence.

## Service Boundaries

The RAG service owns retrieval and grounded answer behavior:

- It receives documents or text snippets to ingest.
- It chunks text and stores chunk metadata.
- It retrieves relevant chunks for a question.
- It answers only from retrieved evidence.
- It returns source references.
- It records the interaction in an in-memory audit store.

The document intelligence service remains responsible for extraction and summaries. The Spring Boot backend remains the system of record and can later call this service after claim/policy/document data is assembled.

## API Contract

### `GET /health`

```json
{
  "status": "ok",
  "service": "rag-service"
}
```

### `POST /ai/v1/rag/ingest`

Request:

```json
{
  "documentId": "DOC-POLICY-001",
  "claimId": "CLM-ID-001",
  "policyId": "POL-ID-001",
  "documentType": "POLICY_DOCUMENT",
  "title": "Motor Policy Coverage",
  "text": "Collision Coverage\nCollision damage is covered when the policy is active on the loss date...",
  "metadata": {
    "sourceSystem": "synthetic-demo"
  }
}
```

Response:

```json
{
  "documentId": "DOC-POLICY-001",
  "chunkCount": 2,
  "chunkIds": ["DOC-POLICY-001-CHUNK-0001", "DOC-POLICY-001-CHUNK-0002"]
}
```

### `POST /ai/v1/rag/query`

Request:

```json
{
  "claimId": "CLM-ID-001",
  "question": "Is this collision loss covered?",
  "topK": 3
}
```

Response when evidence is available:

```json
{
  "answer": "Based on the retrieved policy coverage section, collision damage appears potentially covered when the policy was active on the loss date. Human review is required before any claim decision.",
  "sources": [
    {
      "documentId": "DOC-POLICY-001",
      "chunkId": "DOC-POLICY-001-CHUNK-0001",
      "documentType": "POLICY_DOCUMENT",
      "sectionTitle": "Collision Coverage",
      "pageNumber": 1,
      "score": 0.42
    }
  ],
  "confidence": "MEDIUM",
  "requiresHumanReview": true,
  "promptName": "rag_adjuster_assistant",
  "promptVersion": "v1",
  "auditId": "RAG-AUD-..."
}
```

Response when evidence is missing:

```json
{
  "answer": "I do not have enough retrieved evidence to answer this question. Please add policy, claim, guideline, or document evidence and have an adjuster review the file.",
  "sources": [],
  "confidence": "LOW",
  "requiresHumanReview": true,
  "promptName": "rag_adjuster_assistant",
  "promptVersion": "v1",
  "auditId": "RAG-AUD-..."
}
```

### `GET /ai/v1/rag/documents/{documentId}/chunks`

Returns stored chunks for one document, including chunk IDs, section titles, page numbers, text previews, and metadata.

## Chunking

Phase 8 will use a simple deterministic chunker:

- Split text by paragraphs and headings.
- Preserve the closest heading as `sectionTitle`.
- Keep chunks below a conservative word limit.
- Assign stable IDs as `{documentId}-CHUNK-0001`.
- Default `pageNumber` to 1 unless provided later.

This is intentionally simple, because realistic PDF parsing and page-aware extraction are separate concerns from RAG behavior.

## Retrieval

The first retriever is lexical:

- Normalize text to lowercase tokens.
- Remove common stopwords.
- Score chunks by question-token overlap.
- Add small boosts for document type and exact phrase matches such as `coverage`, `missing`, `risk`, `timeline`, and `exclusion`.
- Return top-k chunks above a minimum score.

This is not a production embedding model. It is an offline, deterministic stand-in that proves API shape, evidence selection, source citation, and hallucination safety.

## Answer Rules

The assistant must:

- Answer only from retrieved chunks.
- Cite source chunks.
- Say when evidence is missing.
- Avoid final claim approval or rejection.
- Avoid legal certainty.
- Avoid fraud accusations.
- Recommend human review for ambiguity, high risk, missing evidence, or coverage questions.
- Keep answers short enough for an adjuster workflow.

## Audit

Phase 8 audit is in-memory and process-local. Each record includes:

- `auditId`
- `claimId`
- `question`
- `promptName`
- `promptVersion`
- `retrievedChunkIds`
- `answer`
- `confidence`
- `requiresHumanReview`
- `createdAt`

Future backend integration can persist this data in PostgreSQL.

## Testing Strategy

Tests will cover:

- Health endpoint.
- Ingest creates stable chunk IDs.
- Chunk listing returns stored chunks.
- Query over ingested policy text returns a grounded answer with sources.
- Query with no relevant evidence returns an evidence-missing answer with no sources.
- Top-k limits returned sources.
- Audit records include the question, answer, prompt version, and retrieved chunk IDs.
- Root `scripts/run-tests.sh` includes the RAG service suite.

## Documentation Updates

Phase 8 will add:

- `docs/api/rag-assistant.md`
- `ai-services/rag-service/README.md`
- Links from the root README, docs index, and AI services README.
- Project memory updates for start, implementation, verification, and PR.

## Done Criteria

Phase 8 is done when:

- Design and implementation plan are committed.
- RAG service supports ingestion, chunk listing, query, source citation, evidence-missing behavior, and audit.
- Focused RAG tests pass.
- Full repository test script passes.
- Documentation and project memory are updated.
- A pull request is opened from `rag-adjuster-assistant` into `main`.
