#!/usr/bin/env bash
# test_combinations.sh — Bateria de combinaciones ARTE
# bash test_combinations.sh
DIR="$(cd "$(dirname "$0")" && pwd)"
PASS=0; FAIL=0; R=()

ok()  { ((PASS++)); R+=("✅ $1"); echo "  ✅ $1"; }
nok() { ((FAIL++)); R+=("❌ $1 — $2"); echo "  ❌ $1"; }

test_api() {
  local model=$1 label=$2
  local f=/data/data/com.termux/files/usr/tmp/opencode/tc.json
  curl -s --max-time 20 -w "\n%{http_code}" "https://opencode.ai/zen/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer sk-Acdgb0kW8l0FzBdNPVd1u3XSLEo521fp3x5r856B0ck2rNN6LxWqYNVOAHIIOw3p" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hello in one word\"}],\"max_tokens\":200}" > "$f" 2>/dev/null
  local code=$(tail -1 "$f")
  local c=$(grep -o '"content":"[^"]*"' "$f" | head -1 | cut -d'"' -f4)
  if [ "$code" = "200" ] && [ -n "$c" ]; then ok "$label → \"$c\""; else nok "$label" "code=$code content=$c"; fi
}

echo "━━━ API DIRECTA ━━━"
test_api "big-pickle" "big-pickle"
test_api "nemotron-3-super-free" "nemotron"

echo "━━━ A2UI ━━━"
if [ -f "$DIR/a2ui_preview.html" ]; then
  cd "$DIR"
  python3 -m http.server 8000 >/dev/null 2>&1 & PID=$!
  sleep 2
  code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/a2ui_preview.html 2>/dev/null || echo "000")
  kill $PID 2>/dev/null
  [ "$code" = "200" ] && ok "A2UI HTTP $code" || nok "A2UI" "HTTP $code"
fi

echo "━━━ PIPELINE ━━━"
[ -f "$DIR/pipeline.py" ] && ok "pipeline.py presente" || nok "pipeline.py" "no encontrado"

echo ""
echo "✅ $PASS  ❌ $FAIL"
[ "$FAIL" -eq 0 ]
