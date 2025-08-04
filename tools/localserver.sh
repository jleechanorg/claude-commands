#!/bin/bash

# localserver.sh - Start a local WorldArchitect.AI server on an available port
# This script finds an available port starting from 8081 and runs the Flask server

set -e  # Exit on error

echo "🚀 WorldArchitect.AI Local Server Launcher"
echo "=========================================="

# Function to list all running servers
list_servers() {
    echo ""
    echo "📊 Currently Running Servers:"
    echo "-----------------------------"

    # Find all Python processes running main.py
    local servers=$(ps aux | grep -E "python.*main.py.*serve" | grep -v grep || true)

    if [ -z "$servers" ]; then
        echo "✅ No WorldArchitect.AI servers currently running"
    else
        echo "$servers" | while read -r line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')

            # Try to find the port
            local port=$(lsof -p $pid 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
            if [ -z "$port" ]; then
                # Try to extract PORT from command
                port=$(echo "$cmd" | grep -oP 'PORT=\K\d+' || echo "unknown")
            fi

            echo "🔹 PID: $pid | Port: $port"
            echo "   Command: $cmd"
            echo "   Worktree: $(echo "$line" | grep -oP '/worktree_\w+/' | sed 's/\///' || echo "main")"
            echo ""
        done
    fi
}

# Function to offer cleanup
cleanup_servers() {
    local servers=$(ps aux | grep -E "python.*main.py.*serve" | grep -v grep || true)

    if [ -n "$servers" ]; then
        echo ""
        echo "🧹 Server Cleanup Options:"
        echo "   [a] Kill all servers"
        echo "   [s] Select specific server to kill"
        echo "   [n] Keep all servers running"
        echo -n "   Choice: "
        read -r choice

        case "$choice" in
            a|A)
                echo "🔄 Stopping all servers..."
                pkill -f "python.*main.py.*serve" || true
                sleep 2
                echo "✅ All servers stopped"
                ;;
            s|S)
                echo ""
                echo "Enter PID to kill (or 'cancel'):"
                read -r pid_to_kill
                if [ "$pid_to_kill" != "cancel" ] && [ -n "$pid_to_kill" ]; then
                    if kill "$pid_to_kill" 2>/dev/null; then
                        echo "✅ Killed process $pid_to_kill"
                    else
                        echo "❌ Failed to kill process $pid_to_kill"
                    fi
                fi
                ;;
            *)
                echo "👍 Keeping existing servers running"
                ;;
        esac
        echo ""
    fi
}

# First, list current servers
list_servers

# Offer cleanup if servers are running
cleanup_servers

# Check if we're in a git worktree and find venv
VENV_PATH=""
if [ -f ".git" ] && grep -q "gitdir:" .git 2>/dev/null; then
    echo "📁 Detected git worktree environment"
    GITDIR=$(grep gitdir: .git | cut -d' ' -f2)
    # Extract the main project directory from the worktree path
    # /home/jleechan/projects/worldarchitect.ai/.git/worktrees/worktree_worker3
    # becomes /home/jleechan/projects/worldarchitect.ai
    MAIN_PROJECT_DIR=$(echo "$GITDIR" | sed 's/\.git\/worktrees\/.*//')
    if [ -f "$MAIN_PROJECT_DIR/venv/bin/activate" ]; then
        echo "✅ Found venv in main project: $MAIN_PROJECT_DIR/venv"
        VENV_PATH="$MAIN_PROJECT_DIR/venv/bin/activate"
    fi
fi

# Function to kill processes using a specific port
kill_port_processes() {
    local port=$1
    echo "🔍 Checking for processes using port $port..."

    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "⚔️  Attempting graceful shutdown of processes using port $port: $pids"
        # Try graceful termination first (SIGTERM)
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2

        # Check if processes are still running
        local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo "⚔️  Forcefully killing remaining processes: $remaining_pids"
            echo "$remaining_pids" | xargs kill -9 2>/dev/null || true
            sleep 1
        fi

        # Verify port is now free
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            echo "❌ ERROR: Port $port still in use after kill attempts (processes may be permission-protected)"
            return 1
        else
            echo "✅ Port $port is now free"
            return 0
        fi
    else
        echo "✅ Port $port is already free"
        return 0
    fi
}

# Function to ensure port is available (kill if necessary)
ensure_port_free() {
    local port=$1
    echo "🎯 Ensuring port $port is available..."

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  Port $port is in use, killing conflicting processes..."
        if ! kill_port_processes $port; then
            echo "❌ CRITICAL: Failed to free port $port. Cannot continue."
            echo "   Please manually kill processes using port $port and try again."
            return 1
        fi
    else
        echo "✅ Port $port is already free"
    fi
    return 0
}

# Check for virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "🐍 Activating local virtual environment..."
    source venv/bin/activate
    PYTHON_CMD="python"
