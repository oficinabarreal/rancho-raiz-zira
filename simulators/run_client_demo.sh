#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$DIR/crm_simulator.py" \
  --session client_demo \
  --with-external \
  --output "$DIR/client_demo.md" \
  --export "$DIR/client_demo.json"
