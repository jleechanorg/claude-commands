#!/bin/bash

# Simplified PR automation - posts Codex comment instructions to drive follow-up agents
# Focuses on batch processing, attempt tracking, cooldowns, and notifications

PROCESSED_FILE="/tmp/pr_automation_processed.txt"
LOG_FILE="/tmp/pr_automation.log"
ATTEMPT_FILE="/tmp/pr_fix_attempts.txt"
MAX_BATCH_SIZE=5
MAX_FIX_ATTEMPTS=3

# Timeout configuration (in seconds)
COMMENT_TIMEOUT=300   # Allow Codex comment posting with generous buffer

# Create files if they don't exist
touch "$PROCESSED_FILE" "$ATTEMPT_FILE"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Default Codex instruction (can be overridden by exporting CODEX_COMMENT)
CODEX_COMMENT_DEFAULT="@codex use your judgment to fix comments from everyone or explain why it should not be fixed. Follow binary response protocol every comment needs done or not done classification explicitly with an explanation. Push any commits needed to remote so the PR is updated."
CODEX_COMMENT="${CODEX_COMMENT:-$CODEX_COMMENT_DEFAULT}"
CODEX_COMMIT_MARKER_PREFIX="<!-- codex-automation-commit:"
CODEX_COMMIT_MARKER_SUFFIX="-->"

GH_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$GH_REPO" ]; then
    log "❌ Unable to determine GitHub repository context for Codex automation"
    exit 1
fi

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
$(gh pr checks "$pr_number" --repo "$GH_REPO" 2>/dev/null || echo "Could not retrieve test details")
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
    shift
    local pr_number="$1"
    shift
    local operation_name="$1"
    shift

    if [ "$#" -eq 0 ]; then
        log "❌ No command provided for $operation_name (PR #$pr_number)"
        return 1
    fi

    log "⏱️  Executing $operation_name for PR #$pr_number (timeout: ${timeout_duration}s)"

    timeout "$timeout_duration" "$@"
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

# Function to notify about automation completion
notify_pr_completion() {
    local pr_number="$1"
    local status="$2"  # success, failure, timeout
    local details="$3"

    case "$status" in
        "success")
            log "✅ Automated processing completed successfully for PR #$pr_number"
            ;;
        "failure")
            log "❌ Automated processing failed for PR #$pr_number. Details: $details"
            ;;
        "timeout")
            log "⏰ Automated processing timed out for PR #$pr_number after ${COMMENT_TIMEOUT}s"
            ;;
        *)
            log "📝 Automated processing completed with status: $status for PR #$pr_number"
            ;;
    esac
}

# Codex instruction handling - posts default comment to PR
post_codex_instruction() {
    local pr_number="$1"

    log "💬 Requesting Codex instruction comment for PR #$pr_number"

    local pr_state_json
    local decision="post:"

    if pr_state_json=$(gh pr view "$pr_number" --repo "$GH_REPO" --json headRefOid,comments 2>/dev/null); then
        decision=$(printf '%s' "$pr_state_json" | python3 - "$CODEX_COMMIT_MARKER_PREFIX" "$CODEX_COMMIT_MARKER_SUFFIX" <<'PY'
import json
import sys

marker_prefix = sys.argv[1]
marker_suffix = sys.argv[2]

try:
    pr_data = json.load(sys.stdin)
except json.JSONDecodeError:
    print("post:")
    sys.exit(0)

head_sha = pr_data.get("headRefOid")
comments = (pr_data.get("comments") or {}).get("nodes", [])

decision = "post"
if head_sha:
    for comment in comments:
        body = (comment.get("body") or "").strip()
        prefix_index = body.find(marker_prefix)
        if prefix_index == -1:
            continue

        start_index = prefix_index + len(marker_prefix)
        end_index = body.find(marker_suffix, start_index)
        if end_index == -1:
            continue

        marker_sha = body[start_index:end_index].strip()
        if marker_sha == head_sha:
            decision = "skip"
            break

print(f"{decision}:{head_sha or ''}")
PY
)
    else
        log "⚠️ Unable to fetch PR state; proceeding with Codex comment"
    fi

    local action
    local head_sha
    if [ -z "$decision" ]; then
        action="post"
        head_sha=""
    else
        action="${decision%%:*}"
        head_sha="${decision#*:}"
    fi

    if [ "$action" = "skip" ]; then
        if [ -n "$head_sha" ]; then
            log "♻️ Codex instruction already posted for commit $head_sha on PR #$pr_number; skipping"
        else
            log "♻️ Codex instruction already posted for current head on PR #$pr_number; skipping"
        fi
        notify_pr_completion "$pr_number" "success" ""
        return 0
    fi

    local comment_body="$CODEX_COMMENT"
    if [ -n "$head_sha" ]; then
        comment_body=$(printf "%s\n\n%s%s%s" "$CODEX_COMMENT" "$CODEX_COMMIT_MARKER_PREFIX" "$head_sha" "$CODEX_COMMIT_MARKER_SUFFIX")
    fi

    execute_with_timeout "$COMMENT_TIMEOUT" "$pr_number" "Codex instruction comment" \
        gh pr comment "$pr_number" --repo "$GH_REPO" --body "$comment_body"
    local comment_result=$?

    case $comment_result in
        0)
            notify_pr_completion "$pr_number" "success" ""
            ;;
        2)
            notify_pr_completion "$pr_number" "timeout" ""
            ;;
        *)
            notify_pr_completion "$pr_number" "failure" "Codex instruction comment failed"
            ;;
    esac

    return $comment_result
}

