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
else
  # Resolve current branch; fall back for detached-HEAD
  REMOTE_BRANCH=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git branch --show-current)
  if [ -z "$REMOTE_BRANCH" ] || [ "$REMOTE_BRANCH" = "HEAD" ]; then
    echo "Error: Could not determine current branch (detached HEAD?). Please specify a branch name or ensure you are in a valid Git repository."
    exit 1
  fi
fi

if ! command -v ccschedule >/dev/null 2>&1; then
  echo "Error: 'ccschedule' command not found in PATH"
  exit 1
fi
ccschedule --time "$SCHEDULE_TIME" --message "Continue work on the remote branch $REMOTE_BRANCH"
