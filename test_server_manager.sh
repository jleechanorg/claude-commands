#!/bin/bash
# test_server_manager.sh - Manage multiple test servers for different branches
# Usage: ./test_server_manager.sh [start|stop|list|cleanup] [branch_name]

set -e

# Configuration
BASE_PORT=8081
MAX_SERVERS=10
PID_DIR="/tmp/worldarchitectai_servers"
LOG_DIR="/tmp/worldarchitectai_logs"
VENV_PATH="venv/bin/activate"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directories if they don't exist
mkdir -p "$PID_DIR" "$LOG_DIR"

# Function to find available port
find_available_port() {
    local port=$BASE_PORT
    while [ $port -lt $((BASE_PORT + MAX_SERVERS)) ]; do
        if ! lsof -i:$port > /dev/null 2>&1; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    echo "ERROR: No available ports in range $BASE_PORT-$((BASE_PORT + MAX_SERVERS))" >&2
    return 1
}

# Function to get branch-specific files
get_branch_files() {
    local branch_name="$1"
    local safe_branch_name=$(echo "$branch_name" | sed 's/[^a-zA-Z0-9_-]/_/g')

    export BRANCH_PID_FILE="$PID_DIR/${safe_branch_name}.pid"
    export BRANCH_LOG_FILE="$LOG_DIR/${safe_branch_name}.log"
    export BRANCH_PORT_FILE="$PID_DIR/${safe_branch_name}.port"
}

# Function to check if server is running for a branch
is_branch_running() {
    local branch_name="$1"
    get_branch_files "$branch_name"

    if [ -f "$BRANCH_PID_FILE" ]; then
        PID=$(cat "$BRANCH_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # Clean up stale files
            rm -f "$BRANCH_PID_FILE" "$BRANCH_PORT_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start server for a branch
start_server() {
    local branch_name="$1"
    get_branch_files "$branch_name"

    if is_branch_running "$branch_name"; then
        local port=$(cat "$BRANCH_PORT_FILE")
        echo -e "${YELLOW}⚠️  Server for branch '$branch_name' is already running on port $port${NC}"
        return 0
    fi

    # Find available port
    local port=$(find_available_port)
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Cannot start server: $port${NC}"
        return 1
    fi

    echo -e "${GREEN}🚀 Starting server for branch '$branch_name' on port $port${NC}"

    # Activate virtual environment
    if [ -f "$VENV_PATH" ]; then
        source "$VENV_PATH"
    else
        echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
        return 1
    fi

    # Set environment variables
    export TESTING=true
    export PORT=$port
    export USE_MOCKS=false
    export BRANCH_NAME="$branch_name"

    # Start the server in background
    nohup python3 mvp_site/main.py serve > "$BRANCH_LOG_FILE" 2>&1 &
    local server_pid=$!

    # Save PID and port
    echo $server_pid > "$BRANCH_PID_FILE"
    echo $port > "$BRANCH_PORT_FILE"

    # Wait for server to be ready
    echo "⏳ Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -s "http://localhost:$port" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server ready for branch '$branch_name'${NC}"
            echo "   URL: http://localhost:$port"
            echo "   PID: $server_pid"
            echo "   Log: $BRANCH_LOG_FILE"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo -e "${RED}❌ Server failed to start${NC}"
    kill $server_pid 2>/dev/null || true
    rm -f "$BRANCH_PID_FILE" "$BRANCH_PORT_FILE"
    return 1
}

# Function to stop server for a branch
stop_server() {
    local branch_name="$1"
    get_branch_files "$branch_name"

    if is_branch_running "$branch_name"; then
        local pid=$(cat "$BRANCH_PID_FILE")
        local port=$(cat "$BRANCH_PORT_FILE")

        echo -e "${YELLOW}🛑 Stopping server for branch '$branch_name' (PID: $pid, Port: $port)${NC}"

        kill $pid 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -9 $pid 2>/dev/null || true
        fi

        rm -f "$BRANCH_PID_FILE" "$BRANCH_PORT_FILE"
        echo -e "${GREEN}✅ Server stopped for branch '$branch_name'${NC}"
    else
        echo -e "${YELLOW}⚠️  No server running for branch '$branch_name'${NC}"
    fi
}

# Function to list all running servers
list_servers() {
    echo -e "${BLUE}📋 Running Test Servers${NC}"
    echo "===================="

    local found_servers=false
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local branch_name=$(basename "$pid_file" .pid)
            if is_branch_running "$branch_name"; then
                local pid=$(cat "$pid_file")
                local port=$(cat "$PID_DIR/$branch_name.port")
                echo -e "${GREEN}✅ $branch_name${NC}"
                echo "   PID: $pid"
                echo "   Port: $port"
                echo "   URL: http://localhost:$port"
                echo "   Log: $LOG_DIR/$branch_name.log"
                echo
                found_servers=true
            fi
        fi
    done

    if [ "$found_servers" = false ]; then
        echo -e "${YELLOW}No servers currently running${NC}"
    fi
}

# Function to cleanup all servers
cleanup_servers() {
    echo -e "${YELLOW}🧹 Cleaning up all test servers${NC}"

    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local branch_name=$(basename "$pid_file" .pid)
            stop_server "$branch_name"
        fi
    done

    # Also clean up any stray processes
    pkill -f "mvp_site/main.py" 2>/dev/null || true

    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Main script logic
case "${1:-help}" in
    start)
        if [ -z "$2" ]; then
            # Use current branch if no branch specified
            branch_name=$(git branch --show-current)
        else
            branch_name="$2"
        fi
        start_server "$branch_name"
        ;;
    stop)
        if [ -z "$2" ]; then
            # Use current branch if no branch specified
            branch_name=$(git branch --show-current)
        else
            branch_name="$2"
        fi
        stop_server "$branch_name"
        ;;
    list)
        list_servers
        ;;
    cleanup)
        cleanup_servers
        ;;
    *)
        echo "Usage: $0 {start|stop|list|cleanup} [branch_name]"
        echo ""
        echo "Commands:"
        echo "  start [branch]  - Start test server for branch (defaults to current branch)"
        echo "  stop [branch]   - Stop test server for branch (defaults to current branch)"
        echo "  list            - List all running test servers"
        echo "  cleanup         - Stop all test servers"
        echo ""
        echo "Examples:"
        echo "  $0 start                    # Start server for current branch"
        echo "  $0 start feature-auth       # Start server for feature-auth branch"
        echo "  $0 stop                     # Stop server for current branch"
        echo "  $0 list                     # Show all running servers"
        echo "  $0 cleanup                  # Stop all servers"
        exit 1
        ;;
esac