# Function to post threaded comment replies with AI Cron Responder prefix
post_threaded_comment() {
    local pr_number="$1"
    local message="$2"
    local in_reply_to="$3"  # Optional: comment ID to reply to

    local prefixed_message="[AI Cron Responder] $message"

    if [ -n "$in_reply_to" ]; then
        # Reply to specific comment thread
        if \! gh pr comment "$pr_number" --repo "$GH_REPO" --body "$prefixed_message" --reply-to "$in_reply_to" 2>/dev/null; then
            log "❌ Failed to post threaded reply for PR #$pr_number"
            return 1
        fi
        log "💬 Posted threaded reply to PR #$pr_number (reply to: $in_reply_to)"
    else
        # Post general comment
        if \! gh pr comment "$pr_number" --repo "$GH_REPO" --body "$prefixed_message" 2>/dev/null; then
            log "❌ Failed to post comment for PR #$pr_number"
            return 1
        fi
        log "💬 Posted comment to PR #$pr_number"
    fi

    return 0
}

# Main processing logic
log "🚀 Starting simplified PR batch processing with Codex instruction comments"

# Get PRs updated in last 24 hours
RECENT_PRS=$(gh pr list --repo "$GH_REPO" --state open --limit 20 --json number,updatedAt | \
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

    # Codex comment automation - instructs Codex by default
    ATTEMPT_COUNT=$(get_fix_attempts "$PR")

    log "💬 Processing PR #$PR with Codex comment automation (attempt count: $ATTEMPT_COUNT)"

    if [ $ATTEMPT_COUNT -lt $MAX_FIX_ATTEMPTS ]; then
        # Attempt Codex instruction comment posting
        NEW_ATTEMPT_COUNT=$(increment_fix_attempts "$PR")
        log "💬 Codex instruction attempt $NEW_ATTEMPT_COUNT/$MAX_FIX_ATTEMPTS for PR #$PR"

        post_codex_instruction "$PR"
        result=$?

        if [ $result -eq 0 ]; then
            # Processing succeeded - mark as completed
            TIMESTAMP=$(date +%s)
            grep -v "^$PR:" "$PROCESSED_FILE" > "${PROCESSED_FILE}.tmp" 2>/dev/null || true
            echo "$PR:$TIMESTAMP" >> "${PROCESSED_FILE}.tmp"
            mv "${PROCESSED_FILE}.tmp" "$PROCESSED_FILE"
            reset_fix_attempts "$PR"
            log "✅ Successfully posted Codex instruction comment for PR #$PR"
            PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
        elif [ $result -eq 2 ]; then
            # Timeout - don't count as failure, will retry later
            log "⏰ Codex instruction attempt $NEW_ATTEMPT_COUNT timed out for PR #$PR - will retry next cycle"
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
            log "❌ Codex instruction attempt $NEW_ATTEMPT_COUNT failed for PR #$PR"
        fi
    else
        # Max attempts reached - send email notification
        log "📧 Max Codex instruction attempts reached for PR #$PR - sending email notification"
        FAILURE_DETAILS_RAW=$(gh pr checks "$PR" --repo "$GH_REPO" 2>/dev/null | grep -E "(FAILURE|ERROR)" | head -5)
        FAILURE_DETAILS_FALLBACK="Could not retrieve failure details for PR #$PR. Last attempt may have timed out - check automation logs for timeout vs failure details."
        if [ -z "$FAILURE_DETAILS_RAW" ]; then
            FAILURE_DETAILS="$FAILURE_DETAILS_FALLBACK"
        else
            FAILURE_DETAILS="$FAILURE_DETAILS_RAW"
        fi
        send_email_notification "$PR" "codex_comment_max_attempts" "$FAILURE_DETAILS" "$ATTEMPT_COUNT"

        # Reset attempts to allow future processing
        reset_fix_attempts "$PR"
    fi
done

log "🏁 Simplified PR batch processing complete (processed: $PROCESSED_COUNT)"