elif [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH" ]; then
    echo "🐍 Activating main project virtual environment..."
    source "$VENV_PATH"
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    echo "⚠️  No virtual environment found, using system Python3"
    PYTHON_CMD="python3"

    # Check if Flask is available
    if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
        echo "❌ ERROR: Flask is not installed and no virtual environment found"
        echo ""
        echo "📚 To set up the environment, run:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r mvp_site/requirements.txt"
        echo ""
        echo "Or for quick testing without venv:"
        echo "   pip3 install --user -r mvp_site/requirements.txt"
        echo ""
        exit 1
    fi
else
    echo "❌ ERROR: Python3 not found"
    exit 1
fi

# Use fixed port and ensure it's available
PORT=5005
ensure_port_free $PORT

# Set environment variables
export TESTING=true
export PORT=$PORT
export FLASK_ENV=development
export PYTHONUNBUFFERED=1

# Display server info
echo ""
echo "📋 Server Configuration:"
echo "   - Port: $PORT"
echo "   - URL: http://localhost:$PORT"
echo "   - Mode: Testing (TESTING=true)"
echo "   - Python: $PYTHON_CMD"
echo "   - Working Directory: $(pwd)"
echo ""

# Add test mode parameters info
echo "💡 Test Mode Access:"
echo "   For authenticated access without sign-in:"
echo "   http://localhost:$PORT?test_mode=true&test_user_id=test-user-123"
echo ""

# Start the server
echo "🚀 Starting WorldArchitect.AI server..."
echo "   Press Ctrl+C to stop the server"
echo ""
echo "─────────────────────────────────────────"
echo ""

# Ask about log capture
echo "📝 Log Capture Options:"
echo "   [1] Run with logs displayed in terminal (default)"
echo "   [2] Run with logs saved to file"
echo "   [3] Run with logs displayed AND saved"
echo -n "   Choice (1-3, default 1): "
read -r log_choice

# Get standardized log directory with branch isolation
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
LOG_DIR="/tmp/worldarchitect.ai/${CURRENT_BRANCH}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/local-server_$(date +%Y%m%d_%H%M%S).log"

# Function to validate server with curl
validate_server() {
    local port=$1
    local max_attempts=10
    local attempt=1

    echo ""
    echo "🔍 Validating server startup with curl..."
    echo "─────────────────────────────────────────"

    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: Testing http://localhost:$port/"

        if curl -s -f "http://localhost:$port/" > /dev/null; then
            echo "✅ Server is responding correctly!"
            echo "🌐 Server URL: http://localhost:$port/"
            echo "🔬 Test Mode URL: http://localhost:$port/?test_mode=true&test_user_id=test-user-123"
            return 0
        else
            echo "❌ Server not responding yet, waiting 2 seconds..."
            sleep 2
            ((attempt++))
        fi
    done

    echo "❌ ERROR: Server failed to respond after $max_attempts attempts"
    echo "🔍 Checking if server process is still running..."
    if ps aux | grep -E "python.*main.py.*serve" | grep -v grep > /dev/null; then
        echo "⚠️  Server process is running but not responding to HTTP requests"
        echo "📋 Check the server logs for errors"
    else
        echo "💀 Server process has died"
    fi
    return 1
}

# Run the server with better error handling and validation
if [ -f "mvp_site/main.py" ]; then
    case "${log_choice:-1}" in
        2)
            echo "📄 Logs will be saved to: $LOG_FILE"
            echo ""
            $PYTHON_CMD mvp_site/main.py serve > "$LOG_FILE" 2>&1 &
            SERVER_PID=$!
            ;;
        3)
            echo "📄 Logs will be displayed AND saved to: $LOG_FILE"
            echo ""
            $PYTHON_CMD mvp_site/main.py serve 2>&1 | tee "$LOG_FILE" &
            SERVER_PID=$!
            ;;
        *)
            $PYTHON_CMD mvp_site/main.py serve &
            SERVER_PID=$!
            ;;
    esac

    # Wait a moment for server to start
    echo "⏳ Waiting for server to initialize..."
    sleep 3

    # Validate server startup
    if validate_server $PORT; then
        echo ""
        echo "🎉 SUCCESS: WorldArchitect.AI server is ready!"
        echo "📍 PID: $SERVER_PID"
        echo "🛑 To stop: kill $SERVER_PID"
        echo ""
        echo "Press Ctrl+C to stop the server or close this terminal"
        wait $SERVER_PID
    else
        echo ""
        echo "💥 FAILURE: Server validation failed"
        echo "🔪 Killing server process..."
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
else
    echo "❌ ERROR: mvp_site/main.py not found!"
    echo "   Current directory: $(pwd)"
    echo "   Looking for: $(pwd)/mvp_site/main.py"
    exit 1
fi
