#!/bin/bash
# Guard against setting strict mode when sourced in incompatible shells
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being executed directly, apply strict mode
    set -euo pipefail
    IFS=$'\n\t'  # Safe word splitting
elif [[ -z "${STRICT_MODE_SET:-}" ]]; then
    # Script is being sourced and strict mode not yet applied
    set -euo pipefail
    IFS=$'\n\t'  # Safe word splitting
    export STRICT_MODE_SET=1
fi

# Enhanced error handling with line info
trap 'echo "Error on line $LINENO: $BASH_COMMAND" >&2; exit 1' ERR

# Claude bot management functions
# Source this file to make functions available in current shell:
#   source scripts/claude_functions.sh

# Define color variables (with validation for strict mode)
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Validate color variables are set
: "${BLUE:?}" "${GREEN:?}" "${YELLOW:?}" "${RED:?}" "${NC:?}"

# Function to check if Claude bot server is running
is_claude_bot_running() {
    if curl -s http://127.0.0.1:5001/health &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start Claude bot server in background
start_claude_bot_background() {
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

    # Setup signal handlers for cleanup
    setup_signal_handlers

    # Check if start script exists in project root
    if [ -f "$PROJECT_ROOT/start-claude-bot.sh" ]; then
        echo -e "${BLUE}🚀 Starting Claude bot server in background...${NC}"

        # Start the server in background, redirecting output to log file
        nohup "$PROJECT_ROOT/start-claude-bot.sh" > "$HOME/.claude-bot-server.log" 2>&1 &

        # Store the PID atomically
        create_pid_file "$HOME/.claude-bot-server.pid" "$!"
        echo -e "${GREEN}✅ Claude bot server started with PID $!${NC}"
        echo -e "${BLUE}📋 Logs: tail -f $HOME/.claude-bot-server.log${NC}"
        return 0
    else
        echo -e "${RED}❌ start-claude-bot.sh not found in $PROJECT_ROOT${NC}"
        return 1
    fi
}

# Function to stop Claude bot server
stop_claude_bot() {
    local pid_file="$HOME/.claude-bot-server.pid"
    if [ -f "$pid_file" ]; then
        local PID=$(cat "$pid_file")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${BLUE}🛑 Stopping Claude bot server (PID: $PID)...${NC}"
            kill "$PID"
            remove_pid_file "$pid_file"
            echo -e "${GREEN}✅ Claude bot server stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  Process not running, cleaning up PID file${NC}"
            remove_pid_file "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found${NC}"
    fi
}

# Function to restart Claude bot server
restart_claude_bot() {
    echo -e "${BLUE}🔄 Restarting Claude bot server...${NC}"
    stop_claude_bot
    sleep 2

    if start_claude_bot_background; then
        sleep 3
        if is_claude_bot_running; then
            echo -e "${GREEN}✅ Claude bot server restarted successfully${NC}"
        else
            echo -e "${RED}❌ Failed to restart Claude bot server${NC}"
            return 1
        fi
    else
        return 1
    fi
}

# Function to check Claude bot server status
claude_bot_status() {
    if is_claude_bot_running; then
        echo -e "${GREEN}✅ Claude bot server is running on port 5001${NC}"
        if [ -f "$HOME/.claude-bot-server.pid" ]; then
            local PID=$(cat "$HOME/.claude-bot-server.pid")
            echo -e "${BLUE}📋 PID: $PID${NC}"
        fi
        echo -e "${BLUE}📋 Health check: curl http://127.0.0.1:5001/health${NC}"
    else
        echo -e "${RED}❌ Claude bot server is not running${NC}"
    fi
}

# Signal handler setup with comprehensive signal coverage
setup_signal_handlers() {
    trap 'cleanup_on_exit' EXIT
    trap 'cleanup_on_interrupt' INT TERM HUP
    # Restore terminal state on exit
    trap 'stty sane 2>/dev/null || true' EXIT
}

# Cleanup functions with error logging
cleanup_on_exit() {
    local pid_file="$HOME/.claude-bot-server.pid"

    # Remove PID file and lock with error handling
    if ! rm -f "$pid_file" "${pid_file}.lock" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Warning: Failed to remove PID files${NC}" >&2
    fi

    # Remove temp directory with error handling
    if [[ -d "/tmp/backup_temp.$$" ]] && ! rm -rf "/tmp/backup_temp.$$" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Warning: Failed to remove temp directory${NC}" >&2
    fi
}

cleanup_on_interrupt() {
    echo -e "${YELLOW}⚠️  Received interrupt signal. Cleaning up...${NC}"
    cleanup_on_exit
    exit 1
}

# Atomic PID file creation with exclusive locking and validation
create_pid_file() {
    local pid_file="$1"
    local pid="$2"
    local temp_file="${pid_file}.tmp.$$"

    # Validate inputs
    if [[ -z "$pid_file" ]] || [[ "$pid_file" =~ \.\./ ]]; then
        echo -e "${RED}❌ Invalid PID file path: $pid_file${NC}" >&2
        return 1
    fi

    if ! [[ "$pid" =~ ^[0-9]+$ ]] || [[ "$pid" -le 0 ]]; then
        echo -e "${RED}❌ Invalid PID: $pid${NC}" >&2
        return 1
    fi

    # Ensure parent directory exists
    local parent_dir
    parent_dir=$(dirname "$pid_file")
    if [[ ! -d "$parent_dir" ]]; then
        echo -e "${RED}❌ Parent directory does not exist: $parent_dir${NC}" >&2
        return 1
    fi

    # Write PID to temp file and move atomically
    if ! echo "$pid" > "$temp_file" 2>/dev/null; then
        echo -e "${RED}❌ Failed to write to temp file: $temp_file${NC}" >&2
        return 1
    fi

    if ! mv "$temp_file" "$pid_file" 2>/dev/null; then
        rm -f "$temp_file" 2>/dev/null || true
        echo -e "${RED}❌ Failed to create PID file: $pid_file${NC}" >&2
        return 1
    fi

    return 0
}

# Secure PID file removal with locking and validation
remove_pid_file() {
    local pid_file="$1"
    local lock_file="${pid_file}.lock"

    # Validate input path
    if [[ -z "$pid_file" ]] || [[ "$pid_file" =~ \.\./  ]]; then
        echo -e "${RED}❌ Invalid PID file path: $pid_file${NC}" >&2
        return 1
    fi

    # Use flock for exclusive access with timeout
    (
        if ! flock -x -w 5 200; then
            echo -e "${YELLOW}⚠️  Failed to acquire lock for PID file removal${NC}" >&2
            return 1
        fi
        if [[ -f "$pid_file" ]] && ! rm -f "$pid_file" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Warning: Failed to remove PID file: $pid_file${NC}" >&2
        fi
    ) 200>"$lock_file"

    # Clean up lock file
    rm -f "$lock_file" 2>/dev/null || true
}

# Timeout wrapper for subprocesses
run_with_timeout() {
    local timeout_duration="${1:-30}"
    shift

    # Check if timeout utility is available
    if ! command -v timeout >/dev/null 2>&1; then
        echo -e "${RED}❌ timeout utility not found${NC}" >&2
        return 127
    fi

    # Use array to preserve arguments properly
    timeout "$timeout_duration" bash -c "$*" || {
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            echo -e "${RED}❌ Command timed out after ${timeout_duration}s${NC}" >&2
        else
            echo -e "${RED}❌ Command failed with exit code $exit_code${NC}" >&2
        fi
        return $exit_code
    }
}

# Input validation with enhanced logging
validate_input() {
    local input="$1"
    local pattern="$2"
    local description="${3:-input}"

    if ! [[ "$input" =~ $pattern ]]; then
        echo -e "${RED}❌ Invalid $description: $input (expected pattern: $pattern)${NC}" >&2
        # Log to syslog for audit trail if available
        if command -v logger >/dev/null 2>&1; then
            logger -p user.warning "claude_functions.sh: Invalid $description rejected: $input"
        fi
        return 1
    fi
    return 0
}

# Secure temporary file creation with enhanced validation
create_secure_temp() {
    local prefix="${1:-claude_temp}"
    local temp_file

    # Validate TMPDIR or use safe default
    local tmpdir="${TMPDIR:-/tmp}"
    if [[ ! -d "$tmpdir" ]] || [[ ! -w "$tmpdir" ]]; then
        echo -e "${RED}❌ Temporary directory not writable: $tmpdir${NC}" >&2
        return 1
    fi

    # Create temporary file with secure template
    if ! temp_file=$(mktemp "$tmpdir/${prefix}.XXXXXXXXXX" 2>/dev/null); then
        echo -e "${RED}❌ Failed to create temporary file in $tmpdir${NC}" >&2
        return 1
    fi

    # Set restrictive permissions
    if ! chmod 600 "$temp_file" 2>/dev/null; then
        echo -e "${RED}❌ Failed to set permissions on temp file${NC}" >&2
        rm -f "$temp_file" 2>/dev/null || true
        return 1
    fi

    echo "$temp_file"
}

# Export functions for shell availability
export -f is_claude_bot_running start_claude_bot_background stop_claude_bot restart_claude_bot claude_bot_status
export -f setup_signal_handlers cleanup_on_exit cleanup_on_interrupt create_pid_file remove_pid_file
export -f run_with_timeout validate_input create_secure_temp
