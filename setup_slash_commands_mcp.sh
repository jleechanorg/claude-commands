#!/usr/bin/env bash
# Standalone installer for the claude-slash-commands MCP server.
# This script mirrors the behaviour previously embedded in claude_mcp.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/claude_slash_commands_$(date +%Y%m%d_%H%M%S).log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DEFAULT_MCP_ENV_FLAGS=(
    --env "MCP_CLAUDE_DEBUG=false"
    --env "MCP_VERBOSE_TOOLS=false"
    --env "MCP_AUTO_DISCOVER=false"
)

log_with_timestamp() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" | tee -a "$LOG_FILE"
}

log_error_details() {
    local operation="$1"
    local context="$2"
    local error_output="$3"
    log_with_timestamp "ERROR: $operation failed for $context"
    log_with_timestamp "Error details: $error_output"
}

server_already_exists() {
    local servers_output="$1"
    echo "$servers_output" | grep -q "^claude-slash-commands:"
}

print_header() {
    echo -e "${BLUE}🚀 Configuring Slash Commands MCP server...${NC}"
    log_with_timestamp "Starting slash commands MCP server setup"
    echo ""
    echo "📝 Logging to: $LOG_FILE"
    echo ""
}

check_prerequisites() {
    if ! command -v claude >/dev/null 2>&1; then
        echo -e "${RED}❌ The 'claude' CLI is required but was not found in PATH.${NC}"
        log_with_timestamp "ERROR: claude CLI missing"
        exit 1
    fi
}

attempt_uvx_install() {
    local add_exit_code=1
    local add_output=""

    if command -v uvx >/dev/null 2>&1; then
        echo -e "${BLUE}📦 Attempting ephemeral uvx installation...${NC}"
        log_with_timestamp "Attempting uvx-based installation"

        if ! command -v claude-slash-commands-mcp >/dev/null 2>&1; then
            echo -e "${BLUE}📥 Installing claude-slash-commands MCP via uvx...${NC}"
            log_with_timestamp "Installing claude-slash-commands via uvx"
            set +e
            uvx --from "file://$SCRIPT_DIR/mcp_servers/slash_commands" claude-slash-commands-mcp >/dev/null 2>&1
            local uvx_exit=$?
            set -e

            if [ $uvx_exit -eq 0 ]; then
                echo -e "${GREEN}✅ uvx installation completed${NC}"
                log_with_timestamp "uvx installation completed"
            else
                echo -e "${YELLOW}⚠️ uvx installation failed, will fall back to local setup${NC}"
                log_with_timestamp "uvx installation failed"
            fi
        else
            echo -e "${GREEN}✅ claude-slash-commands-mcp command already available${NC}"
            log_with_timestamp "claude-slash-commands-mcp command found"
        fi

        echo -e "${BLUE}⚙️ Configuring Claude MCP to use claude-slash-commands-mcp...${NC}"
        set +e
        add_output=$(claude mcp add --scope user "claude-slash-commands" "claude-slash-commands-mcp" "${DEFAULT_MCP_ENV_FLAGS[@]}" 2>&1)
        add_exit_code=$?
        set -e

        if [ $add_exit_code -ne 0 ]; then
            echo -e "${BLUE}🔄 Retrying configuration using add-json...${NC}"
            log_with_timestamp "Direct add failed, attempting add-json"
            local add_json_payload
            add_json_payload=$(cat <<JSON
{"command":"uvx","args":["--from","file://$SCRIPT_DIR/mcp_servers/slash_commands","claude-slash-commands-mcp"],"env":{"MCP_CLAUDE_DEBUG":"false","MCP_VERBOSE_TOOLS":"false","MCP_AUTO_DISCOVER":"false"}}
JSON
)
            set +e
            add_output=$(claude mcp add-json --scope user "claude-slash-commands" "$add_json_payload" 2>&1)
            add_exit_code=$?
            set -e
        fi

        if [ $add_exit_code -eq 0 ]; then
            echo -e "${GREEN}✅ Successfully configured claude-slash-commands via uvx${NC}"
            log_with_timestamp "Configured slash commands MCP using uvx"
            return 0
        fi

        log_error_details "uvx configuration" "claude-slash-commands" "$add_output"
        echo -e "${YELLOW}⚠️ uvx configuration failed, falling back to local installation${NC}"
    else
        echo -e "${YELLOW}⚠️ uvx not found, falling back to local installation${NC}"
        log_with_timestamp "uvx not available"
    fi

    return 1
}

select_python_interpreter() {
    if [ -x "$SCRIPT_DIR/vpython" ]; then
        echo "$SCRIPT_DIR/vpython"
    elif [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
        echo "$SCRIPT_DIR/venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        command -v python3
    elif command -v python >/dev/null 2>&1; then
        command -v python
    else
        echo ""
    fi
}

configure_local_installation() {
    local slash_commands_path="$SCRIPT_DIR/mcp_servers/slash_commands"

    if [ ! -f "$slash_commands_path/server.py" ]; then
        echo -e "${RED}❌ Slash Commands MCP server not found at $slash_commands_path/server.py${NC}"
        log_with_timestamp "ERROR: Slash Commands MCP server missing at $slash_commands_path/server.py"
        return 1
    fi

    local python_interpreter
    python_interpreter=$(select_python_interpreter)

    if [ -z "$python_interpreter" ]; then
        echo -e "${RED}❌ Python interpreter not found. Unable to continue.${NC}"
        log_with_timestamp "ERROR: Python interpreter not found"
        return 1
    fi

    echo -e "${BLUE}🐍 Using Python interpreter: $python_interpreter${NC}"
    log_with_timestamp "Using Python interpreter: $python_interpreter"

    echo -e "${BLUE}🔗 Adding claude-slash-commands via local server.py...${NC}"
    set +e
    local add_output
    add_output=$(claude mcp add --scope user "claude-slash-commands" "$python_interpreter" "$slash_commands_path/server.py" "${DEFAULT_MCP_ENV_FLAGS[@]}" 2>&1)
    local add_exit_code=$?
    set -e

    if [ $add_exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Successfully added claude-slash-commands (local)${NC}"
        log_with_timestamp "Configured slash commands MCP using local server"
        return 0
    fi

    log_error_details "local configuration" "claude-slash-commands" "$add_output"
    echo -e "${RED}❌ Failed to configure claude-slash-commands via local server${NC}"
    return 1
}

main() {
    print_header
    check_prerequisites

    local existing_servers
    existing_servers=$(claude mcp list 2>/dev/null || true)

    if server_already_exists "$existing_servers"; then
        echo -e "${GREEN}✅ claude-slash-commands already configured. Nothing to do.${NC}"
        log_with_timestamp "claude-slash-commands already present"
        exit 0
    fi

    echo -e "${BLUE}🧹 Removing any existing claude-slash-commands entries...${NC}"
    claude mcp remove "claude-slash-commands" >/dev/null 2>&1 || true

    if attempt_uvx_install; then
        exit 0
    fi

    if configure_local_installation; then
        exit 0
    fi

    log_with_timestamp "Failed to configure claude-slash-commands via all methods"
    exit 1
}

main "$@"
