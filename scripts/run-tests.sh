#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -d "$ROOT_DIR/backend" ]; then
  (cd "$ROOT_DIR/backend" && mvn test)
fi
