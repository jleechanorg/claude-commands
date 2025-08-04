#!/bin/bash

# Simplified PR automation - /copilot handles all analysis and workflow decisions
# Focuses on batch processing, attempt tracking, cooldowns, and notifications

PROCESSED_FILE="/tmp/pr_automation_processed.txt"
LOG_FILE="/tmp/pr_automation.log"
ATTEMPT_FILE="/tmp/pr_fix_attempts.txt"
MAX_BATCH_SIZE=5
MAX_FIX_ATTEMPTS=3

# Timeout configuration (in seconds)
COPILOT_TIMEOUT=1200   # 20 minutes for comprehensive /copilot processing

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

# Function to handle command execution with timeout and error detection
execute_with_timeout() {
    local timeout_duration="$1"
    local command="$2"
    local pr_number="$3"
    local operation_name="$4"

    log "⏱️  Executing $operation_name for PR #$pr_number (timeout: ${timeout_duration}s)"

    eval timeout "$timeout_duration" "$command"
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log "✅ $operation_name succeeded for PR #$pr_number"
        return 0
    elif [ $exit_code -eq 124 ]; then
        log "⏰ $operation_name timed out after ${timeout_duration}s for PR #$pr_number"
        return 2  # Special return code for timeout
    else
        log "❌ $operation_name failed for PR #$pr_number (exit code: $exit_code)"
        return 1
    fi
}

# Simplified PR processing - /copilot handles all analysis
process_pr_with_copilot() {
    local pr_number="$1"

    log "🤖 Processing PR #$pr_number with comprehensive /copilot workflow"
    cd ~/projects/worldarchitect.ai

    execute_with_timeout "$COPILOT_TIMEOUT" \
        "claude --dangerously-skip-permissions --model sonnet '/copilot $pr_number'" \
        "$pr_number" "comprehensive PR processing"

    return $?
}

# Main processing logic
log "🚀 Starting simplified PR batch processing with /copilot"

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

    # Simplified processing - /copilot handles all analysis and decisions
    ATTEMPT_COUNT=$(get_fix_attempts "$PR")

    log "🤖 Processing PR #$PR with /copilot (attempt count: $ATTEMPT_COUNT)"

    if [ $ATTEMPT_COUNT -lt $MAX_FIX_ATTEMPTS ]; then
        # Attempt comprehensive /copilot processing
        NEW_ATTEMPT_COUNT=$(increment_fix_attempts "$PR")
        log "🤖 Copilot attempt $NEW_ATTEMPT_COUNT/$MAX_FIX_ATTEMPTS for PR #$PR"

        process_pr_with_copilot "$PR"
        result=$?

        if [ $result -eq 0 ]; then
            # Processing succeeded - mark as completed
            TIMESTAMP=$(date +%s)
            grep -v "^$PR:" "$PROCESSED_FILE" > "${PROCESSED_FILE}.tmp" 2>/dev/null || true
            echo "$PR:$TIMESTAMP" >> "${PROCESSED_FILE}.tmp"
            mv "${PROCESSED_FILE}.tmp" "$PROCESSED_FILE"
            reset_fix_attempts "$PR"
            log "✅ Successfully processed PR #$PR with /copilot"
            PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
        elif [ $result -eq 2 ]; then
            # Timeout - don't count as failure, will retry later
            log "⏰ Copilot attempt $NEW_ATTEMPT_COUNT timed out for PR #$PR - will retry next cycle"
            # Decrement attempt count since timeout shouldn't count as attempt
            DECREMENTED_COUNT=$((NEW_ATTEMPT_COUNT - 1))
            # Ensure DECREMENTED_COUNT doesn't go below 0
            if [ $DECREMENTED_COUNT -lt 0 ]; then
                DECREMENTED_COUNT=0
            fi
            if [ $DECREMENTED_COUNT -gt 0 ]; then
                grep -v "^$PR:" "$ATTEMPT_FILE" > "${ATTEMPT_FILE}.tmp" 2>/dev/null || true
                echo "$PR:$DECREMENTED_COUNT" >> "${ATTEMPT_FILE}.tmp"
                mv "${ATTEMPT_FILE}.tmp" "$ATTEMPT_FILE"
            else
                reset_fix_attempts "$PR"
            fi
        else
            log "❌ Copilot attempt $NEW_ATTEMPT_COUNT failed for PR #$PR"
        fi
    else
        # Max attempts reached - send email notification
        log "📧 Max copilot attempts reached for PR #$PR - sending email notification"
        FAILURE_DETAILS_RAW=$(gh pr checks "$PR" 2>/dev/null | grep -E "(FAILURE|ERROR)" | head -5)
        FAILURE_DETAILS_FALLBACK="Could not retrieve failure details for PR #$PR. Last attempt may have timed out - check automation logs for timeout vs failure details."
        if [ -z "$FAILURE_DETAILS_RAW" ]; then
            FAILURE_DETAILS="$FAILURE_DETAILS_FALLBACK"
        else
            FAILURE_DETAILS="$FAILURE_DETAILS_RAW"
        fi
        send_email_notification "$PR" "copilot_max_attempts" "$FAILURE_DETAILS" "$ATTEMPT_COUNT"

        # Reset attempts to allow future processing
        reset_fix_attempts "$PR"
    fi
