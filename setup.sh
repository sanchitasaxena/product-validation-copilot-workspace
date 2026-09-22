#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
VENV="$ROOT/.venv"

"$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"
if ! command -v officecli >/dev/null 2>&1; then
  echo "Warning: officecli is not installed; DOCX intake and Office editing will remain unavailable." >&2
  echo "Install it from https://officecli.ai/ before using DOCX workflows." >&2
fi
echo "Product Validation Copilot Workspace dependencies are installed in $VENV."
echo "Use .venv/bin/python for workflow commands, or run: source .venv/bin/activate"
