#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
PY="$ROOT/.venv/bin/python"

if [ ! -x "$PY" ]; then
  PY="python3"
fi

"$PY" "$DIR/voice_demo.py" \
  --session client_demo \
  --output "$DIR/client_demo_es.mp3" \
  --caption "Demo CRM en español" \
  --send
