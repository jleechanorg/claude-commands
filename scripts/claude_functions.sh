#!/bin/bash
set -euo pipefail

# Claude bot management functions
# Source this file to make functions available in current shell:
#   source scripts/claude_functions.sh

# Define color variables
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

    # Check if start script exists
    if [ -f "$SCRIPT_DIR/start-claude-bot.sh" ]; then
        echo -e "${BLUE}🚀 Starting Claude bot server in background...${NC}"

        # Start the server in background, redirecting output to log file
        nohup "$SCRIPT_DIR/start-claude-bot.sh" > "$HOME/.claude-bot-server.log" 2>&1 &

        # Store the PID
        echo $! > "$HOME/.claude-bot-server.pid"
        echo -e "${GREEN}✅ Claude bot server started with PID $!${NC}"
        echo -e "${BLUE}📋 Logs: tail -f $HOME/.claude-bot-server.log${NC}"
        return 0
    else
        echo -e "${RED}❌ start-claude-bot.sh not found in $SCRIPT_DIR${NC}"
        return 1
    fi
}

# Function to stop Claude bot server
stop_claude_bot() {
    if [ -f "$HOME/.claude-bot-server.pid" ]; then
        local PID=$(cat "$HOME/.claude-bot-server.pid")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${BLUE}🛑 Stopping Claude bot server (PID: $PID)...${NC}"
            kill "$PID"
            rm -f "$HOME/.claude-bot-server.pid"
            echo -e "${GREEN}✅ Claude bot server stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  Process not running, cleaning up PID file${NC}"
            rm -f "$HOME/.claude-bot-server.pid"
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

# Export functions for shell availability
export -f is_claude_bot_running start_claude_bot_background stop_claude_bot restart_claude_bot claude_bot_status
