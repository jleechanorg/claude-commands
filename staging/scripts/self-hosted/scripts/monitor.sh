#!/bin/bash
# GitHub Actions Runner Monitor Script
# Checks if runner is running and restarts if needed
#
# ⚠️  WARNING: This script will restart the runner if it detects it's down.
#     Active jobs may be interrupted. GitHub Actions will automatically
#     requeue interrupted jobs, but you may lose partial progress.
#
# Installation:
#   1. Copy this script to ~/actions-runner/monitor.sh
#   2. Make it executable: chmod +x ~/actions-runner/monitor.sh
#   3. Add to crontab: */15 * * * * ~/actions-runner/monitor.sh

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Error handler
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "$(date): Monitor script failed with exit code $exit_code" >> "${LOG_FILE:-/tmp/monitor-error.log}" 2>&1 || true
    fi
}

trap cleanup EXIT ERR

RUNNER_DIR=~/actions-runner
LOG_FILE="$RUNNER_DIR/monitor.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Check if the runner process is running for THIS specific runner directory
# Allow pgrep to fail without triggering set -e
if ! pgrep -f "Runner.Listener.*$RUNNER_DIR" > /dev/null 2>&1; then
    echo "$(date): Runner not running, attempting restart..." >> "$LOG_FILE"
    cd "$RUNNER_DIR" || {
        echo "$(date): ERROR: Cannot access $RUNNER_DIR" >> "$LOG_FILE"
        exit 1
    }

    # Try service restart first (may fail if service not installed)
    if ./svc.sh start >> "$LOG_FILE" 2>&1; then
        echo "$(date): Service restart attempted" >> "$LOG_FILE"
    else
        echo "$(date): Service start failed, trying direct run" >> "$LOG_FILE"
    fi

    # Wait for service to spawn the Runner.Listener process
    sleep 3

    # If service doesn't work, try direct run in background
    if ! pgrep -f "Runner.Listener.*$RUNNER_DIR" > /dev/null 2>&1; then
        echo "$(date): Service not running, starting via run.sh" >> "$LOG_FILE"
        nohup ./run.sh >> "$RUNNER_DIR/runner.log" 2>&1 &
        echo "$(date): Started runner directly via run.sh (PID: $!)" >> "$LOG_FILE"
    else
        echo "$(date): Service successfully started" >> "$LOG_FILE"
    fi
else
    echo "$(date): Runner is healthy" >> "$LOG_FILE"
fi
