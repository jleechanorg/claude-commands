#!/usr/bin/env bash
# Universal MCP Server Installer for Claude Code & Codex
# Installs all MCP servers to user scope for global availability
#
# Usage:
#   ./scripts/install_mcp_servers.sh           # Install for Claude (default)
#   ./scripts/install_mcp_servers.sh claude    # Install for Claude explicitly
#   ./scripts/install_mcp_servers.sh codex     # Install for Codex
#   ./scripts/install_mcp_servers.sh both      # Install for both Claude and Codex
#
# On a new computer: Just run this script to install all your MCP servers

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_LAUNCHER_PATH="$0"

# Colors for output (defined early for use in argument parsing)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
TEST_INSTALL_DIR=""

# Check for --test-dir flag
if [[ "${1:-}" == "--test-dir" ]]; then
    if [[ -z "${2:-}" ]]; then
        echo -e "${RED}❌ Error: --test-dir requires a directory path${NC}" >&2
        echo "Usage: $0 --test-dir /path/to/test/dir [claude|codex|both]" >&2
        exit 1
    fi
    TEST_INSTALL_DIR="$2"
    shift 2
fi

# Normalize arguments for compatibility with old launchers
# Translate --dry-run to --test and preserve additional flags
normalized_args=()
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        normalized_args+=("--test")
    else
        normalized_args+=("$arg")
    fi
done

TARGET_ARG=""
PASSTHROUGH_ARGS=()
TEST_MODE_DETECTED=false
for arg in "${normalized_args[@]}"; do
    lower_arg="$(printf '%s' "$arg" | tr '[:upper:]' '[:lower:]')"
    case "$lower_arg" in
        claude|codex|both)
            if [[ -z "$TARGET_ARG" ]]; then
                TARGET_ARG="$lower_arg"
            else
                PASSTHROUGH_ARGS+=("$arg")
            fi
            ;;
        --test)
            PASSTHROUGH_ARGS+=("--test")
            TEST_MODE_DETECTED=true
            ;;
        *)
            PASSTHROUGH_ARGS+=("$arg")
            ;;
    esac
done

if [[ -z "$TARGET_ARG" ]]; then
    # Check if we're being re-executed after Bash upgrade (preserves target through re-exec)
    if [[ -n "${MCP_TARGET_PRODUCT:-}" ]]; then
        TARGET_ARG="$MCP_TARGET_PRODUCT"
    else
        TARGET_ARG="claude"
    fi
fi

TARGET_PRODUCT="$TARGET_ARG"
# Export for preservation through Bash 4 re-exec on macOS
export MCP_TARGET_PRODUCT="$TARGET_PRODUCT"

# Export test directory if provided
if [[ -n "$TEST_INSTALL_DIR" ]]; then
    export TEST_INSTALL_DIR
    export TEST_MODE="true"
    echo -e "${YELLOW}🧪 TEST MODE: Installing to $TEST_INSTALL_DIR${NC}"
    echo -e "${YELLOW}   Production configs will not be modified${NC}"
    echo ""
fi

# Function to load environment variables from .bashrc (for Codex)
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
        ' -- "$HOME/.bashrc" "$var_name" 2>/dev/null || true
    )"

    if [[ -n "$loaded_value" ]]; then
        export "$var_name=$loaded_value"
    fi
}

# Main installation logic - matches old launcher pattern
case "$TARGET_PRODUCT" in
    claude)
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║  Claude MCP Server Installer (User Scope)                     ║${NC}"
        echo -e "${BLUE}║  Installing to user scope for global availability             ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}📍 Installation Scope: User (available in ALL projects)${NC}"
        echo -e "${GREEN}📦 All servers will be globally available after installation${NC}"
        echo ""

        # Check if CLI is available (skip in test mode)
        if [[ "$TEST_MODE_DETECTED" != true ]]; then
            if ! command -v claude &> /dev/null; then
                echo -e "${RED}❌ claude CLI not found. Please install Claude first.${NC}"
                echo -e "${YELLOW}💡 Install from: https://claude.com/claude-code${NC}"
                exit 1
            fi
        fi

        # Configuration (matches old launcher)
        MCP_PRODUCT_NAME="Claude"
        MCP_CLI_BIN="claude"
        export MCP_SCOPE="user"
        export MCP_INSTALL_DUAL_SCOPE="false"
        export TEST_MODE="${TEST_MODE:-false}"

        # Source shared logic (like old launcher)
        source "${SCRIPT_DIR}/mcp_common.sh" "${PASSTHROUGH_ARGS[@]}"
        exit $?
        ;;

    codex)
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║  Codex MCP Server Installer (User Scope)                      ║${NC}"
        echo -e "${BLUE}║  Installing to user scope for global availability             ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}📍 Installation Scope: User (available in ALL projects)${NC}"
        echo -e "${GREEN}📦 All servers will be globally available after installation${NC}"
        echo ""

        # Check if CLI is available (skip in test mode)
        if [[ "$TEST_MODE_DETECTED" != true ]]; then
            if ! command -v codex &> /dev/null; then
                echo -e "${RED}❌ codex CLI not found. Please install Codex first.${NC}"
                exit 1
            fi
        fi

        # Configuration (matches old launcher)
        MCP_PRODUCT_NAME="Codex"
        MCP_CLI_BIN="codex"
        export MCP_SCOPE="user"
        export MCP_INSTALL_DUAL_SCOPE="false"
        export TEST_MODE="${TEST_MODE:-false}"

        # Load environment variables from .bashrc (like old codex launcher)
        load_interactive_env_var "ANTHROPIC_API_KEY"
        load_interactive_env_var "GITHUB_TOKEN"
        load_interactive_env_var "XAI_API_KEY"
        load_interactive_env_var "PERPLEXITY_API_KEY"
        load_interactive_env_var "RENDER_API_KEY"
        load_interactive_env_var "GROK_API_KEY"

        if [[ -z "${GROK_DEFAULT_MODEL:-}" ]]; then
            export GROK_DEFAULT_MODEL="grok-3"
        fi

        if [[ -z "${XAI_DEFAULT_CHAT_MODEL:-}" ]]; then
            export XAI_DEFAULT_CHAT_MODEL="$GROK_DEFAULT_MODEL"
        fi

        # Source shared logic (like old launcher)
        source "${SCRIPT_DIR}/mcp_common.sh" "${PASSTHROUGH_ARGS[@]}"
        exit $?
        ;;

    both)
        echo -e "${BLUE}🔄 Installing for both Claude and Codex...${NC}"
        echo ""

        # Run Claude installation
        "$0" claude "${PASSTHROUGH_ARGS[@]}"
        CLAUDE_EXIT=$?

        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        # Run Codex installation
        "$0" codex "${PASSTHROUGH_ARGS[@]}"
        CODEX_EXIT=$?

        # Exit with failure if either failed
        if [[ $CLAUDE_EXIT -ne 0 ]] || [[ $CODEX_EXIT -ne 0 ]]; then
            exit 1
        fi
        exit 0
        ;;

    *)
        echo -e "${RED}❌ Invalid target: $TARGET_PRODUCT${NC}"
        echo -e "${YELLOW}Usage: $0 [claude|codex|both]${NC}"
        echo -e "${YELLOW}  claude - Install for Claude only (default)${NC}"
        echo -e "${YELLOW}  codex  - Install for Codex only${NC}"
        echo -e "${YELLOW}  both   - Install for both Claude and Codex${NC}"
        exit 1
        ;;
esac
