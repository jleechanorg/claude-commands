#!/bin/bash
# run_test_server.sh - Start/stop the Flask test server for WorldArchitect.AI
# Usage: ./run_test_server.sh [start|stop|status|restart]

set -e

# Configuration
PID_FILE="/tmp/worldarchitectai_test_server.pid"
LOG_FILE="/tmp/worldarchitectai_test_server.log"
VENV_PATH="venv/bin/activate"

# Source shared port utilities
source "$(dirname "$0")/claude_command_scripts/port-utils.sh"

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID_PORT=$(cat "$PID_FILE")
        PID=$(echo "$PID_PORT" | cut -d: -f1)
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is not running
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the server
start_server() {
    echo -e "${GREEN}🚀 Starting WorldArchitect.AI Test Server${NC}"
    
    # Check if already running
    if is_running; then
        echo -e "${YELLOW}⚠️  Server is already running (PID: $(cat $PID_FILE))${NC}"
        return 1
    fi
    
    # Find available port
    echo "🔍 Finding available port..."
    TEST_PORT=$(find_available_port)
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Could not find available port${NC}"
        return 1
    fi
    echo "✅ Found available port: $TEST_PORT"
    
    # Update log file name to include port
    LOG_FILE="/tmp/worldarchitectai_test_server_$TEST_PORT.log"
    
    # Activate virtual environment
    if [ -f "$VENV_PATH" ]; then
        echo "🔧 Activating virtual environment..."
        source "$VENV_PATH"
    else
        echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
        exit 1
    fi
    
    # Set environment variables
    export TESTING=true
    export PORT=$TEST_PORT
    export USE_MOCKS=false  # Change to true for mock APIs
    
    echo "📝 Environment variables set:"
    echo "   TESTING=$TESTING"
    echo "   PORT=$PORT ($TEST_PORT)"
    echo "   USE_MOCKS=$USE_MOCKS"
    
    # Start the server in background
    echo "🏃 Starting server on port $TEST_PORT..."
    nohup python3 mvp_site/main.py serve > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # Save PID and port info
    echo "$SERVER_PID:$TEST_PORT" > "$PID_FILE"
    
    # Wait for server to be ready
    echo "⏳ Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -s "http://localhost:$TEST_PORT" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}"
            echo "   PID: $SERVER_PID"
            echo "   URL: http://localhost:$TEST_PORT"
            echo "   Log: $LOG_FILE"
            return 0
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Server failed to start within 30 seconds${NC}"
            echo "📋 Last 20 lines of log:"
            tail -20 "$LOG_FILE"
            # Clean up
            kill $SERVER_PID 2>/dev/null || true
            rm -f "$PID_FILE"
            return 1
        fi
        sleep 1
        echo -n "."
    done
    echo
}

# Function to stop the server
stop_server() {
    echo -e "${YELLOW}🛑 Stopping WorldArchitect.AI Test Server${NC}"
    
    if is_running; then
        PID_PORT=$(cat "$PID_FILE")
        PID=$(echo "$PID_PORT" | cut -d: -f1)
        echo "   Killing process $PID..."
        kill $PID 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "   Force killing process $PID..."
            kill -9 $PID 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
        echo -e "${GREEN}✅ Server stopped${NC}"
    else
        echo "⚠️  Server is not running"
    fi
    
    # Also clean up any processes on ports 8081-8090 range
    for port in $(seq $BASE_PORT $((BASE_PORT + MAX_PORTS - 1))); do
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    done
}

# Function to check server status
check_status() {
    if is_running; then
        PID_PORT=$(cat "$PID_FILE")
        PID=$(echo "$PID_PORT" | cut -d: -f1)
        STORED_PORT=$(echo "$PID_PORT" | cut -d: -f2)
        LOG_FILE="/tmp/worldarchitectai_test_server_$STORED_PORT.log"
        
        echo -e "${GREEN}✅ Server is running${NC}"
        echo "   PID: $PID"
        echo "   Port: $STORED_PORT"
        echo "   URL: http://localhost:$STORED_PORT"
        echo "   Log: $LOG_FILE"
        
        # Show recent log entries
        echo ""
        echo "📋 Recent log entries:"
        tail -5 "$LOG_FILE"
    else
        echo -e "${RED}❌ Server is not running${NC}"
    fi
}

# Function to restart the server
restart_server() {
    echo "🔄 Restarting server..."
    stop_server
    sleep 2
    start_server
}

# Main script logic
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        check_status
        ;;
    restart)
        restart_server
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the test server"
        echo "  stop     - Stop the test server"
        echo "  status   - Check if server is running"
        echo "  restart  - Stop and start the server"
        echo ""
        echo "Default: start"
        exit 1
        ;;
esac