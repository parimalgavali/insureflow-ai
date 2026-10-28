#!/usr/bin/env sh
# Migrate, make sure the AKB corpus is in pgvector (idempotent — skips chunks already stored), serve.
set -eu
cd /app
alembic upgrade head
python scripts/fetch_data.py akb >/dev/null 2>&1 || echo "AKB fetch failed; retrieval will use whatever is already ingested"
python -m rag.ingest || echo "ingest skipped"
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-7860}"
