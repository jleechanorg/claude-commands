#!/bin/bash
# Start the agent monitoring coordinator
# This runs a lightweight Python process that monitors agents without LLM capabilities

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/tmp/orchestration_logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🤖 Starting Agent Monitor Coordinator${NC}"
echo -e "${YELLOW}📁 Logs: $LOG_DIR/agent_monitor.log${NC}"
echo -e "${YELLOW}🔍 Pings agents every 2 minutes${NC}"
echo -e "${YELLOW}📊 Uses A2A protocol for coordination${NC}"
echo

# Check if monitor is already running
if pgrep -f "agent_monitor.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Agent monitor already running${NC}"
    echo "   To stop: pkill -f agent_monitor.py"
    echo "   To view logs: tail -f $LOG_DIR/agent_monitor.log"
    exit 0
fi

# Start monitor in background
echo -e "${GREEN}🚀 Starting monitor...${NC}"
cd "$SCRIPT_DIR"

# Check if agent_monitor.py exists
if [ ! -f "agent_monitor.py" ]; then
    echo -e "${RED}❌ Error: agent_monitor.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Start monitor in background and redirect output to log file
python3 agent_monitor.py > "$LOG_DIR/agent_monitor.log" 2>&1 &
MONITOR_PID=$!

# Wait a moment and check if it started successfully
sleep 2
if kill -0 $MONITOR_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Agent monitor started successfully (PID: $MONITOR_PID)${NC}"
    echo
    echo "Monitor commands:"
    echo "  📊 View logs:    tail -f $LOG_DIR/agent_monitor.log"
    echo "  🔍 Test ping:    python3 $SCRIPT_DIR/agent_monitor.py --once"
    echo "  🛑 Stop monitor: pkill -f agent_monitor.py"
    echo "  📋 Check status: pgrep -f agent_monitor.py"
    echo
else
    echo -e "${RED}❌ Failed to start agent monitor${NC}"
    exit 1
fi
