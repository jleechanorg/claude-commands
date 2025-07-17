#!/bin/bash

# Source bashrc to ensure PATH and environment variables are loaded
# This is necessary because ccschedule runs in a non-interactive context
# where bashrc isn't automatically sourced
source ~/.bashrc

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <remote-branch-name> <time-HH:MM>"
  exit 1
fi

REMOTE_BRANCH="$1"
SCHEDULE_TIME="$2"

ccschedule --time "$SCHEDULE_TIME" --message "Continue work on the remote branch $REMOTE_BRANCH"
