#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$DIR/zira_service.log"
ROOT="$(cd "$DIR/.." && pwd)"
PY="$ROOT/.venv/bin/python"

if [ ! -x "$PY" ]; then
  PY="python3"
fi

while true; do
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] starting zira bot" >> "$LOG"
  "$PY" "$DIR/zira_bot.py" >> "$LOG" 2>&1 || true
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] zira bot exited, restarting in 2s" >> "$LOG"
  sleep 2
done
