#!/usr/bin/env bash
set -euo pipefail

PAYLOAD="${1:-}"
[ -n "$PAYLOAD" ] || exit 0

EVENT_TYPE=""
if command -v jq >/dev/null 2>&1; then
  EVENT_TYPE=$(printf '%s' "$PAYLOAD" | jq -r '.type // empty' 2>/dev/null || true)
else
  EVENT_TYPE=$(python3 - <<'PY' "$PAYLOAD" 2>/dev/null || true
import json, sys
try:
    print((json.loads(sys.argv[1]) or {}).get('type',''))
except Exception:
    print('')
PY
)
fi

[ "$EVENT_TYPE" = "agent-turn-complete" ] || exit 0

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
[ -n "$ROOT" ] || exit 0

if [ -x "$ROOT/.claude/hooks/git-header.sh" ]; then
  exec "$ROOT/.claude/hooks/git-header.sh" --status-only
fi
if [ -x "$ROOT/.codex/hooks/git-header.sh" ]; then
  exec "$ROOT/.codex/hooks/git-header.sh"
fi
if [ -x "$HOME/.claude/hooks/git-header.sh" ]; then
  exec "$HOME/.claude/hooks/git-header.sh" --status-only
fi

exit 0
