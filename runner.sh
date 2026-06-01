#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ARTE_LOG="$HERE/ARTE_OPENCLAW.md"
HEARTBEAT="$HERE/.worktrees/openclaw/heartbeat.py"
SPOOL_DIR="$HOME/.openclaw/telegram/ingress-spool-default"
INTERVAL=600  # 10 min
TIMEOUT=300   # 5 min por pipeline
CYCLE=0

MODES=(
  "--mode cache --auto"
  "--solo-banner --auto"
  "--solo-gif --auto"
  "--solo-reel --auto"
)

cleanup() {
  echo "[runner] SIG recibido — cerrando..."
  log_cycle "SHUTDOWN" "interrumpido por señal"
  exit 0
}
trap cleanup SIGINT SIGTERM

clean_spool() {
  local removed
  removed="$(find "$SPOOL_DIR" -name '*.json' -mmin +2 2>/dev/null | wc -l)"
  if [ "$removed" -gt 0 ]; then
    find "$SPOOL_DIR" -name '*.json' -mmin +2 -delete 2>/dev/null
    echo "[runner] spool: $removed archivo(s) estancado(s) eliminado(s)"
  fi
}

log_cycle() {
  local result="$1" obs="$2"
  local ts; ts="$(date '+%H:%M')"
  local entry
  entry="| $CYCLE | $ts | $MODE_ACTUAL | $result | $obs |"
  if [ -f "$ARTE_LOG" ]; then
    # insert after the marker comment
    sed -i "/<!-- runner-insert -->/a\\$entry" "$ARTE_LOG"
  else
    echo "$entry" >> "$ARTE_LOG"
  fi
  echo "[runner] log: $entry"
}

do_heartbeat() {
  if [ -f "$HEARTBEAT" ]; then
    python "$HEARTBEAT" --beat openclaw "runner ciclo $CYCLE" 2>/dev/null || true
  fi
}

run_pipeline() {
  local mode="$1"
  echo "[runner] ciclo $CYCLE — ejecutando: pipeline.py $mode"
  # shellcheck disable=SC2086
  timeout "$TIMEOUT" python "$HERE/pipeline.py" $mode 2>&1
  local rc=$?
  if [ $rc -eq 124 ]; then
    log_cycle "TIMEOUT ❌" "excedio ${TIMEOUT}s"
    return 1
  elif [ $rc -ne 0 ]; then
    log_cycle "ERROR ❌" "codigo $rc"
    return 1
  else
    log_cycle "COMPLETADO ✅" "ok"
    return 0
  fi
}

echo "[runner] ===== INICIO ====="
echo "[runner] intervalo: ${INTERVAL}s | timeout: ${TIMEOUT}s | modos: ${#MODES[@]}"

while true; do
  CYCLE=$((CYCLE + 1))
  IDX=$(( (CYCLE - 1) % ${#MODES[@]} ))
  MODE_ACTUAL="${MODES[$IDX]}"

  clean_spool
  run_pipeline "$MODE_ACTUAL" || true
  do_heartbeat

  echo "[runner] esperando ${INTERVAL}s hasta el ciclo $((CYCLE + 1))..."
  sleep "$INTERVAL"
done
