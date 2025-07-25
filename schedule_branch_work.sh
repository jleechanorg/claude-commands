#!/bin/bash
set -euo pipefail

# Source bashrc to ensure PATH and environment variables are loaded
# This is necessary because ccschedule runs in a non-interactive context
# where bashrc isn't automatically sourced
[[ -f ~/.bashrc ]] && source ~/.bashrc

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <time-HH:MM> [remote-branch-name]"
  echo "If branch is not specified, uses current branch"
  exit 1
fi

SCHEDULE_TIME="$1"

# Ensure HH:MM 24-hour format
if ! [[ "$SCHEDULE_TIME" =~ ^([01]?[0-9]|2[0-3]):[0-5][0-9]$ ]]; then
  echo "Error: time must be in HH:MM 24-hour format"
  exit 1
fi

# If branch is provided as second argument, use it; otherwise use current branch
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
  
  # Check for open PR on this branch
  PR_INFO=""
  if command -v gh >/dev/null 2>&1; then
    PR_INFO=$(gh pr list --head "$REMOTE_BRANCH" --state open --json number,title,url 2>/dev/null | jq -r '.[] | "PR #\(.number): \(.title)"' 2>/dev/null || echo "")
  fi
  
  # Check for scratchpad file
  SCRATCHPAD_INFO=""
  SCRATCHPAD_FILE="roadmap/scratchpad_${REMOTE_BRANCH}.md"
  if [ -f "$SCRATCHPAD_FILE" ]; then
    # Get first few lines of scratchpad for context
    SCRATCHPAD_INFO=$(head -n 10 "$SCRATCHPAD_FILE" 2>/dev/null | grep -E "(Goal:|Task:|Current:|Status:)" | head -n 3 | tr '\n' ' ' || echo "")
  fi
  
  # Get recent commit messages (only from current branch, not from main)
  RECENT_COMMITS=$(git log --oneline -3 --first-parent 2>/dev/null | sed 's/^/  /' || echo "")
  
  # Check for TODO or task files that might provide context
  TODO_INFO=""
  TODO_FILE="TODO_${REMOTE_BRANCH}.md"
  if [ -f "$TODO_FILE" ]; then
    TODO_INFO=$(head -n 5 "$TODO_FILE" 2>/dev/null | tr '\n' ' ' || echo "")
  fi
  
  # Build comprehensive context message
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
  
  # Add instruction to check conversation history
  BRANCH_MESSAGE="$BRANCH_MESSAGE$'\n\n'Please review conversation history and any existing context to continue the work appropriately."
fi

if ! command -v ccschedule >/dev/null 2>&1; then
  echo "Error: 'ccschedule' command not found in PATH"
  exit 1
fi
ccschedule --time "$SCHEDULE_TIME" --message "$BRANCH_MESSAGE"
