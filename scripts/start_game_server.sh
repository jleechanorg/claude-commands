#!/bin/bash
# Start the WorldArchitect Game MCP Server

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🎮 Starting WorldArchitect Game MCP Server...${NC}"

# Navigate to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run setup first.${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Flask not installed. Installing dependencies...${NC}"
    pip install flask flask-cors
fi

# Kill any existing server on port 7000
if lsof -Pi :7000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Killing existing server on port 7000...${NC}"
    PIDS="$(lsof -Pi :7000 -sTCP:LISTEN -t)"
    if [[ -n "$PIDS" && "$PIDS" =~ ^[0-9\ ]+$ ]]; then
        kill $PIDS 2>/dev/null
        sleep 2
    else
        echo -e "${RED}❌ Could not determine valid PID(s) to kill.${NC}"
    fi
fi

# Start the server
export GAME_SERVER_PORT=7000
echo -e "${GREEN}🚀 Starting server on port $GAME_SERVER_PORT...${NC}"

if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    # Start in background with dual transport (default)
    nohup python mvp_site/mcp_api.py > /tmp/worldarchitect_game_server.log 2>&1 &
    SERVER_PID=$!
    sleep 2
    
    # Check if server started successfully
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Server started in background (PID: $SERVER_PID)${NC}"
        echo -e "${GREEN}📝 Logs: /tmp/worldarchitect_game_server.log${NC}"
        echo $SERVER_PID > /tmp/worldarchitect_game_server.pid
    else
        echo -e "${RED}❌ Failed to start server${NC}"
        exit 1
    fi
else
    # Start in foreground with dual transport (default)
    python mvp_site/mcp_api.py
fi