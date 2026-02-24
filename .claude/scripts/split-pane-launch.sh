#!/bin/bash
# Claude Code Split-Pane Launcher
# Usage: claudet [model]
#        claudet          # uses sonnet (default)
#        claudet opus    # uses opus
#        claudet haiku   # uses haiku

MODEL="${1:-sonnet}"
SESSION_NAME="claude-team-$(date +%H%M%S)-$$"  # unique per invocation (time + PID)
MODEL_Q=$(printf '%q' "$MODEL")  # safe quoting to prevent shell injection in tmux command

# Check if we're already in tmux
if [ -z "${TMUX:-}" ]; then
    # Not in tmux - start a new session and launch Claude Code with bypass permissions + tmux split mode
    tmux new-session -d -s "$SESSION_NAME" "claude --dangerously-skip-permissions --teammate-mode tmux --model $MODEL_Q"

    # Attach to the session
    tmux attach-session -t "$SESSION_NAME"
else
    # Already in tmux - launch Claude Code with bypass permissions + tmux split mode
    exec claude --dangerously-skip-permissions --teammate-mode tmux --model "$MODEL"
fi
