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
# NOTE: agent_monitor.py is a long-running service, so we don't use timeout on it
python3 agent_monitor.py > "$LOG_DIR/agent_monitor.log" 2>&1 &
MONITOR_PID=$!

# Wait for startup with timeout and verify process stays running
max_wait=5
wait_time=0
startup_verified=false

while [ $wait_time -lt $max_wait ]; do
    if kill -0 $MONITOR_PID 2>/dev/null; then
        # Process is running, wait a bit more to ensure it's stable
        if [ $wait_time -ge 2 ]; then
            # Check again after 2 seconds to ensure process didn't crash after startup
            sleep 1
            if kill -0 $MONITOR_PID 2>/dev/null; then
                startup_verified=true
                break
            else
                echo -e "${RED}❌ Agent monitor crashed after startup${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${RED}❌ Agent monitor failed to start or crashed immediately${NC}"
        exit 1
    fi
    sleep 1
    wait_time=$((wait_time + 1))
done

if [ "$startup_verified" = true ]; then
    echo -e "${GREEN}✅ Agent monitor started successfully (PID: $MONITOR_PID)${NC}"
    echo
    echo "Monitor commands:"
    echo "  📊 View logs:    tail -f $LOG_DIR/agent_monitor.log"
    echo "  🔍 Test ping:    python3 $SCRIPT_DIR/agent_monitor.py --once"
    echo "  🛑 Stop monitor: pkill -f agent_monitor.py"
    echo "  📋 Check status: pgrep -f agent_monitor.py"
    echo
    exit 0
else
    echo -e "${RED}❌ Failed to start agent monitor (timeout or startup failure)${NC}"
    exit 1
fi
