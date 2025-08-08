#!/bin/bash
# run_local_server.sh - WorldArchitect.AI Dual Server Launcher
# Starts both Flask backend and React v2 frontend servers simultaneously

# Load shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
source "$SCRIPT_DIR/scripts/server-utils.sh"
source "$SCRIPT_DIR/scripts/venv_utils.sh"

print_banner "WorldArchitect.AI Development Server Launcher" "Dual server setup: Flask backend + React v2 frontend"

# Kill any existing server processes
kill_worldarchitect_servers true

# Setup virtual environment using new venv_utils
ensure_venv

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
    gnome-terminal --tab --title="Flask Backend" -- bash -c "source venv/bin/activate && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -title "Flask Backend" -e "source venv/bin/activate && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve" &
else
    # Fallback: run in background
    echo "${EMOJI_INFO} Running Flask in background (no terminal emulator found)"
    (source venv/bin/activate && TESTING=true PORT=$FLASK_PORT python mvp_site/main.py serve) &
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

echo ""
echo "${EMOJI_CHECK} Development servers launched successfully!"
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
