#!/bin/bash

# Enhanced PR automation with intelligent test fixing and email notifications
# Processes PRs with status analysis, automated fixing, and detailed error reporting

PROCESSED_FILE="/tmp/pr_automation_processed.txt"
LOG_FILE="/tmp/pr_automation.log"
ATTEMPT_FILE="/tmp/pr_fix_attempts.txt"
MAX_BATCH_SIZE=5
MAX_FIX_ATTEMPTS=3

# Create files if they don't exist
touch "$PROCESSED_FILE" "$ATTEMPT_FILE"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to send email notification
send_email_notification() {
    local pr_number="$1"
    local issue_type="$2"
    local details="$3"
    local attempt_count="$4"

    # Load email configuration
    source ~/.memory_email_config

    local subject="PR #$pr_number Automation Failed: $issue_type"
    local body="PR #$pr_number requires manual intervention after $attempt_count automated fix attempts.

Issue Type: $issue_type
Details: $details

PR URL: https://github.com/jleechanorg/worldarchitect.ai/pull/$pr_number

Automated fix attempts have been exhausted. Please review and fix manually.

=== Recent Automation Logs ===
$(tail -20 "$LOG_FILE")

=== Test Failure Details ===
$(gh pr checks "$pr_number" 2>/dev/null || echo "Could not retrieve test details")
"

    # Send email using Python
    python3 -c "
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.environ.get('SMTP_PORT', '587'))
username = os.environ.get('SMTP_USERNAME')
password = os.environ.get('SMTP_PASSWORD')
from_email = os.environ.get('MEMORY_EMAIL_FROM')
to_email = os.environ.get('MEMORY_EMAIL_TO')

msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = '''$subject'''

msg.attach(MIMEText('''$body''', 'plain'))

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(username, password)
    server.send_message(msg)
    server.quit()
    print('Email sent successfully')
except Exception as e:
    print(f'Email failed: {e}')
"
}

# Function to get PR status details
get_pr_status() {
    local pr_number="$1"
    gh pr view "$pr_number" --json mergeable,mergeStateStatus,statusCheckRollup
}

# Function to count fix attempts for a PR
get_fix_attempts() {
    local pr_number="$1"
    local attempts=$(grep "^$pr_number:" "$ATTEMPT_FILE" 2>/dev/null | cut -d':' -f2)
    if [ -z "$attempts" ]; then
        echo "0"
    else
        echo "$attempts"
    fi
}

# Function to increment fix attempts
increment_fix_attempts() {
    local pr_number="$1"
    local current_attempts=$(get_fix_attempts "$pr_number")
    local new_attempts=$((current_attempts + 1))

    # Remove old entry and add new one
    grep -v "^$pr_number:" "$ATTEMPT_FILE" > "${ATTEMPT_FILE}.tmp" 2>/dev/null || true
    echo "$pr_number:$new_attempts" >> "${ATTEMPT_FILE}.tmp"
    mv "${ATTEMPT_FILE}.tmp" "$ATTEMPT_FILE"

    echo "$new_attempts"
}

# Function to reset fix attempts (on success)
reset_fix_attempts() {
    local pr_number="$1"
    grep -v "^$pr_number:" "$ATTEMPT_FILE" > "${ATTEMPT_FILE}.tmp" 2>/dev/null || true
    mv "${ATTEMPT_FILE}.tmp" "$ATTEMPT_FILE"
}

# Function to attempt automated fix
attempt_automated_fix() {
    local pr_number="$1"
    local issue_type="$2"

    log "🔧 Attempting automated fix for PR #$pr_number ($issue_type)"

    cd ~/projects/worldarchitect.ai

    case "$issue_type" in
        "failing_tests")
            # Use /copilot to fix failing tests
            if claude --dangerously-skip-permissions "/copilot $pr_number focus on fixing failing tests"; then
                log "✅ Automated test fix succeeded for PR #$pr_number"
                return 0
            else
                log "❌ Automated test fix failed for PR #$pr_number"
                return 1
            fi
            ;;

        "unknown_status")
            # Refresh merge status by viewing the PR
            log "🔄 Refreshing merge status for PR #$pr_number"
            gh pr view "$pr_number" > /dev/null 2>&1
            sleep 5  # Give GitHub time to refresh

            # Check if status is still unknown
            local status=$(gh pr view "$pr_number" --json mergeable | jq -r '.mergeable')
            if [ "$status" != "UNKNOWN" ]; then
                log "✅ Merge status refreshed for PR #$pr_number (now: $status)"
                return 0
            else
                log "❌ Merge status still unknown for PR #$pr_number"
                return 1
            fi
            ;;

        "merge_conflicts")
            # Use /copilot to resolve merge conflicts
            if claude --dangerously-skip-permissions "/copilot $pr_number focus on resolving merge conflicts"; then
                log "✅ Automated conflict resolution succeeded for PR #$pr_number"
                return 0
            else
                log "❌ Automated conflict resolution failed for PR #$pr_number"
                return 1
            fi
            ;;

        *)
            log "❓ Unknown issue type: $issue_type for PR #$pr_number"
            return 1
            ;;
    esac
}

