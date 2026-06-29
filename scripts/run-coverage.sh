#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COVERAGE_DIR="$ROOT_DIR/coverage"
PYTHON_BIN="${PYTHON_BIN:-}"

if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi
fi

mkdir -p "$COVERAGE_DIR/python"

run_python_coverage() {
  local project_dir="$1"
  local package_name="$2"
  local report_name="$3"
  local extra_name="$4"

  if [ -d "$ROOT_DIR/$project_dir" ]; then
    echo "Running Python coverage for $project_dir"
    (
      cd "$ROOT_DIR/$project_dir"
      "$PYTHON_BIN" -m pip install -q -e ".[$extra_name]"
      "$PYTHON_BIN" -m pytest \
        --cov="$package_name" \
        --cov-report=term-missing \
        --cov-report=xml:"$COVERAGE_DIR/python/$report_name.xml"
    )
  fi
}

if [ -d "$ROOT_DIR/backend" ]; then
  echo "Running backend JaCoCo coverage"
  (cd "$ROOT_DIR/backend" && mvn clean -Pcoverage verify)
fi

run_python_coverage "synthetic-data-generator" "generator" "synthetic-data-generator" "dev"
run_python_coverage "ai-services/triage-service" "triage_service" "triage-service" "test"
run_python_coverage "ai-services/document-intelligence-service" "document_intelligence" "document-intelligence-service" "test"
run_python_coverage "ai-services/rag-service" "rag_service" "rag-service" "test"
run_python_coverage "ml" "insureflow_ml" "ml" "test"

if [ -f "$ROOT_DIR/frontend/package.json" ]; then
  echo "Running frontend coverage"
  (cd "$ROOT_DIR/frontend" && npm run coverage)
fi

echo "Coverage reports generated under $COVERAGE_DIR and package target directories."
