#!/usr/bin/env bash
# Real claudeor CLI (not a bash function) — OpenRouter-routed Claude Code.
# Usable from Go AO PATH shims, cron, and non-interactive shells.
# Template: copy to ~/bin/<provider-short>, edit MODEL / BASE_URL.
set -euo pipefail
: "${<PROVIDER>_API_KEY:?<PROVIDER>_API_KEY must be set (same as ~/.bashrc <wrapper>)}"
export CLAUDEOR_MODE=1
export ANTHROPIC_BASE_URL="<BASE_URL>"
export ANTHROPIC_AUTH_TOKEN="$<PROVIDER>_API_KEY"
export ANTHROPIC_API_KEY="$<PROVIDER>_API_KEY"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL_OVERRIDE:-<DEFAULT_MODEL>}"
export CLAUDE_CODE_ENABLE_EXPERIMENTAL_ADVISOR_TOOL=0
export CLAUDE_EFFORT="${CLAUDE_EFFORT:-high}"
exec claude --dangerously-skip-permissions --effort high "$@"
