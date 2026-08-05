#!/usr/bin/env bash
# com.$USER.cmux-codex-approve-wrapper.sh
# launchd wrapper for the cmux auto-approve worker.
# Sources user profile so CLAUDE_MODEL/PATH come from bashrc; sets sane defaults
# so the daemon mode scans every 20 minutes using Haiku as the design-decision model.

set -euo pipefail

# Source user profile (PATH, CLAUDE_MODEL overrides, alias paths)
if [[ -f "$HOME/.bash_profile" ]]; then
    set +u
    # shellcheck disable=SC1090
    source "$HOME/.bash_profile" 2>/dev/null || true
    set -u
fi
if [[ -f "$HOME/.bashrc" ]]; then
    set +u
    # shellcheck disable=SC1090
    source "$HOME/.bashrc" 2>/dev/null || true
    set -u
fi

# Job-specific defaults — overridable via exported env in bashrc.
: "${CLAUDE_MODEL:=claude-haiku-4-5}"        # cheap design-decision model
: "${POLL_INTERVAL:=600}"                    # 10 min between scans
: "${DAEMON_MODE:=1}"                        # stay alive between scans
# Discover the live cmux socket. The previous hardcoded
# "/private/tmp/cmux-debug-appclick.sock" pointed at a retired install and
# caused the daemon to call a dead socket. Multiple builds coexist in
# /Applications (dev-fork, classic, nightly, ...); pick whichever socket is
# actually live at launchd startup time.
_CMUX_SOCKET_CANDIDATES=(/private/tmp/cmux-*.sock /tmp/cmux-*.sock "$HOME/.local/state/cmux"/*.sock "$HOME/Library/Application Support/cmux"/*.sock)
for _candidate in "${_CMUX_SOCKET_CANDIDATES[@]}"; do
    # shellcheck disable=SC2086
    for _sock in $_candidate; do
        if [[ -S "$_sock" ]]; then
            CMUX_SOCKET_PATH="$_sock"
            break 2
        fi
    done
done
unset _CMUX_SOCKET_CANDIDATES _candidate _sock
: "${LOG_FILE:=$HOME/.claude/supervisor/cmux-codex-launchd.log}"
: "${STATE_FILE:=$HOME/.claude/supervisor/cmux-codex-launchd-state.json}"
: "${WORKER_POOL_SIZE:=5}"
: "${CLASSIFY_TIMEOUT:=30}"
: "${ESCALATION_TIMEOUT:=30}"

export CLAUDE_MODEL POLL_INTERVAL DAEMON_MODE \
       CMUX_SOCKET_PATH LOG_FILE STATE_FILE \
       WORKER_POOL_SIZE CLASSIFY_TIMEOUT ESCALATION_TIMEOUT

echo "[cmux-codex-approve] starting model=$CLAUDE_MODEL poll=${POLL_INTERVAL}s daemon=$DAEMON_MODE at $(date)"

exec /opt/homebrew/bin/python3 \
    "$HOME/.claude/skills/cmux-codex-autoapprove/scripts/cmux_codex_approve_launchd.py"