# Function to analyze PR and determine issues
analyze_pr_status() {
    local pr_number="$1"
    local pr_status=$(get_pr_status "$pr_number")

    local mergeable=$(echo "$pr_status" | jq -r '.mergeable')
    local merge_state=$(echo "$pr_status" | jq -r '.mergeStateStatus')
    local failed_checks=$(echo "$pr_status" | jq -r '.statusCheckRollup[] | select(.conclusion == "FAILURE") | .name' | wc -l)

    log "📊 PR #$pr_number status: mergeable=$mergeable, state=$merge_state, failed_checks=$failed_checks"

    # Determine primary issue
    if [ "$failed_checks" -gt 0 ] || [ "$merge_state" = "UNSTABLE" ]; then
        echo "failing_tests"
    elif [ "$mergeable" = "UNKNOWN" ]; then
        echo "unknown_status"
    elif [ "$merge_state" = "DIRTY" ]; then
        echo "merge_conflicts"
    elif [ "$mergeable" = "MERGEABLE" ] && [ "$merge_state" = "CLEAN" ]; then
        echo "ready"
    else
        echo "other:$mergeable:$merge_state"
    fi
}

# Main processing logic
log "🚀 Starting enhanced PR batch processing"

# Get PRs updated in last 24 hours
RECENT_PRS=$(gh pr list --state open --limit 20 --json number,updatedAt | \
    jq -r '.[] | select((.updatedAt | fromdateiso8601) > (now - 86400)) | .number')

if [ -z "$RECENT_PRS" ]; then
    log "No PRs updated in the last 24 hours"
    exit 0
fi

# Process each PR
PROCESSED_COUNT=0
CURRENT_TIME=$(date +%s)

for PR in $RECENT_PRS; do
    # Check processing limits
    if [ $PROCESSED_COUNT -ge $MAX_BATCH_SIZE ]; then
        log "Reached batch size limit ($MAX_BATCH_SIZE)"
        break
    fi

    # Check if processed recently (4 hour cooldown for successful processing)
    LAST_PROCESSED=$(grep "^$PR:" "$PROCESSED_FILE" 2>/dev/null | cut -d':' -f2)
    if [ -n "$LAST_PROCESSED" ]; then
        TIME_DIFF=$((CURRENT_TIME - LAST_PROCESSED))
        if [ $TIME_DIFF -lt 14400 ]; then  # 4 hours
            log "Skipping PR #$PR (processed $(($TIME_DIFF / 60)) minutes ago)"
            continue
        fi
    fi

    # Analyze PR status
    ISSUE_TYPE=$(analyze_pr_status "$PR" 2>&1 | grep -v "📊" | tail -1)
    ATTEMPT_COUNT=$(get_fix_attempts "$PR")

    log "🔍 PR #$PR issue: $ISSUE_TYPE (attempt count: $ATTEMPT_COUNT)"

    case "$ISSUE_TYPE" in
        "ready")
            log "✅ PR #$PR is ready to merge - running standard /copilot"
            cd ~/projects/worldarchitect.ai
            if claude --dangerously-skip-permissions "/copilot $PR"; then
                # Mark as processed
                TIMESTAMP=$(date +%s)
                grep -v "^$PR:" "$PROCESSED_FILE" > "${PROCESSED_FILE}.tmp" 2>/dev/null || true
                echo "$PR:$TIMESTAMP" >> "${PROCESSED_FILE}.tmp"
                mv "${PROCESSED_FILE}.tmp" "$PROCESSED_FILE"
                reset_fix_attempts "$PR"
                log "✅ Successfully processed ready PR #$PR"
                PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
            else
                log "❌ Standard processing failed for PR #$PR"
            fi
            ;;

        "failing_tests"|"unknown_status"|"merge_conflicts")
            log "🔧 Processing PR #$PR with issue: $ISSUE_TYPE (attempts: $ATTEMPT_COUNT/$MAX_FIX_ATTEMPTS)"
            if [ $ATTEMPT_COUNT -lt $MAX_FIX_ATTEMPTS ]; then
                # Attempt automated fix
                NEW_ATTEMPT_COUNT=$(increment_fix_attempts "$PR")
                log "🔧 Fix attempt $NEW_ATTEMPT_COUNT/$MAX_FIX_ATTEMPTS for PR #$PR"

                if attempt_automated_fix "$PR" "$ISSUE_TYPE"; then
                    # Fix succeeded - mark as processed
                    TIMESTAMP=$(date +%s)
                    grep -v "^$PR:" "$PROCESSED_FILE" > "${PROCESSED_FILE}.tmp" 2>/dev/null || true
                    echo "$PR:$TIMESTAMP" >> "${PROCESSED_FILE}.tmp"
                    mv "${PROCESSED_FILE}.tmp" "$PROCESSED_FILE"
                    reset_fix_attempts "$PR"
                    log "✅ Successfully fixed and processed PR #$PR"
                    PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
                else
                    log "❌ Fix attempt $NEW_ATTEMPT_COUNT failed for PR #$PR"
                fi
            else
                # Max attempts reached - send email notification
                log "📧 Max fix attempts reached for PR #$PR - sending email notification"
                FAILURE_DETAILS=$(gh pr checks "$PR" 2>/dev/null | grep -E "(FAILURE|ERROR)" | head -5 || echo "Could not retrieve failure details")
                send_email_notification "$PR" "$ISSUE_TYPE" "$FAILURE_DETAILS" "$ATTEMPT_COUNT"

                # Reset attempts to allow future processing
                reset_fix_attempts "$PR"
            fi
            ;;

        other:*)
            log "❓ Unknown issue type for PR #$PR: $ISSUE_TYPE"
            ;;
    esac
done

log "🏁 Enhanced PR batch processing complete (processed: $PROCESSED_COUNT)"
