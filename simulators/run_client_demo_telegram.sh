#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MSG="$(python3 "$DIR/crm_simulator.py" \
  --session client_demo \
  --with-external \
  --format telegram-session)"

python3 /root/.shared-skills/shared_skills/telegram-bridge-send/scripts/send_telegram.py \
  --message "$MSG"
