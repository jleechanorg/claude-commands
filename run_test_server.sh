#!/bin/bash
# run_test_server.sh - Start/stop the Flask test server for WorldArchitect.AI
# Usage: ./run_test_server.sh [start|stop|status|restart]

set -e

# Configuration
TEST_PORT=6006
PID_FILE="/tmp/worldarchitectai_test_server.pid"
LOG_FILE="/tmp/worldarchitectai_test_server.log"
VENV_PATH="venv/bin/activate"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if server is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
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
    
    # Clean up any existing processes on the port
    echo "🧹 Cleaning up port $TEST_PORT..."
    lsof -ti:$TEST_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
    
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
    export USE_MOCKS=true  # Change to false for real APIs
    
    echo "📝 Environment variables set:"
    echo "   TESTING=$TESTING"
    echo "   PORT=$PORT"
    echo "   USE_MOCKS=$USE_MOCKS"
    
    # Start the server in background
    echo "🏃 Starting server on port $TEST_PORT..."
    nohup python3 mvp_site/main.py serve > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # Save PID
    echo $SERVER_PID > "$PID_FILE"
    
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
        PID=$(cat "$PID_FILE")
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
    
    # Also clean up any processes on the port
    lsof -ti:$TEST_PORT | xargs kill -9 2>/dev/null || true
}

# Function to check server status
check_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ Server is running${NC}"
        echo "   PID: $PID"
        echo "   URL: http://localhost:$TEST_PORT"
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