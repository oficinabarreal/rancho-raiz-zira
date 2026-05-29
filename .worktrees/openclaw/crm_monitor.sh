#!/bin/bash
# CRM Monitor — Persistencia de agentes en segundo plano
# Verifica que Hermes y OpenClaw esten operativos
# Ejecutar desde crontab cada 5 minutos
#
# crontab -e
# */5 * * * * /ruta/a/.worktrees/openclaw/crm_monitor.sh >> /tmp/crm_monitor.log 2>&1

LOCKFILE="/tmp/crm_monitor.lock"
exec 200>"$LOCKFILE"
flock -n 200 || exit 1

PROJECT="/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3"
STATE_DIR="$PROJECT/crm_state"
LOG_FILE="/tmp/crm_monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] CRM Monitor: check..."

# 1. Verificar estado del pipeline
cd "$PROJECT"
if python3 -c "from crm.connectors import GmailConnector; exit(0)" 2>/dev/null; then
    echo "  ✅ GmailConnector OK"
else
    echo "  ⚠️  GmailConnector error"
fi

# 2. Verificar Telegram token
if grep -q "CRM_TG_TOKEN" hybrid/.env 2>/dev/null || grep -q "CRM_TG_TOKEN" .env 2>/dev/null; then
    echo "  ✅ Telegram token presente"
else
    echo "  ⚠️  Telegram token no encontrado"
fi

# 3. Verificar archivos clave del pipeline
for f in pipeline.py flows/arte/banner_flows.py flows/arte/reel_pipeline.py; do
    if [ -f "$PROJECT/$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ⚠️  $f FALTANTE"
    fi
done

# 4. Verificar assets en cache
BANNER_COUNT=$(ls -1 "$PROJECT/simulaciones_output/"banner_*.png 2>/dev/null | wc -l)
GIF_COUNT=$(ls -1 "$PROJECT/simulaciones_output/"anim_*.gif 2>/dev/null | wc -l)
REEL_COUNT=$(ls -1 "$HOME/ranchoraiz_reels/"*.mp4 2>/dev/null | wc -l)
echo "  🖼️  Banners: $BANNER_COUNT | GIFs: $GIF_COUNT | Reels: $REEL_COUNT"

# 5. Verificar Google token
if [ -f "$STATE_DIR/.google_token.json" ]; then
    TOKEN_SIZE=$(stat -c%s "$STATE_DIR/.google_token.json" 2>/dev/null || stat -f%z "$STATE_DIR/.google_token.json" 2>/dev/null)
    echo "  ✅ Google token: ${TOKEN_SIZE}B"
else
    echo "  ⚠️  Google token faltante"
fi

# 6. Alerta si algo critico falta
ALERTA=""
if [ ! -f "$PROJECT/pipeline.py" ]; then
    ALERTA="$ALERTA\n  🚨 pipeline.py FALTANTE"
fi
if [ $BANNER_COUNT -eq 0 ]; then
    ALERTA="$ALERTA\n  ⚠️  Sin banners en cache"
fi

if [ -n "$ALERTA" ]; then
    echo -e "  📡 Enviando alerta:$ALERTA"
    # Notificar via Telegram si hay problemas
    if command -v python3 &>/dev/null; then
        TG_TOKEN=$(grep CRM_TG_TOKEN "$PROJECT/hybrid/.env" 2>/dev/null | cut -d= -f2)
        TG_CHAT=$(grep CRM_TG_CHAT_ID "$PROJECT/hybrid/.env" 2>/dev/null | cut -d= -f2)
        if [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ]; then
            MSG="CRM Monitor [$TIMESTAMP]"
            MSG="$MSG$ALERTA"
            curl -s -X POST "https://api.telegram.org/bot$TG_TOKEN/sendMessage" \
                -d "chat_id=$TG_CHAT" \
                -d "text=$MSG" \
                -o /dev/null 2>/dev/null
        fi
    fi
fi

echo "  ✅ Monitor OK"
