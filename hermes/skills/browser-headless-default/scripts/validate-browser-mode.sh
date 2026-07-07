#!/usr/bin/env bash
# Quick gate: fail if recent Hermes gateway log shows show_browser without opt-in.
set -euo pipefail

LOG="${HERMES_GATEWAY_LOG:-$HOME/.hermes_prod/logs/gateway.log}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK="$SCRIPT_DIR/check_browser_policy.py"

if [[ ! -f "$LOG" ]]; then
  echo "WARN: no gateway log at $LOG — skipping log scan"
  exit 0
fi

# Last 500 lines — headed pops are usually recent
tail -500 "$LOG" 2>/dev/null | python3 "$CHECK" - || {
  echo "FAIL: headed browser action detected in recent gateway log"
  echo "Fix: hide_browser / use Playwright headless. See skills/browser-headless-default/SKILL.md"
  exit 1
}

echo "OK: validate-browser-mode (log tail clean)"
