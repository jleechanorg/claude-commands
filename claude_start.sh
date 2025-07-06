#!/bin/bash
# Claude Code startup script with model selection
# Always uses --dangerously-skip-permissions and prompts for model choice
# Model updated: July 6th, 2025

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

echo "Select mode:"
echo "1) Worker (Sonnet 4)"
echo "2) Default"
read -p "Choice [2]: " choice

case ${choice:-2} in
    1) 
        MODEL="claude-sonnet-4-20250514"
        echo "Starting Claude Code in worker mode with $MODEL..."
        claude --model "$MODEL" --dangerously-skip-permissions "$@"
        ;;
    2) 
        echo "Starting Claude Code with default settings..."
        claude --dangerously-skip-permissions "$@"
        ;;
    *) 
        echo "Invalid choice, using default"
        claude --dangerously-skip-permissions "$@"
        ;;
esac