done

log "🏁 Simplified PR batch processing complete (processed: $PROCESSED_COUNT)"

# Define workspace base directory if not already set
WORKSPACE_BASE_DIR="${WORKSPACE_BASE_DIR:-/tmp/pr-automation-workspace}"

# Function to create isolated workspace for PR processing
create_isolated_workspace() {
    local pr_number="$1"
    local workspace_dir="$WORKSPACE_BASE_DIR-$pr_number"

    log "🏗️  Creating isolated workspace for PR #$pr_number at $workspace_dir"

    # Clean up any existing workspace (with safety validation)
    if [ -z "$workspace_dir" ] || [ "$workspace_dir" = "/" ] || [ "$workspace_dir" = "/tmp" ]; then
        log "❌ Invalid workspace directory: $workspace_dir"
        return 1
    fi
    rm -rf "$workspace_dir"
    mkdir -p "$workspace_dir"

    # Get PR branch info
    local pr_info=$(gh pr view "$pr_number" --json headRefName,headRepository 2>/dev/null || echo "")
    if [ -z "$pr_info" ]; then
        log "❌ Failed to get PR #$pr_number information"
        return 1
    fi

    local branch_name=$(echo "$pr_info" | jq -r '.headRefName // "unknown"')
    local repo_owner=$(echo "$pr_info" | jq -r '.headRepository.owner.login // "unknown"')

    if [ "$branch_name" = "unknown" ] || [ "$repo_owner" = "unknown" ]; then
        log "❌ Could not extract branch info for PR #$pr_number"
        return 1
    fi

    # Clone the PR branch to isolated workspace
    cd "$workspace_dir" || return 1
    local repo_url="https://github.com/$repo_owner/worldarchitect.ai.git"

    if \! git clone --depth 1 --single-branch --branch "$branch_name" "$repo_url" . 2>/dev/null; then
        log "❌ Failed to clone PR #$pr_number branch $branch_name from $repo_url"
        cd - >/dev/null
        rm -rf "$workspace_dir"
        return 1
    fi

    log "✅ Isolated workspace created for PR #$pr_number"
    cd - >/dev/null
    echo "$workspace_dir"
}

# Function to post threaded comment replies with AI Cron Responder prefix
post_threaded_comment() {
    local pr_number="$1"
    local message="$2"
    local in_reply_to="$3"  # Optional: comment ID to reply to

    local prefixed_message="[AI Cron Responder] $message"

    if [ -n "$in_reply_to" ]; then
        # Reply to specific comment thread
        if \! gh pr comment "$pr_number" --body "$prefixed_message" --reply-to "$in_reply_to" 2>/dev/null; then
            log "❌ Failed to post threaded reply for PR #$pr_number"
            return 1
        fi
        log "💬 Posted threaded reply to PR #$pr_number (reply to: $in_reply_to)"
    else
        # Post general comment
        if \! gh pr comment "$pr_number" --body "$prefixed_message" 2>/dev/null; then
            log "❌ Failed to post comment for PR #$pr_number"
            return 1
        fi
        log "💬 Posted comment to PR #$pr_number"
    fi

    return 0
}

# Function to cleanup isolated workspace
cleanup_isolated_workspace() {
    local pr_number="$1"
    local workspace_dir="$WORKSPACE_BASE_DIR-$pr_number"

    if [ -d "$workspace_dir" ]; then
        rm -rf "$workspace_dir"
        log "🧹 Cleaned up workspace for PR #$pr_number"
    fi
}

# Function to push changes from isolated workspace to remote PR branch
push_to_remote_pr_branch() {
    local pr_number="$1"
    local workspace_dir="$2"
    local original_dir="$(pwd)"

    cd "$workspace_dir" || return 1

    # Check if there are any changes to commit
    if git diff --quiet && git diff --cached --quiet; then
        log "📝 No changes to push for PR #$pr_number"
        cd "$original_dir" || true
        return 0
    fi

    # Configure git if needed
    git config user.email "automation@worldarchitect.ai" 2>/dev/null || true
    git config user.name "PR Automation" 2>/dev/null || true

    # Commit and push changes
    git add -A
    if \! git commit -m "🤖 Automated fixes via copilot for PR #$pr_number

Co-Authored-By: Claude <noreply@anthropic.com>"; then
        log "❌ Failed to commit changes for PR #$pr_number"
        cd "$original_dir" || true
        return 1
    fi

    if \! git push origin HEAD; then
        log "❌ Failed to push changes for PR #$pr_number"
        cd "$original_dir" || true
        return 1
    fi

    log "✅ Successfully pushed automated fixes for PR #$pr_number"
    cd "$original_dir" || true
    return 0
}
