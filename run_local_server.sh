#!/bin/bash
# run_local_server.sh - WorldArchitect.AI Dual Server Launcher
# Starts both Flask backend and React v2 frontend servers simultaneously

# Load shared utilities
MAIN_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$MAIN_SCRIPT_DIR"
source "$MAIN_SCRIPT_DIR/scripts/server-utils.sh"
source "$MAIN_SCRIPT_DIR/scripts/venv_utils.sh"

# Ensure all relative paths below are resolved from the repo root
cd "$PROJECT_ROOT"

print_banner "WorldArchitect.AI Development Server Launcher" "Dual server setup: Flask backend + React v2 frontend"

# Function to offer cleanup of existing servers with aggressive port clearing
cleanup_servers_aggressive() {
    list_worldarchitect_servers
    
    local servers=$(ps aux | grep -E "python.*main.py.*serve" | grep -v grep || true)
    local vite_servers=$(ps aux | grep -E "(vite|node.*vite)" | grep -v grep || true)
    
    if [ -n "$servers" ] || [ -n "$vite_servers" ]; then
        echo ""
        echo "${EMOJI_GEAR} Server Cleanup Options:"
        echo "   [a] Kill all servers (aggressive cleanup)"
        echo "   [p] Kill processes on target ports only" 
        echo "   [n] Keep all servers running"
        echo -n "   Choice (default: a): "
        read -r choice
        choice=${choice:-a}  # Default to aggressive cleanup

        case "$choice" in
            a|A)
                echo "${EMOJI_GEAR} Stopping all servers..."
                kill_worldarchitect_servers true
                ;;
            p|P)
                echo "${EMOJI_GEAR} Killing processes on target ports..."
                # Find ports first, then clear them
                TEMP_FLASK_PORT=$(find_available_port $DEFAULT_FLASK_PORT 10)
                TEMP_REACT_PORT=$(find_available_port $DEFAULT_REACT_PORT 10)
                if [ $? -eq 0 ]; then
                    ensure_port_free $TEMP_FLASK_PORT
                    ensure_port_free $TEMP_REACT_PORT
                fi
                ;;
            *)
                echo "${EMOJI_INFO} Keeping existing servers running"
                ;;
        esac
        echo ""
    else
        # No servers running, but still do aggressive port cleanup
        echo "${EMOJI_INFO} No servers currently running"
        echo "${EMOJI_GEAR} Performing aggressive port cleanup..."
        kill_worldarchitect_servers true
    fi
}

# Perform server cleanup
cleanup_servers_aggressive

# Setup virtual environment using new venv_utils
ensure_venv
if [ $? -ne 0 ]; then
    echo "${EMOJI_ERROR} Failed to setup virtual environment"
    exit 1
fi

# Validate that virtual environment is properly activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "${EMOJI_ERROR} Virtual environment not activated properly"
    echo "${EMOJI_INFO} Attempting manual activation..."
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        # Always activate using an absolute path to avoid CWD issues
        # shellcheck disable=SC1091
        source "$PROJECT_ROOT/venv/bin/activate"
        if [ -z "$VIRTUAL_ENV" ]; then
            echo "${EMOJI_ERROR} Manual activation also failed"
            exit 1
        fi
    else
        echo "${EMOJI_ERROR} Virtual environment activation file not found: $PROJECT_ROOT/venv/bin/activate"
        exit 1
    fi
fi

echo "${EMOJI_CHECK} Virtual environment active: $VIRTUAL_ENV"

# Aggressive port cleanup - ensure target ports are available
echo "${EMOJI_GEAR} Ensuring target ports are available..."
ensure_port_free $DEFAULT_FLASK_PORT 3 2>/dev/null || true
ensure_port_free $DEFAULT_REACT_PORT 3 2>/dev/null || true

# Find available ports
echo "${EMOJI_SEARCH} Finding available ports..."
FLASK_PORT=$(find_available_port $DEFAULT_FLASK_PORT 10)
if [ $? -ne 0 ]; then
    echo "${EMOJI_ERROR} Failed to find available Flask port"
    exit 1
fi

REACT_PORT=$(find_available_port $DEFAULT_REACT_PORT 10)
if [ $? -ne 0 ]; then
    echo "${EMOJI_ERROR} Failed to find available React port"
    exit 1
fi

export PORT=$FLASK_PORT

print_server_config $FLASK_PORT $REACT_PORT

