#!/usr/bin/env bash
# Codex-agnostic launcher for the cross-cli Stop hook. Codex 0.144+ invokes
# the command registered in codex_hooks.json via this script so the same
# behavior is available in both repo-local and home-scope installs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"

export HERMES_HOOK_CLI="${HERMES_HOOK_CLI:-codex}"
export HERMES_HOOK_EVENT="${HERMES_HOOK_EVENT:-Stop}"

if [ -x "$SCRIPT_DIR/cross_cli_status.py" ]; then
  exec "$SCRIPT_DIR/cross_cli_status.py" "$@"
fi

if [ -x "$REPO_ROOT/.codex/hooks/cross_cli_status.py" ]; then
  exec "$REPO_ROOT/.codex/hooks/cross_cli_status.py" "$@"
fi

if [ -x "$HOME/.codex/hooks/cross_cli_status.py" ]; then
  exec "$HOME/.codex/hooks/cross_cli_status.py" "$@"
fi

echo "cross_cli_status.py not found (looked in $SCRIPT_DIR, $REPO_ROOT/.codex/hooks, and $HOME/.codex/hooks)" >&2
exit 1
