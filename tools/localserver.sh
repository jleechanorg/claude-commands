#!/bin/bash
# localserver.sh - Start a local WorldArchitect.AI server on an available port
# This script finds an available port and runs the Flask server with comprehensive logging

set -e  # Exit on error

# Load shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../scripts/server-utils.sh"

# Robust port parsing function to handle descriptive PORT environment variables
parse_port_robust_bash() {
    local port_string="$1"
    local default_port=8081
    
    # If empty or null, return default
    if [ -z "$port_string" ]; then
        echo "$default_port"
        return
    fi
    
    # Try direct number check first (normal case)
    if [[ "$port_string" =~ ^[0-9]+$ ]]; then
        # Validate range
        if [ "$port_string" -ge 1024 ] && [ "$port_string" -le 65535 ]; then
            echo "$port_string"
            return
        else
            echo "$default_port"
            return
        fi
    fi
    
    # Extract all numbers using grep and get the last one
    numbers=$(echo "$port_string" | grep -o '[0-9]\+' | tail -1)
    
    if [ -n "$numbers" ]; then
        # Validate range
        if [ "$numbers" -ge 1024 ] && [ "$numbers" -le 65535 ]; then
            echo "$numbers"
            return
        fi
    fi
    
    echo "$default_port"
}

print_banner "WorldArchitect.AI Local Server Launcher" "Single Flask server with comprehensive logging and validation"

# Function to offer cleanup of existing servers
cleanup_servers() {
    list_worldarchitect_servers
    
    local servers=$(ps aux | grep -E "python.*main.py.*serve" | grep -v grep || true)
    
    if [ -n "$servers" ]; then
        echo ""
        echo "${EMOJI_GEAR} Server Cleanup Options:"
        echo "   [a] Kill all servers"
        echo "   [s] Select specific server to kill" 
        echo "   [n] Keep all servers running"
        echo -n "   Choice: "
        read -r choice

        case "$choice" in
            a|A)
                echo "${EMOJI_GEAR} Stopping all servers..."
                kill_worldarchitect_servers true
                ;;
            s|S)
                echo ""
                echo "Enter PID to kill (or 'cancel'):"
                read -r pid_to_kill
                if [ "$pid_to_kill" != "cancel" ] && [ -n "$pid_to_kill" ]; then
                    if kill "$pid_to_kill" 2>/dev/null; then
                        echo "${EMOJI_CHECK} Killed process $pid_to_kill"
                    else
                        echo "${EMOJI_ERROR} Failed to kill process $pid_to_kill"
                    fi
                fi
                ;;
            *)
                echo "${EMOJI_INFO} Keeping existing servers running"
                ;;
        esac
        echo ""
    fi
}

# First, list current servers and offer cleanup
cleanup_servers

# Setup virtual environment
if ! detect_and_activate_venv; then
    exit 1
fi

# Use dynamic port - accept as argument or use default
PORT=${1:-$DEFAULT_FLASK_PORT}
echo "${EMOJI_TARGET} Using port $PORT (default: $DEFAULT_FLASK_PORT)"

# Ensure port is available
if ! ensure_port_free $PORT; then
    exit 1
fi

# Set environment variables (already set in server-config.sh, but ensure PORT is set)
export PORT=$PORT

# Setup logging
LOG_FILE=$(setup_logging "local-server")

print_server_config $PORT

# Ask about log capture options
echo "${EMOJI_INFO} Log Capture Options:"
echo "   [1] Run with logs displayed in terminal (default)"
echo "   [2] Run with logs saved to file"
echo "   [3] Run with logs displayed AND saved"
echo -n "   Choice (1-3, default 1): "
read -r log_choice

# Verify Flask server file exists
if [ ! -f "mvp_site/main.py" ]; then
    echo "${EMOJI_ERROR} ERROR: mvp_site/main.py not found!"
    echo "   Current directory: $(pwd)"
    echo "   Looking for: $(pwd)/mvp_site/main.py"
    exit 1
fi

# Start the server with appropriate logging
echo ""
echo "${EMOJI_ROCKET} Starting WorldArchitect.AI server..."
echo "   Press Ctrl+C to stop the server"
echo ""
echo "─────────────────────────────────────────"
echo ""

case "${log_choice:-1}" in
    2)
        echo "${EMOJI_INFO} Logs will be saved to: $LOG_FILE"
        echo ""
        $PYTHON_CMD mvp_site/main.py serve > "$LOG_FILE" 2>&1 &
        SERVER_PID=$!
        ;;
    3)
        echo "${EMOJI_INFO} Logs will be displayed AND saved to: $LOG_FILE"
        echo ""
        $PYTHON_CMD mvp_site/main.py serve 2>&1 | tee "$LOG_FILE" &
        SERVER_PID=$!
        ;;
    *)
        $PYTHON_CMD mvp_site/main.py serve &
        SERVER_PID=$!
        ;;
esac

# Wait for server to initialize
echo "${EMOJI_CLOCK} Waiting for server to initialize..."
sleep 3

# Parse PORT robustly to handle descriptive text
PARSED_PORT=$(parse_port_robust_bash "$PORT")

# Validate server startup
if validate_server $PARSED_PORT; then
    echo ""
    echo "${EMOJI_CHECK} SUCCESS: WorldArchitect.AI server is ready!"
    echo "${EMOJI_INFO} PID: $SERVER_PID"
    echo "${EMOJI_GEAR} To stop: kill $SERVER_PID"
    echo ""
    echo "Press Ctrl+C to stop the server or close this terminal"
    wait $SERVER_PID
else
    echo ""
    echo "${EMOJI_ERROR} FAILURE: Server validation failed"
    echo "${EMOJI_GEAR} Killing server process..."
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi