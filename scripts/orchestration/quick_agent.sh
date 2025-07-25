#!/bin/bash
# Quick agent spawner that bypasses orchestration complexity
# Usage: ./quick_agent.sh "task description"

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if task provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No task provided${NC}"
    echo "Usage: $0 \"task description\""
    exit 1
fi

TASK="$1"
SESSION_NAME="agent-$(date +%s | tail -c 5)"
CLAUDE_PATH="/home/jleechan/.claude/local/claude"

# Create agent prompt with standard instructions
AGENT_PROMPT="$TASK

IMPORTANT INSTRUCTIONS:
1. First use /nb to create a clean branch from latest main
2. Complete the task using appropriate tools
3. Run tests with ./run_tests.sh if you modify code
4. Use /pr to create a pull request when done
5. Include test results in PR description"

echo -e "${GREEN}🚀 Starting agent for task${NC}"
echo -e "${YELLOW}Task: $TASK${NC}"
echo -e "${YELLOW}Session: $SESSION_NAME${NC}"
echo

# Create the agent session with correct token limit
tmux new-session -d -s "$SESSION_NAME" \
    -c "/home/jleechan/projects/worldarchitect.ai" \
    "cd /home/jleechan/projects/worldarchitect.ai && \
     export CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192 && \
     echo 'Starting Claude with token limit: 8192' && \
     $CLAUDE_PATH -p '$AGENT_PROMPT' \
         --output-format stream-json \
         --verbose \
         --model claude-sonnet-4-20250514 && \
     echo && \
     echo 'Task completed. Press Enter to exit...' && \
     read"

# Wait for session to start
sleep 2

# Check if session was created
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${GREEN}✅ Agent started successfully!${NC}"
    echo
    echo "Monitor with: tmux attach -t $SESSION_NAME"
    echo "List agents: tmux ls | grep agent"
    echo
else
    echo -e "${RED}❌ Failed to start agent${NC}"
    exit 1
fi

# Show initial output
echo -e "${YELLOW}Starting output:${NC}"
tmux capture-pane -t "$SESSION_NAME" -p | tail -20