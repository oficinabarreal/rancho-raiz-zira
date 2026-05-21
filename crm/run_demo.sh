#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" -m crm.cli \
  --lead-name "${CRM_DEMO_NAME:-Cliente demo}" \
  --arrival-date "${CRM_DEMO_ARRIVAL:-2026-06-01}" \
  --departure-date "${CRM_DEMO_DEPARTURE:-2026-06-05}" \
  --guests "${CRM_DEMO_GUESTS:-3}" \
  --brief
