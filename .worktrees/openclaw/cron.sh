#!/bin/bash
# OpenClaw — Script para crontab
# Agregar al crontab:
#   30 * * * * /ruta/a/.worktrees/openclaw/cron.sh >> /tmp/openclaw.log 2>&1
cd "$(dirname "$0")"
source .env 2>/dev/null || true
python3 daemon.py --cron
