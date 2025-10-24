#!/usr/bin/env bash

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
    # Validate variable name to avoid unexpected command execution
    if [[ ! "$var_name" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then
        echo "Error: Invalid variable name '$var_name'" >&2
        return 1
    fi
    local current_value="${!var_name-}"

    if [[ -n "$current_value" ]]; then
        return 0
    fi

    if [[ ! -f "$HOME/.bashrc" ]]; then
        return 0
    fi

    local loaded_value=""
    loaded_value="$(
        bash --noprofile --norc -c '
            if [[ -f "$1" ]]; then
                source "$1" >/dev/null 2>&1
            fi
            printenv "$2"
        ' bash "$HOME/.bashrc" "$var_name" 2>/dev/null || true
    )"

    if [[ -n "$loaded_value" ]]; then
        export "$var_name=$loaded_value"
    fi
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

mcp_common_path=""
if [[ -f "$SCRIPT_DIR/../../scripts/mcp_common.sh" ]]; then
    mcp_common_path="$SCRIPT_DIR/../../scripts/mcp_common.sh"
elif [[ -f "$SCRIPT_DIR/mcp_common.sh" ]]; then
    mcp_common_path="$SCRIPT_DIR/mcp_common.sh"
else
    echo "Error: mcp_common.sh not found relative to $SCRIPT_DIR" >&2
    exit 1
fi

source "$mcp_common_path" "${args[@]}"
exit $?
