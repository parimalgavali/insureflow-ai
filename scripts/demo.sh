#!/usr/bin/env bash
# One-command demo: data → AKB ingest → fraud model → docker compose up.
# Needs: uv, docker compose. Optional: ANTHROPIC_API_KEY (else recorded replies), Kaggle creds (else committed model).
set -euo pipefail
cd "$(dirname "$0")/.."

[ -f .env ] || cp .env.example .env
if [ -n "${ANTHROPIC_API_KEY:-}" ] && ! grep -q '^LLM_PROVIDER=anthropic' .env; then
  sed -i.bak 's/^LLM_PROVIDER=.*/LLM_PROVIDER=anthropic/' .env && rm -f .env.bak
  grep -q '^ANTHROPIC_API_KEY=' .env || echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" >> .env
fi

echo "▸ python deps";            uv sync --all-extras -q
echo "▸ public data (cached)";   uv run python scripts/fetch_data.py akb openml seed
if [ -n "${KAGGLE_KEY:-}" ] || [ -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "▸ Kaggle fraud data + retrain"; uv run python scripts/fetch_data.py kaggle && uv run python -m ml.train --no-cv
else
  echo "▸ no Kaggle credentials → using committed ml/artifacts/fraud_model.joblib"
fi
echo "▸ containers (db + api + web)"; docker compose up --build -d
echo "▸ waiting for API";       until curl -fs localhost:8000/api/health >/dev/null; do sleep 2; done
echo "▸ AKB → pgvector";        docker compose exec -T api uv run python -m rag.ingest
echo
echo "ClaimPilot is up: http://localhost:8080  (API: http://localhost:8000/docs)"
echo "Stop with: docker compose down"
