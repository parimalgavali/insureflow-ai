# InsureFlow AI Document Intelligence Service

FastAPI service for Phase 7 LLM-style document extraction, missing-document checks, and adjuster-ready claim summaries.

The service runs offline by default with a deterministic local provider. That keeps local demos and tests reliable without OpenAI or Azure OpenAI credentials, while preserving a provider boundary for hosted LLM integration later.

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
python3 -m uvicorn document_intelligence.app:app --reload --port 8002
```

## Endpoints

- `GET /health`
- `GET /ai/v1/documents/health`
- `POST /ai/v1/documents/extract`
- `POST /ai/v1/documents/missing-check`
- `POST /ai/v1/documents/summarize`

The public contract is documented in `../../docs/api/document-intelligence.md`.

## Safety Boundary

Outputs are decision support only. They must not be used for real claim approval, rejection, fraud accusation, legal advice, medical advice, or production insurance decisions.
