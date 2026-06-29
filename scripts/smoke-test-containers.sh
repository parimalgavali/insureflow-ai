#!/usr/bin/env bash
set -euo pipefail

API_PORT="${API_PORT:-8080}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
TRIAGE_SERVICE_PORT="${TRIAGE_SERVICE_PORT:-8001}"
DOCUMENT_INTELLIGENCE_SERVICE_PORT="${DOCUMENT_INTELLIGENCE_SERVICE_PORT:-8002}"
RAG_SERVICE_PORT="${RAG_SERVICE_PORT:-8003}"

check() {
  local name="$1"
  local url="$2"
  local attempts="${SMOKE_TEST_ATTEMPTS:-30}"
  local delay_seconds="${SMOKE_TEST_DELAY_SECONDS:-2}"

  echo "Checking ${name}: ${url}"
  for attempt in $(seq 1 "$attempts"); do
    if curl --fail --silent --show-error "$url" >/dev/null; then
      return 0
    fi
    if [ "$attempt" -lt "$attempts" ]; then
      sleep "$delay_seconds"
    fi
  done

  echo "Smoke check failed for ${name} after ${attempts} attempts." >&2
  return 1
}

check "backend api" "http://localhost:${API_PORT}/api/v1/health"
check "triage service" "http://localhost:${TRIAGE_SERVICE_PORT}/health"
check "document intelligence service" "http://localhost:${DOCUMENT_INTELLIGENCE_SERVICE_PORT}/health"
check "rag service" "http://localhost:${RAG_SERVICE_PORT}/health"
check "frontend" "http://localhost:${FRONTEND_PORT}/"

echo "Container smoke checks passed."
