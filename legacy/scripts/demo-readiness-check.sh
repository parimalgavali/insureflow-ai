#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

required_files=(
  "README.md"
  "docs/README.md"
  "docs/demo/demo-script.md"
  "docs/demo/recruiter-walkthrough.md"
  "docs/frontend/adjuster-workbench.md"
  "docs/product/dynamic-claims-application-roadmap.md"
  "docs/ai/responsible-ai-statement.md"
  "frontend/package.json"
  "docker-compose.yml"
)

echo "Checking demo documentation and app assets..."
for relative_path in "${required_files[@]}"; do
  if [ ! -f "$ROOT_DIR/$relative_path" ]; then
    echo "Missing required demo asset: $relative_path" >&2
    exit 1
  fi
done

echo "Running frontend smoke tests and production build..."
(cd "$ROOT_DIR/frontend" && npm test -- --run && npm run build)

cat <<'MESSAGE'
Demo readiness checks passed.

Optional container validation:
  docker compose --profile app up --build
  ./scripts/smoke-test-containers.sh

Optional full quality validation:
  ./scripts/run-tests.sh
  ./scripts/run-quality-gates.sh
MESSAGE
