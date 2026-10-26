# RAG Assistant API

Phase 8 adds a document-grounded adjuster assistant service under `ai-services/rag-service`. The service ingests claim, policy, guideline, note, or document text; chunks it; retrieves relevant chunks for adjuster questions; and returns answers with source references.

The first implementation is offline and deterministic. It uses in-memory chunk storage and lexical retrieval instead of pgvector and hosted embeddings. The API and metadata are designed so a future phase can replace the local retriever with pgvector and embedding models.

Phase 18 adds a Spring Boot product facade for frontend grounded questions:

```http
POST /api/v1/claims/{claimNumber}/rag-query
```

The Vue app calls this backend facade, not the Python RAG service directly. The facade answers from live claim, coverage, triage, and document context, while preserving the same decision-support boundary and source-reference shape.

## Boundaries

The assistant is decision support only. It must not approve or reject claims, make fraud accusations, provide legal advice, provide medical advice, or replace human adjuster review.

If retrieved evidence is missing or weak, the service says it cannot answer from available evidence.

## Local Run

```bash
cd ai-services/rag-service
python3 -m pip install -e ".[test]"
python3 -m pytest
python3 -m uvicorn rag_service.app:app --reload --port 8003
```

## Health

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "rag-service"
}
```

## Ingest Document

```http
POST /ai/v1/rag/ingest
```

Request:

```json
{
  "documentId": "DOC-POLICY-001",
  "claimId": "CLM-ID-001",
  "policyId": "POL-ID-001",
  "documentType": "POLICY_DOCUMENT",
  "title": "Motor Policy Coverage",
  "text": "Collision Coverage\nCollision damage is covered when the policy is active on the loss date.",
  "metadata": {
    "sourceSystem": "synthetic-demo"
  }
}
```

Response:

```json
{
  "documentId": "DOC-POLICY-001",
  "chunkCount": 1,
  "chunkIds": ["DOC-POLICY-001-CHUNK-0001"]
}
```

## Query Assistant

```http
POST /ai/v1/rag/query
```

## Spring Boot Claim RAG Facade

```http
POST /api/v1/claims/CLM-20260626-000418/rag-query
```

Request:

```json
{
  "question": "Is this collision loss covered?"
}
```

Response:

```json
{
  "claimNumber": "CLM-20260626-000418",
  "question": "Is this collision loss covered?",
  "answer": "Based on the live coverage validation snapshot, this collision loss appears potentially covered when reviewed against the active policy context. Human review is still required before any claim decision.",
  "confidence": "MEDIUM",
  "requiresHumanReview": true,
  "sources": [
    {
      "documentId": "CLAIM-CLM-20260626-000418",
      "chunkId": "CLAIM-CLM-20260626-000418-LIVE-CONTEXT",
      "documentType": "CLAIM_CONTEXT",
      "sectionTitle": "Coverage validation",
      "pageNumber": 1,
      "score": 0.72
    }
  ]
}
```

The Phase 18 facade is deterministic and claim-context based. Future hardening can replace the answer engine with persisted RAG service evidence while keeping this frontend contract stable.

Request:

```json
{
  "claimId": "CLM-ID-001",
  "question": "Is this collision loss covered?",
  "topK": 3
}
```

Response with evidence:

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
      "score": 0.65
    }
  ],
  "confidence": "MEDIUM",
  "requiresHumanReview": true,
  "promptName": "rag_adjuster_assistant",
  "promptVersion": "v1",
  "auditId": "RAG-AUD-..."
}
```

Response without evidence:

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

## List Document Chunks

```http
GET /ai/v1/rag/documents/{documentId}/chunks
```

Response:

```json
{
  "documentId": "DOC-POLICY-001",
  "chunks": [
    {
      "documentId": "DOC-POLICY-001",
      "chunkId": "DOC-POLICY-001-CHUNK-0001",
      "claimId": "CLM-ID-001",
      "policyId": "POL-ID-001",
      "documentType": "POLICY_DOCUMENT",
      "sectionTitle": "Collision Coverage",
      "pageNumber": 1,
      "chunkIndex": 1,
      "textPreview": "Collision Coverage\nCollision damage is covered...",
      "metadata": {
        "sourceSystem": "synthetic-demo"
      }
    }
  ]
}
```

## Chunking And Retrieval

Phase 8 chunking is deterministic:

- split by paragraphs and section headings
- preserve section titles
- assign stable chunk IDs
- default page number to 1

Phase 8 retrieval is lexical:

- lowercase token matching
- stopword filtering
- top-k source limiting
- no external embedding calls

This is intentionally not production-grade retrieval. It proves source-cited RAG behavior before adding pgvector and embeddings.

## Audit

Each query writes an in-memory audit record with:

- claim ID
- question
- prompt name and version
- retrieved chunk IDs
- answer
- confidence
- human-review flag
- timestamp

Future backend integration can persist these records in PostgreSQL.
