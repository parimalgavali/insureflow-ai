#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -d "$ROOT_DIR/backend" ]; then
  (cd "$ROOT_DIR/backend" && mvn test)
fi

if [ -d "$ROOT_DIR/synthetic-data-generator" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi

  (cd "$ROOT_DIR/synthetic-data-generator" && "$PYTHON_BIN" -m pytest)
fi

if [ -d "$ROOT_DIR/ai-services/triage-service" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi

  (cd "$ROOT_DIR/ai-services/triage-service" && "$PYTHON_BIN" -m pytest)
fi

if [ -d "$ROOT_DIR/ai-services/document-intelligence-service" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi

  (cd "$ROOT_DIR/ai-services/document-intelligence-service" && "$PYTHON_BIN" -m pytest)
fi

if [ -d "$ROOT_DIR/ai-services/rag-service" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi

  (cd "$ROOT_DIR/ai-services/rag-service" && "$PYTHON_BIN" -m pytest)
fi

if [ -d "$ROOT_DIR/ml" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi

  (cd "$ROOT_DIR/ml" && "$PYTHON_BIN" -m pytest)
fi
