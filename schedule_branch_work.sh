#!/bin/bash
set -euo pipefail

# Source bashrc to ensure PATH and environment variables are loaded
# This is necessary because some tools might be defined in bashrc
[[ -f ~/.bashrc ]] && source ~/.bashrc

# Check for correct number of arguments
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <time-HH:MM> [remote-branch-name]"
  echo "If a branch name is not specified, the script uses the current git branch."
  exit 1
fi

SCHEDULE_TIME="$1"

# Ensure the time is in HH:MM 24-hour format
if ! [[ "$SCHEDULE_TIME" =~ ^([01]?[0-9]|2[0-3]):[0-5][0-9]$ ]]; then
  echo "Error: time must be in HH:MM 24-hour format"
  exit 1
fi

# If a branch is provided as an argument, use it; otherwise, determine the current branch.
if [ "$#" -eq 2 ]; then
  REMOTE_BRANCH="$2"
  BRANCH_MESSAGE="Continue work on the remote branch $REMOTE_BRANCH. If you see conversation history that aligns with the current branch work, please review and consider that context to guide your continuation approach."
else
  # Resolve current branch; fall back for detached-HEAD
  REMOTE_BRANCH=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git branch --show-current)
  if [ -z "$REMOTE_BRANCH" ] || [ "$REMOTE_BRANCH" = "HEAD" ]; then
    echo "Error: Could not determine current branch (detached HEAD?). Please specify a branch name or ensure you are in a valid Git repository."
    exit 1
  fi

  # Gather context about current work
  echo "Gathering context for branch: $REMOTE_BRANCH"

  # Check for an open PR on this branch using the 'gh' CLI tool
  PR_INFO=""
  if command -v gh >/dev/null 2>&1; then
    PR_INFO=$(gh pr list --head "$REMOTE_BRANCH" --state open --json number,title,url 2>/dev/null | jq -r '.[] | "PR #\(.number): \(.title)"' 2>/dev/null || echo "")
  fi

  # Check for a scratchpad file for additional context
  SCRATCHPAD_INFO=""
  SCRATCHPAD_FILE="roadmap/scratchpad_${REMOTE_BRANCH}.md"
  if [ -f "$SCRATCHPAD_FILE" ]; then
    # Get the first few relevant lines of the scratchpad for context
    SCRATCHPAD_INFO=$(head -n 10 "$SCRATCHPAD_FILE" 2>/dev/null | grep -E "(Goal:|Task:|Current:|Status:)" | head -n 3 | tr '\n' ' ' || echo "")
  fi

  # Get recent commit messages from the current branch
  RECENT_COMMITS=$(git log --oneline -3 --first-parent 2>/dev/null | sed 's/^/  /' || echo "")

  # Check for a TODO file that might provide context
  TODO_INFO=""
  TODO_FILE="TODO_${REMOTE_BRANCH}.md"
  if [ -f "$TODO_FILE" ]; then
    TODO_INFO=$(head -n 5 "$TODO_FILE" 2>/dev/null | tr '\n' ' ' || echo "")
  fi

  # Build a comprehensive context message to be sent to Claude
  BRANCH_MESSAGE="Resume work on branch: $REMOTE_BRANCH"

  if [ -n "$PR_INFO" ]; then
    BRANCH_MESSAGE="$BRANCH_MESSAGE. Active $PR_INFO"
  fi

  if [ -n "$SCRATCHPAD_INFO" ]; then
    BRANCH_MESSAGE="$BRANCH_MESSAGE. Context: $SCRATCHPAD_INFO"
  fi

  if [ -n "$TODO_INFO" ]; then
    BRANCH_MESSAGE="$BRANCH_MESSAGE. TODO: $TODO_INFO"
  fi

  if [ -n "$RECENT_COMMITS" ]; then
    BRANCH_MESSAGE="$BRANCH_MESSAGE. Recent commits:$'\n'$RECENT_COMMITS"
  fi

  # Add a final instruction to review all available context
  BRANCH_MESSAGE="$BRANCH_MESSAGE$'\n\n'Please review conversation history and any existing context to continue the work appropriately."
fi

# --- SCHEDULING LOGIC ---
# Calculate the number of seconds to wait until the scheduled time.
# Cross-platform compatible date handling for GNU/Linux and macOS/BSD systems.

# Get current time in seconds since epoch
CURRENT_SECONDS=$(date +%s)

# Get target time in seconds since epoch (cross-platform compatible)
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "freebsd"* ]]; then
  # macOS/BSD date syntax
  TARGET_SECONDS=$(date -j -f "%H:%M" "$SCHEDULE_TIME" "+%s" 2>/dev/null)
  if [ $? -ne 0 ]; then
    echo "Error: Invalid time format for macOS/BSD date command"
    exit 1
  fi
else
  # GNU/Linux date syntax
  TARGET_SECONDS=$(date -d "$SCHEDULE_TIME" +%s 2>/dev/null)
  if [ $? -ne 0 ]; then
    echo "Error: Invalid time format for GNU date command"
    exit 1
  fi
fi

# If the target time has already passed today, schedule it for the same time tomorrow.
if [ "$TARGET_SECONDS" -lt "$CURRENT_SECONDS" ]; then
  TARGET_SECONDS=$((TARGET_SECONDS + 86400)) # Add 24 hours in seconds
fi

SLEEP_DURATION=$((TARGET_SECONDS - CURRENT_SECONDS))

# Validate sleep duration is reasonable (not negative, not more than 24 hours)
if [ "$SLEEP_DURATION" -lt 0 ] || [ "$SLEEP_DURATION" -gt 86400 ]; then
  echo "Error: Calculated sleep duration ($SLEEP_DURATION seconds) is invalid"
  exit 1
fi

# Format target time for display (cross-platform compatible)
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "freebsd"* ]]; then
  TARGET_TIME_DISPLAY=$(date -r "$TARGET_SECONDS" "+%Y-%m-%d %H:%M:%S")
else
  TARGET_TIME_DISPLAY=$(date -d "@$TARGET_SECONDS" "+%Y-%m-%d %H:%M:%S")
fi

echo "Waiting for $SLEEP_DURATION seconds until $TARGET_TIME_DISPLAY..."
echo "Press Ctrl+C to cancel."

# Set up signal handler to gracefully handle interruption
trap 'echo "\nScheduling cancelled by user."; exit 130' INT TERM

# Wait until the scheduled time and validate successful completion
if ! sleep "$SLEEP_DURATION"; then
  echo "Error: Sleep command was interrupted or failed"
  exit 1
fi

echo "Time reached! Launching Claude..."

# Run the claude command interactively, passing the gathered context as the initial prompt.
# Note: --dangerously-skip-permissions bypasses Claude's file access confirmation prompts.
# This is used here for automated scheduling but should be used carefully in interactive contexts.
claude --dangerously-skip-permissions --model sonnet "$BRANCH_MESSAGE"
