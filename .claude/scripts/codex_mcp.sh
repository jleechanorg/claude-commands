#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_LAUNCHER_PATH="$0"

MCP_PRODUCT_NAME="Codex"
MCP_CLI_BIN="codex"

# Support --dry-run as an alias for --test
args=()
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        args+=("--test")
    else
        args+=("$arg")
    fi
done

# Ensure secrets that live in ~/.bashrc are available even when this launcher
# runs in a non-interactive shell (e.g. via `bash -lc`).
load_interactive_env_var() {
    local var_name="$1"
    [[ "$var_name" =~ ^[A-Z_][A-Z0-9_]*$ ]] || { echo "Error: Invalid variable '$var_name'" >&2; return 1; }
    [[ -n "${!var_name-}" ]] && return 0
    local env_file="${CLAUDE_MCP_ENV_FILE:-$HOME/.config/claude-mcp/env}"
    [[ -f "$env_file" ]] || return 0
    local line
    line="$(grep -E "^\s*${var_name}=.*" "$env_file" | tail -n1 || true)"
    [[ -z "$line" ]] && return 0
    local value="${line#*=}"
    value="${value%\"}"; value="${value#\"}"
    export "$var_name=$value"
}

API_KEYS_TO_LOAD=(
    "XAI_API_KEY"
    "GROK_API_KEY"
    "RENDER_API_KEY"
    "PERPLEXITY_API_KEY"
)

for api_key_var in "${API_KEYS_TO_LOAD[@]}"; do
    load_interactive_env_var "$api_key_var"
done

unset -v api_key_var
unset -v API_KEYS_TO_LOAD

if [[ -z "${GROK_DEFAULT_MODEL:-}" ]]; then
    export GROK_DEFAULT_MODEL="grok-3"
fi

if [[ -z "${XAI_DEFAULT_CHAT_MODEL:-}" ]]; then
    export XAI_DEFAULT_CHAT_MODEL="$GROK_DEFAULT_MODEL"
fi

if [[ -f "$SCRIPT_DIR/mcp_common.sh" ]]; then
  source "$SCRIPT_DIR/mcp_common.sh" "${args[@]}"
elif [[ -f "$SCRIPT_DIR/../mcp_common.sh" ]]; then
  source "$SCRIPT_DIR/../mcp_common.sh" "${args[@]}"
elif [[ -f "$SCRIPT_DIR/../scripts/mcp_common.sh" ]]; then
  source "$SCRIPT_DIR/../scripts/mcp_common.sh" "${args[@]}"
else
  echo "❌ Error: Cannot find mcp_common.sh relative to $SCRIPT_DIR" >&2
  exit 1
fi

exit $?
