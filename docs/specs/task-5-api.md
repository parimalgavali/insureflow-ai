# Task 5 — Backend API

**Goal:** a FastAPI service that persists conversations and claims, streams agent events over SSE, and runs with `docker compose up`.

**Deliverables (`api/`)**
- `main.py` with lifespan: load fraud model, init embeddings, check DB, init provider.
- `db/`: SQLAlchemy 2.x models `Conversation`, `Message`, `Claim`, `Attachment`; Alembic migrations (plus `policy_chunks` from task 3 and LangGraph checkpoint tables).
- `routers/conversations.py`: `POST /api/conversations`, `GET /api/conversations/{id}`, `POST /api/conversations/{id}/messages` → `text/event-stream` with typed events `token | facts | question | citations | risk | card | done | error`.
- `routers/claims.py`: `POST /api/claims/{id}/review` (accept / edit facts / request more info) → resumes the graph; `GET /api/claims/{id}`.
- `routers/health.py`: db, model artifact, provider reachability.
- Uploads: `POST .../messages` accepts multipart with optional image/PDF; stored on disk under `data/uploads/` (volume), metadata in `Attachment`; the agent only receives the filename + type in v2 (content understanding is task 8).
- Auth: single bearer token from `DEMO_API_TOKEN`; CORS for the web dev server.
- `docker-compose.yml`: `db` (pgvector image), `api`; `web` is added in task 6. `.env.example`.
- CI (`.github/workflows/ci.yml`): ruff, mypy (loose), pytest for `api/ ml/ rag/` with a Postgres service; builds the api image.

**Tests:** router tests with `RecordedProvider`; SSE event order; review resume; migration up/down; health endpoint.

**Done when:** `docker compose up -d db api && curl` can create a conversation, stream a reply, and resume after review; CI green.

**Risks:** SSE through nginx (task 6) needs `proxy_buffering off`; LangGraph checkpoint tables must be created by Alembic, not at import time.
