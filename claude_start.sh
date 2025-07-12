#!/bin/bash
# Claude Code startup script with model selection
# Always uses --dangerously-skip-permissions and prompts for model choice
# Model updated: July 6th, 2025

# Check if MCP servers are installed by checking if claude mcp list returns any servers
echo "🔍 Checking MCP servers..."
MCP_LIST=$(claude mcp list 2>/dev/null)
MCP_SERVERS=$(echo "$MCP_LIST" | grep -E "^[a-zA-Z].*:" | wc -l)

if [ "$MCP_SERVERS" -eq 0 ]; then
    echo "🔧 No MCP servers detected. Installing..."
    if [ -f "./claude_mcp.sh" ]; then
        bash ./claude_mcp.sh
        echo ""
    else
        echo "⚠️  claude_mcp.sh not found in current directory"
        echo ""
    fi
else
    echo "✅ Found $MCP_SERVERS MCP servers installed:"
    echo "$MCP_LIST" | head -5
    if [ "$MCP_SERVERS" -gt 5 ]; then
        echo "... and $((MCP_SERVERS - 5)) more"
    fi
    echo ""
fi

# Check if it's been a month since model was last updated
LAST_UPDATE="2025-07-06"
CURRENT_DATE=$(date +%Y-%m-%d)
LAST_UPDATE_EPOCH=$(date -d "$LAST_UPDATE" +%s)
CURRENT_EPOCH=$(date -d "$CURRENT_DATE" +%s)
DAYS_DIFF=$(( (CURRENT_EPOCH - LAST_UPDATE_EPOCH) / 86400 ))

if [ $DAYS_DIFF -gt 30 ]; then
    echo "⚠️  WARNING: Model was last updated on $LAST_UPDATE (${DAYS_DIFF} days ago)"
    echo "   Consider checking if claude-sonnet-4-20250514 is still the latest model"
    echo ""
fi

# Check if there's an existing conversation to continue
# Claude stores conversations in ~/.claude/projects/ directories
# Claude converts slashes, underscores, and dots to hyphens in directory names
PROJECT_DIR_NAME=$(pwd | sed 's/[\/._]/-/g')
CLAUDE_PROJECT_DIR="$HOME/.claude/projects/${PROJECT_DIR_NAME}"

# Check if the project directory exists and has conversation files
# Using find to check for .jsonl files as a more reliable method
if find "$HOME/.claude/projects" -maxdepth 1 -type d -name "${PROJECT_DIR_NAME}" 2>/dev/null | grep -q .; then
    if find "$HOME/.claude/projects/${PROJECT_DIR_NAME}" -name "*.jsonl" -type f 2>/dev/null | grep -q .; then
        echo "Found existing conversation(s) in this project directory"
        FLAGS="--dangerously-skip-permissions --continue"
    else
        echo "Project directory exists but no conversations found"
        FLAGS="--dangerously-skip-permissions"
    fi
else
    echo "No existing conversations found for this project"
    FLAGS="--dangerously-skip-permissions"
fi

echo ""
echo "Select mode:"
echo "1) Worker (Sonnet 4)"
echo "2) Default"
read -p "Choice [2]: " choice

case ${choice:-2} in
    1) 
        MODEL="claude-sonnet-4-20250514"
        echo "Starting Claude Code in worker mode with $MODEL..."
        claude --model "$MODEL" $FLAGS "$@"
        ;;
    2) 
        echo "Starting Claude Code with default settings..."
        claude $FLAGS "$@"
        ;;
    *) 
        echo "Invalid choice, using default"
        claude $FLAGS "$@"
        ;;
esac