#!/usr/bin/env bash
# automejora.sh — Pipeline de Automejora Autónoma v2
# Uso:
#   ./scripts/automejora.sh "mensaje del cambio"         # push + monitor + merge/discard
#   ./scripts/automejora.sh --status                      # ver estado del último run
#   ./scripts/automejora.sh --help                        # esta ayuda
#
# Requiere: git, curl, termux-notification (opcional)
# Variables de entorno: GITHUB_TOKEN (o git credential store)
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

BRANCH_PREFIX="test-automejora"
TIMESTAMP=$(date +%s)
BRANCH="${BRANCH_PREFIX}-${TIMESTAMP}"
GH_REPO="oficinabarreal/hola-3-crm"
POLL_INTERVAL=15  # segundos entre consultas a GH Actions
MAX_POLLS=40      # max 10 minutos de espera

# ─── Colores ──────────────────────────────────────────────────────
VERDE='\033[0;32m'; ROJO='\033[0;31m'; AMAR='\033[1;33m'; CYA='\033[0;36m'; RESET='\033[0m'
ok()  { echo -e "  ${VERDE}✅${RESET} $1"; }
nok() { echo -e "  ${ROJO}❌${RESET} $1"; }
info(){ echo -e "  ${CYA}ℹ️${RESET} $1"; }
warn(){ echo -e "  ${AMAR}⚠️${RESET} $1"; }

# ─── Help ──────────────────────────────────────────────────────────
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "automejora.sh — Pipeline de Automejora Autónoma v2"
    echo ""
    echo "  Uso: ./scripts/automejora.sh [mensaje] [--dry-run]"
    echo "       ./scripts/automejora.sh --status"
    echo ""
    echo "  Flujo:"
    echo "    1. Crea rama test-automejora-<timestamp>"
    echo "    2. Commit + push del cambio actual"
    echo "    3. Monitorea GitHub Actions hasta completar"
    echo "    4. Success → merge a main + notify"
    echo "    5. Failure → descarta rama + notify error"
    echo ""
    echo "  --dry-run  muestra los pasos sin ejecutarlos"
    exit 0
fi