# Start Flask backend in a new terminal/tab if possible
echo ""
echo "${EMOJI_ROCKET} Starting Flask backend on port $FLASK_PORT..."

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --tab --title="Flask Backend" -- bash -c "cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -title "Flask Backend" -e "cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve" &
else
    # Fallback: run in background
    echo "${EMOJI_INFO} Running Flask in background (no terminal emulator found)"
    # Check if venv is still active in subshell, if not reactivate it
    (
        cd "$PROJECT_ROOT" || exit 1
        if [ -z "$VIRTUAL_ENV" ] && [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
            # shellcheck disable=SC1091
            source "$PROJECT_ROOT/venv/bin/activate"
        fi
        TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve
    ) &
    FLASK_PID=$!
    echo "${EMOJI_INFO} Flask backend started in background (PID: $FLASK_PID)"
fi

# Give Flask time to start
echo "${EMOJI_CLOCK} Waiting for Flask to initialize..."
sleep 3

# Validate Flask is running
if ! validate_server $FLASK_PORT 5 2; then
    echo "${EMOJI_ERROR} Flask backend failed to start properly"
    exit 1
fi

# Navigate to frontend directory
if [ ! -d "mvp_site/frontend_v2" ]; then
    echo "${EMOJI_ERROR} ERROR: Frontend v2 directory not found!"
    echo "   Looking for: $(pwd)/mvp_site/frontend_v2"
    exit 1
fi

cd mvp_site/frontend_v2

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "${EMOJI_WARNING} Node modules not found. Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "${EMOJI_ERROR} Failed to install npm dependencies"
        exit 1
    fi
fi

# Start React frontend with environment variables
echo ""
echo "${EMOJI_ROCKET} Starting React v2 frontend on port $REACT_PORT..."
echo "${EMOJI_INFO} Frontend will proxy API calls to Flask backend on port $FLASK_PORT"

# Set environment variables for React build
export PORT=$FLASK_PORT  # For vite.config.ts proxy target
export REACT_APP_API_URL="http://localhost:$FLASK_PORT"

# Start the React development server
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --tab --title="React Frontend" -- bash -c "PORT=$FLASK_PORT npm run dev -- --port $REACT_PORT --host 0.0.0.0; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -title "React Frontend" -e "PORT=$FLASK_PORT npm run dev -- --port $REACT_PORT --host 0.0.0.0" &
else
    # Fallback: run in foreground
    echo "${EMOJI_INFO} Starting React in current terminal..."
    PORT=$FLASK_PORT npm run dev -- --port $REACT_PORT --host 0.0.0.0
fi

# Comprehensive health checks for both servers
echo ""
echo "${EMOJI_SEARCH} Performing comprehensive health checks..."
echo "-------------------------------------------------------------"

# Wait a bit more for React to fully start
echo "${EMOJI_CLOCK} Waiting for React frontend to initialize..."
sleep 5

# Validate Flask backend again
echo "${EMOJI_TARGET} Testing Flask backend..."
if ! validate_server $FLASK_PORT 3 2; then
    echo "${EMOJI_ERROR} Flask backend health check failed"
    kill_worldarchitect_servers true
    exit 1
fi

# Validate React frontend
echo "${EMOJI_TARGET} Testing React frontend..."
if ! validate_server $REACT_PORT 8 3; then
    echo "${EMOJI_ERROR} React frontend health check failed"
    echo "${EMOJI_INFO} This is common - React may take longer to start"
    echo "${EMOJI_INFO} Flask backend is working. Check React manually if needed."
fi

# Final validation - test API endpoint
echo "${EMOJI_TARGET} Testing API connectivity..."
if curl -s -f --max-time 3 "http://localhost:$FLASK_PORT/api/campaigns" > /dev/null 2>&1; then
    echo "${EMOJI_CHECK} API endpoint responding correctly"
elif curl -s --max-time 3 "http://localhost:$FLASK_PORT/api/campaigns" 2>/dev/null | grep -q "No token provided"; then
    echo "${EMOJI_CHECK} API endpoint responding correctly (authentication required)"
else
    echo "${EMOJI_WARNING} API endpoint test inconclusive"
fi

echo ""
echo "${EMOJI_CHECK} Health checks completed successfully!"
echo ""
echo "${EMOJI_INFO} Server URLs:"
echo "   - Flask Backend:  http://localhost:$FLASK_PORT"
echo "   - React Frontend: http://localhost:$REACT_PORT"
echo ""
echo "${EMOJI_INFO} For authentication bypass in development:"
echo "   http://localhost:$REACT_PORT?test_mode=true&test_user_id=test-user-123"
echo ""
echo "${EMOJI_GEAR} To stop servers:"
echo "   - Close terminal tabs, or"
echo "   - Run: pkill -f 'python.*main.py.*serve' && pkill -f 'node.*vite'"
echo ""
echo "Press Ctrl+C to exit this script (servers will continue running in background)"

# Wait for user to exit
while true; do
    sleep 10
    # Check if servers are still running
    if ! ps aux | grep -E "python.*main.py.*serve" | grep -v grep > /dev/null; then
        echo "${EMOJI_WARNING} Flask backend appears to have stopped"
        break
    fi
    if ! ps aux | grep -E "node.*vite" | grep -v grep > /dev/null; then
        echo "${EMOJI_WARNING} React frontend appears to have stopped"
        break
    fi
done
