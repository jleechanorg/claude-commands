#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_LAUNCHER_PATH="$0"

MCP_PRODUCT_NAME="Claude"
MCP_CLI_BIN="claude"


# Preserve --test flag handling so CI invocations remain side-effect free
TEST_MODE=false
FORWARDED_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --test)
            TEST_MODE=true
            ;;
        *)
            FORWARDED_ARGS+=("$arg")
            ;;
    esac
done

if [[ "$TEST_MODE" == true ]]; then
    export TEST_MODE=true
else
    unset TEST_MODE 2>/dev/null || true
fi

# Reset positional parameters for downstream scripts
if (( ${#FORWARDED_ARGS[@]} )); then
    set -- "${FORWARDED_ARGS[@]}"
else
    set --
fi
# Location-aware sourcing: works from both root and scripts/ directory
if [[ -f "$SCRIPT_DIR/mcp_common.sh" ]]; then
    source "$SCRIPT_DIR/mcp_common.sh" "$@"
elif [[ -f "$SCRIPT_DIR/scripts/mcp_common.sh" ]]; then
    source "$SCRIPT_DIR/scripts/mcp_common.sh" "$@"
else
    echo "❌ Error: Cannot find mcp_common.sh" >&2
    exit 1
fi
exit $?