# ─── Obtener token ─────────────────────────────────────────────────
get_token() {
    # Intentar variable de entorno primero
    if [ -n "${GITHUB_TOKEN:-}" ]; then
        echo "$GITHUB_TOKEN"
        return
    fi
    # Intentar git credential store
    local tok
    tok=$(echo "protocol=https
host=github.com" | git credential-store get 2>/dev/null | grep password | cut -d= -f2)
    if [ -n "$tok" ]; then
        echo "$tok"
        return
    fi
    # Fallback: leer .git-credentials
    if [ -f ~/.git-credentials ]; then
        tok=$(grep -oP 'https://[^:]+:\K[^@]+' ~/.git-credentials 2>/dev/null || true)
        if [ -n "$tok" ]; then
            echo "$tok"
            return
        fi
    fi
    echo ""
}

notify() {
    local title="$1" msg="$2" priority="${3:-normal}"
    if command -v termux-notification &>/dev/null; then
        termux-notification \
            --title "$title" \
            --content "$msg" \
            --priority "$priority" \
            --id "automejora" \
            --alert-once \
            2>/dev/null || true
    fi
    echo ""
    echo -e "  ${CYA}📱${RESET} $title"
    echo -e "     $msg"
}

# ─── STATUS ─────────────────────────────────────────────────────────
if [ "${1:-}" = "--status" ]; then
    TOKEN=$(get_token)
    if [ -z "$TOKEN" ]; then
        nok "No se pudo obtener token de GitHub"
        exit 1
    fi
    echo "📊 Estado de GitHub Actions para $GH_REPO"
    echo ""
    curl -s -H "Authorization: Bearer $TOKEN" \
        "https://api.github.com/repos/${GH_REPO}/actions/runs?per_page=5" | \
    python3 -c "
import json,sys
data = json.load(sys.stdin)
for run in data.get('workflow_runs', []):
    icon = '✅' if run.get('conclusion') == 'success' else '❌' if run.get('conclusion') == 'failure' else '⏳'
    print(f'  {icon} #{run[\"run_number\"]} {run[\"head_branch\"]:30s} {run[\"status\"]:10s} {run.get(\"conclusion\",\"pending\"):10s}')
" 2>&1
    exit 0
fi

# ─── Validar entorno ───────────────────────────────────────────────
DRY_RUN=false
COMMIT_MSG="${1:-}"
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
    COMMIT_MSG="${2:-}"
fi
COMMIT_MSG="${COMMIT_MSG:-automejora: mejora autonoma ${TIMESTAMP}}"

TOKEN=$(get_token)
if [ -z "$TOKEN" ]; then
    nok "No se pudo obtener token de GitHub. Configurá GITHUB_TOKEN o git credential store."
    nok "Podés: export GITHUB_TOKEN=ghp_..."
    exit 1
fi

# Verificar que estamos en el repo
if ! git rev-parse --git-dir &>/dev/null; then
    nok "No estamos dentro de un repositorio Git"
    exit 1
fi

# Verificar que estamos en main
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    warn "No estás en main (estás en $CURRENT_BRANCH)"
    warn "Se va a pushear desde la rama actual igualmente"
fi

# ─── FLUJO PRINCIPAL ───────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔄 AUTOMEJORA — Ciclo v2"
echo "  Rama:   $BRANCH"
echo "  Msg:    $COMMIT_MSG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Guardar cambios sin commitear (si hay)
if [ -n "$(git status --porcelain)" ]; then
    info "Hay cambios sin commitear. Se incluirán en el commit."
    git add -A
fi

# 2. Crear rama temporal
if $DRY_RUN; then
    info "[DRY-RUN] git checkout -b $BRANCH"
    info "[DRY-RUN] git commit -m \"$COMMIT_MSG\""
    info "[DRY-RUN] git push origin $BRANCH"
else
    info "Creando rama $BRANCH..."
    git checkout -b "$BRANCH"

    # Si no hay cambios staged, crear un commit vacío no, mejor avisar
    if git diff --cached --quiet; then
        warn "No hay cambios para commitear"
        # Commit vacío igual para que GH Actions se dispare
        git commit --allow-empty -m "$COMMIT_MSG"
    else
        git commit -m "$COMMIT_MSG"
    fi

    info "Pusheando a GitHub..."
    if ! git push origin "$BRANCH" 2>&1; then
        nok "Error al pushear. Revertiendo..."
        git checkout main 2>/dev/null || git checkout "${CURRENT_BRANCH}"
        git branch -D "$BRANCH" 2>/dev/null || true
        notify "❌ Automejora Falló" "Error de push en $BRANCH" high
        exit 1
    fi
    ok "Push exitoso — $BRANCH en GitHub"
fi

# 3. Monitorear GitHub Actions
echo ""
info "Monitoreando GitHub Actions..."
echo "     (consultando cada ${POLL_INTERVAL}s, timeout ${MAX_POLLS} intentos)"
echo ""

if $DRY_RUN; then
    info "[DRY-RUN] Monitoreo de GH Actions omitido"
    info "[DRY-RUN] Conclusión simulada: SUCCESS"
    echo ""
    echo -e "  ${VERDE}━━━ TESTS PASARON (simulado) ━━━${RESET}"
    ok "Dry-run: merge simulado a main"
    echo ""
    exit 0
fi

attempt=0
CONCLUSION=""
RUN_ID=""

while [ $attempt -lt $MAX_POLLS ]; do
    sleep $POLL_INTERVAL
    attempt=$((attempt + 1))

    # Obtener runs para esta rama
    RESP=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "https://api.github.com/repos/${GH_REPO}/actions/runs?branch=${BRANCH}&per_page=1" 2>&1)

    RUN_ID=$(echo "$RESP" | python3 -c "
import json,sys
try:
    data = json.load(sys.stdin)
    runs = data.get('workflow_runs', [])
    if runs:
        print(runs[0].get('id', ''))
    else:
        print('')
except: print('')
" 2>/dev/null)

    if [ -z "$RUN_ID" ]; then
        echo -ne "\r  ⏳ Intento $attempt/$MAX_POLLS — run no disponible aún..."
        continue
    fi

    STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "https://api.github.com/repos/${GH_REPO}/actions/runs/${RUN_ID}" | \
        python3 -c "
import json,sys
try:
    data = json.load(sys.stdin)
    print(data.get('status', 'unknown'))
except: print('unknown')
" 2>/dev/null)

    CONCLUSION=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "https://api.github.com/repos/${GH_REPO}/actions/runs/${RUN_ID}" | \
        python3 -c "
import json,sys
try:
    data = json.load(sys.stdin)
    print(data.get('conclusion', '') or '')
except: print('')
" 2>/dev/null)

    echo -ne "\r  ⏳ Intento $attempt/$MAX_POLLS — status: $STATUS   "

    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo ""
        break
    fi
done

echo ""

# 4. Decidir según resultado
if [ -z "$CONCLUSION" ]; then
    nok "Timeout esperando a GitHub Actions ($MAX_POLLS intentos)"
    notify "⏰ Automejora Timeout" "No se completó a tiempo: $BRANCH" high
    exit 1
fi

if [ "$CONCLUSION" = "success" ]; then
    # ─── SUCCESS ────────────────────────────────────────────────────
    echo -e "  ${VERDE}━━━ TESTS PASARON ━━━${RESET}"
    ok "GitHub Actions: SUCCESS"
    echo ""

    if $DRY_RUN; then
        info "[DRY-RUN] git checkout main"
        info "[DRY-RUN] git merge $BRANCH"
        info "[DRY-RUN] git push origin main"
        info "[DRY-RUN] git branch -d $BRANCH"
        info "[DRY-RUN] git push origin --delete $BRANCH"
    else
        info "Fusionando a main..."
        git checkout main
        git merge "$BRANCH" --no-ff -m "merge(automejora): $COMMIT_MSG"
        git push origin main

        info "Limpiando rama temporal..."
        git branch -d "$BRANCH"
        git push origin --delete "$BRANCH" 2>/dev/null || true

        echo ""
        ok "Ciclo completado exitosamente"
        notify "✅ Automejora Exitosa" "Mejora aplicada y testeada en la nube" low
    fi

elif [ "$CONCLUSION" = "failure" ] || [ "$CONCLUSION" = "cancelled" ]; then
    # ─── FAILURE ────────────────────────────────────────────────────
    echo -e "  ${ROJO}━━━ TESTS FALLARON ━━━${RESET}"
    nok "GitHub Actions: $CONCLUSION"
    echo ""

    # Obtener logs del run para diagnóstico
    LOGS=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "https://api.github.com/repos/${GH_REPO}/actions/runs/${RUN_ID}/jobs" | \
        python3 -c "
import json,sys
data = json.load(sys.stdin)
for job in data.get('jobs', []):
    for step in job.get('steps', []):
        if step.get('conclusion') == 'failure':
            print(f'  ❌ {step[\"name\"]}')
" 2>/dev/null)

    echo "  Pasos fallidos:"
    echo "$LOGS"
    echo ""

    if $DRY_RUN; then
        info "[DRY-RUN] git checkout main"
        info "[DRY-RUN] git branch -D $BRANCH"
        info "[DRY-RUN] git push origin --delete $BRANCH"
    else
        info "Revertiendo: descartando rama $BRANCH..."
        git checkout main
        git branch -D "$BRANCH"
        git push origin --delete "$BRANCH" 2>/dev/null || true

        nok "Ciclo falló — rama descartada"
        notify "❌ Automejora Falló" "Tests no pasaron en $BRANCH. Revisá GH Actions." high
    fi

else
    # ─── OTRO (cancelled, skipped, etc) ─────────────────────────────
    warn "Resultado inesperado: $CONCLUSION"
    if $DRY_RUN; then
        info "[DRY-RUN] No se hace nada"
    else
        notify "⚠️ Automejora Indefinido" "Resultado: $CONCLUSION en $BRANCH" normal
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Fin del ciclo automejora"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
