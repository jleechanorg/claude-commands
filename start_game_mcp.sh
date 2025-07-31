#!/bin/bash
# WorldArchitect.AI Game MCP Server startup script
# Starts the game MCP server on port 7000 with proper error handling and logging

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_PORT=7000
MCP_HOST="localhost"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SCRIPT="$SCRIPT_DIR/mvp_site/mcp_api.py"

# Get current git branch for log directory
CURRENT_BRANCH=$(git -C "$SCRIPT_DIR" branch --show-current 2>/dev/null || echo "unknown")
LOG_DIR="/tmp/worldarchitect.ai/${CURRENT_BRANCH}"
PID_FILE="$LOG_DIR/game-mcp-server.pid"
LOG_FILE="$LOG_DIR/game-mcp-server.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to check if MCP server is running
is_game_mcp_running() {
    if curl -s "http://$MCP_HOST:$MCP_PORT/health" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start MCP server in background
start_game_mcp_background() {
    # Check if MCP script exists
    if [ ! -f "$MCP_SCRIPT" ]; then
        echo -e "${RED}❌ MCP script not found at $MCP_SCRIPT${NC}"
        return 1
    fi

    # Check if virtual environment is activated or available
    if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        echo -e "${RED}❌ Python virtual environment not found at $SCRIPT_DIR/venv${NC}"
        return 1
    fi

    echo -e "${BLUE}🚀 Starting Game MCP server on port $MCP_PORT...${NC}"

    # Start the MCP server in background with proper environment
    (
        source "$SCRIPT_DIR/venv/bin/activate"
        cd "$SCRIPT_DIR" || exit 1
        python "$MCP_SCRIPT" --port "$MCP_PORT" --host "$MCP_HOST" > "$LOG_FILE" 2>&1 &
        local PID=$!
        echo $PID > "$PID_FILE"
    )

    # Wait a moment for startup
    sleep 3

    return 0
}

# Function to stop MCP server
stop_game_mcp() {
    if [ -f "$PID_FILE" ]; then
        local PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${BLUE}🛑 Stopping Game MCP server (PID: $PID)...${NC}"
            kill "$PID"
            rm -f "$PID_FILE"
            echo -e "${GREEN}✅ Game MCP server stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  Process not running, cleaning up PID file${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found${NC}"
    fi
}

# Function to restart MCP server
restart_game_mcp() {
    echo -e "${BLUE}🔄 Restarting Game MCP server...${NC}"
    stop_game_mcp
    sleep 2
    start_game_mcp_background
    sleep 3
    if is_game_mcp_running; then
        echo -e "${GREEN}✅ Game MCP server restarted successfully${NC}"
    else
        echo -e "${RED}❌ Failed to restart Game MCP server${NC}"
    fi
}

# Function to show MCP server status
game_mcp_status() {
    if is_game_mcp_running; then
        echo -e "${GREEN}✅ Game MCP server is running on port $MCP_PORT${NC}"
        if [ -f "$PID_FILE" ]; then
            local PID=$(cat "$PID_FILE")
            echo -e "${BLUE}📋 PID: $PID${NC}"
        fi
        echo -e "${BLUE}📋 Health check: curl http://$MCP_HOST:$MCP_PORT/health${NC}"
        echo -e "${BLUE}📋 JSON-RPC endpoint: http://$MCP_HOST:$MCP_PORT/rpc${NC}"
    else
        echo -e "${RED}❌ Game MCP server is not running${NC}"
    fi
}

# Main execution logic
case "${1:-start}" in
    start)
        if is_game_mcp_running; then
            echo -e "${GREEN}✅ Game MCP server already running on port $MCP_PORT${NC}"
        else
            echo -e "${YELLOW}⚠️  Game MCP server not running${NC}"

            if start_game_mcp_background; then
                # Give it a moment to start up
                sleep 2

                if is_game_mcp_running; then
                    echo -e "${GREEN}✅ Game MCP server started successfully${NC}"
                    echo -e "${BLUE}📋 Server info:${NC}"
                    echo -e "   • Health check: http://$MCP_HOST:$MCP_PORT/health"
                    echo -e "   • JSON-RPC endpoint: http://$MCP_HOST:$MCP_PORT/rpc"
                    echo -e "   • Log file: $LOG_FILE"
                    echo -e "   • PID file: $PID_FILE"
                    echo -e "   • Available tools: create_campaign, get_campaign_state, process_action, etc."
                else
                    echo -e "${RED}❌ Failed to start Game MCP server${NC}"
                    echo -e "${BLUE}💡 Check log: tail -f $LOG_FILE${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️  Could not start Game MCP server${NC}"
            fi
        fi
        ;;
    stop)
        stop_game_mcp
        ;;
    restart)
        restart_game_mcp
        ;;
    status)
        game_mcp_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Game MCP Server Management:"
        echo "  start   - Start the MCP server (default)"
        echo "  stop    - Stop the MCP server"
        echo "  restart - Restart the MCP server"
        echo "  status  - Show server status"
        exit 1
        ;;
esac

# Export functions so they're available in the shell
export -f stop_game_mcp restart_game_mcp game_mcp_status is_game_mcp_running start_game_mcp_background
