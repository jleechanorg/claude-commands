#!/bin/bash
# Wrapper script that sets required env vars for jleechanorg-pr-monitor
# This is needed because cron runs with minimal environment

# Source automation env vars if available
if [ -f "$HOME/.automation_env" ]; then
    source "$HOME/.automation_env"
fi

exec jleechanorg-pr-monitor "$@"
