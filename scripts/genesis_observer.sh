#!/bin/bash
# Genesis Observer - Monitoring ONLY (No Completion Detection)
# Fixed version that observes Genesis sessions without making completion decisions

SCRIPT_NAME="Genesis Observer"
CHECK_INTERVAL=${CHECK_INTERVAL:-180}  # 3 minutes default

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

monitor_session() {
    local session_name="$1"
    local log_file="$2"

    log_with_timestamp "🔄 Starting $SCRIPT_NAME for session: $session_name" | tee -a "$log_file"
    log_with_timestamp "📊 Check interval: ${CHECK_INTERVAL}s (${CHECK_INTERVAL}s)" | tee -a "$log_file"
    log_with_timestamp "======================================" | tee -a "$log_file"

    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

        # Check if session exists
        if tmux list-sessions 2>/dev/null | grep -q "^$session_name:"; then
            log_with_timestamp "✅ Session $session_name is running" | tee -a "$log_file"

            # Capture recent output for observation only
            local recent_output=$(tmux capture-pane -t "$session_name" -p -S -5 2>/dev/null | tail -3)
            if [ -n "$recent_output" ]; then
                log_with_timestamp "📋 Recent output:" | tee -a "$log_file"
                echo "$recent_output" | sed 's/^/   /' | tee -a "$log_file"
            else
                log_with_timestamp "📋 No recent output captured" | tee -a "$log_file"
            fi

            log_with_timestamp "⏰ Next check in ${CHECK_INTERVAL}s..." | tee -a "$log_file"

        else
            log_with_timestamp "❌ Session $session_name not found" | tee -a "$log_file"
            log_with_timestamp "🏁 Genesis session ended - Observer stopping" | tee -a "$log_file"
            break
        fi

        echo "" | tee -a "$log_file"
        sleep "$CHECK_INTERVAL"
    done

    log_with_timestamp "👁️ Observer monitoring completed for session: $session_name" | tee -a "$log_file"
}

# 🚨 CRITICAL: NO COMPLETION DETECTION LOGIC
# This observer only monitors and reports - Genesis determines its own completion

if [ $# -lt 1 ]; then
    echo "Usage: $0 <session_name> [log_file]"
    echo "Example: $0 gene-20250923-173740 /tmp/genesis_observer.log"
    exit 1
fi

SESSION_NAME="$1"
LOG_FILE="${2:-/tmp/genesis_observer.log}"

monitor_session "$SESSION_NAME" "$LOG_FILE"
