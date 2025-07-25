#!/bin/bash
# Usage: ./orch_direct.sh "task description"

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Error: No task provided${NC}"
    echo "Usage: $0 \"task description\""
    exit 1
fi

TASK="$1"
SESSION_NAME="task-direct-$(date +%s | tail -c 5)"
WORK_DIR="${WORK_DIR:-$(pwd)}"

echo -e "${GREEN}🚀 Starting direct agent for task${NC}"
echo -e "${YELLOW}Task: $TASK${NC}"
echo -e "${YELLOW}Session: $SESSION_NAME${NC}"

# Create the agent with direct claude command
tmux new-session -d -s "$SESSION_NAME" -c "$WORK_DIR" \
    "export CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192 && \
     cd $WORK_DIR && \
     echo '🤖 Starting agent with token limit: 8192' && \
     claude -p \"You are an AI assistant helping with software development tasks.

TASK: $TASK

Instructions:
1. First, create a new branch from main for your work
2. Search for and fix the issue described in the task
3. Run tests to ensure your fix works
4. Create a pull request with your changes

Use the appropriate tools to complete this task efficiently.\" \
     --output-format stream-json \
     --verbose \
     --model claude-sonnet-4-20250514 && \
     echo && \
     echo '✅ Agent completed' && \
     read -p 'Press Enter to close...'"

sleep 2

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${GREEN}✅ Agent started successfully!${NC}"
    echo
    echo "Monitor with: tmux attach -t $SESSION_NAME"
    echo
else
    echo -e "${RED}❌ Failed to start agent${NC}"
    exit 1
fi