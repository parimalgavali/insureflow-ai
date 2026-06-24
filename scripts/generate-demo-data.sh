#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  PYTHON_BIN="$(command -v python)"
fi

cd "$ROOT_DIR/synthetic-data-generator"
"$PYTHON_BIN" -m generator --customers 500 --policies 650 --claims 200 --adjusters 25 --seed 42 --output-dir ../data/synthetic
