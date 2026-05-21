#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$DIR/crm_simulator.py" \
  --session zira_demo \
  --output "$DIR/zira_demo.md" \
  --export "$DIR/zira_demo.json"
