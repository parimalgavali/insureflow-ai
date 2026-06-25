# InsureFlow AI RAG Service

FastAPI service for Phase 8 document-grounded adjuster assistance.

The service runs offline by default with deterministic chunking, in-memory chunk storage, lexical retrieval, grounded answer generation, source references, and in-memory audit. This keeps local demos and tests reliable without embedding services, pgvector, or hosted LLM credentials.

## Local Setup

Install runtime and test dependencies in a Python 3.12+ environment:

```bash
python3 -m pip install -e ".[test]"
```

Run tests:

```bash
python3 -m pytest
```

Run the development server:

```bash
python3 -m uvicorn rag_service.app:app --reload --port 8003
```

## Endpoints

- `GET /health`
- `POST /ai/v1/rag/ingest`
- `POST /ai/v1/rag/query`
- `GET /ai/v1/rag/documents/{documentId}/chunks`

The public contract is documented in `../../docs/api/rag-assistant.md`.

## Safety Boundary

Answers are grounded decision support only. The assistant must cite sources, say when evidence is missing, avoid legal certainty, avoid final claim approval or rejection, and recommend human review.
