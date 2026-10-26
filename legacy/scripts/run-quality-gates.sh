#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

./scripts/run-tests.sh
./scripts/run-coverage.sh
docker compose --profile app --profile observability config >/dev/null
bash -n scripts/smoke-test-containers.sh
bash -n scripts/load-smoke-test.sh
git diff --check

if command -v trivy >/dev/null 2>&1; then
  trivy fs --severity HIGH,CRITICAL --exit-code 1 --scanners vuln,secret,misconfig .
else
  echo "trivy not installed; skipping local Trivy scan."
fi

if [ -f frontend/package.json ]; then
  (cd frontend && npm audit --audit-level=high)
fi

echo "Quality gates passed."
