#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

# Ensure only one instance runs at a time
exec 9>/tmp/comment-validation.lock
if ! flock -n 9; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another comment validation instance is running; exiting." | tee -a "/tmp/comment_validation.log"
    exit 0
fi

# Comment Validation Mode - Same as PR automation but asks AI bots to review instead of Codex fixing
# Posts comment asking @coderabbit-ai, @greptileai, bugbot, copilot to review PR and check comments are fixed

PROCESSED_FILE="/tmp/comment_validation_processed.txt"
LOG_FILE="/tmp/comment_validation.log"
ATTEMPT_FILE="/tmp/comment_validation_attempts.txt"
MAX_BATCH_SIZE=5
MAX_VALIDATION_ATTEMPTS=3

# Timeout configuration (in seconds)
COMMENT_TIMEOUT=1200   # 20 minutes

# Create files if they don't exist
touch "$PROCESSED_FILE" "$ATTEMPT_FILE"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

GH_REPO="${GH_REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)}"
if [ -z "$GH_REPO" ]; then
    log "❌ Unable to determine GitHub repository context"
    exit 1
fi

# Function to send email notification
send_email_notification() {
    local pr_number="$1"
    local issue_type="$2"
    local details="$3"
    local attempt_count="$4"

    # Load email configuration if present
    if [ -f "$HOME/.memory_email_config" ]; then
        set -a
        . "$HOME/.memory_email_config"
        set +a
    fi

    local subject="PR #$pr_number Comment Validation Failed: $issue_type"
    local body="PR #$pr_number requires manual validation after $attempt_count automated validation attempts.

Issue Type: $issue_type
Details: $details

PR URL: https://github.com/jleechanorg/worldarchitect.ai/pull/$pr_number

Automated validation attempts have been exhausted. Please review manually.

=== Recent Validation Logs ===
$(tail -20 "$LOG_FILE")
"

    SUBJECT="$subject" BODY="$body" python3 - <<'PY'
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.environ.get('SMTP_PORT', '587'))
username = os.environ.get('SMTP_USERNAME')
password = os.environ.get('SMTP_PASSWORD')
from_email = os.environ.get('MEMORY_EMAIL_FROM')
to_email = os.environ.get('MEMORY_EMAIL_TO')
subject = os.environ.get('SUBJECT', '')
body = os.environ.get('BODY', '')

if not all([smtp_server, smtp_port, from_email, to_email]):
    print('Email configuration incomplete - skipping notification')
    raise SystemExit(0)

msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

try:
    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(msg)
    print('Email sent successfully')
except Exception as exc:
    print(f'Email failed: {exc}')
PY
}

# Function to count validation attempts for a PR
get_validation_attempts() {
    local pr_number="$1"
    local attempts=$(grep "^$pr_number:" "$ATTEMPT_FILE" 2>/dev/null | cut -d':' -f2)
    if [ -z "$attempts" ]; then
        echo "0"
    else
        echo "$attempts"
    fi
}

# Function to increment validation attempts
increment_validation_attempts() {
    local pr_number="$1"
    local lock_file="${ATTEMPT_FILE}.lock"
    local new_attempts

    new_attempts=$(
        flock -x 200 || exit 1
        local current_attempts=$(grep "^$pr_number:" "$ATTEMPT_FILE" 2>/dev/null | cut -d':' -f2)
        if [ -z "$current_attempts" ]; then
            current_attempts=0
        fi
        local updated=$((current_attempts + 1))
        grep -v "^$pr_number:" "$ATTEMPT_FILE" > "${ATTEMPT_FILE}.tmp" 2>/dev/null || true
        echo "$pr_number:$updated" >> "${ATTEMPT_FILE}.tmp"
        mv "${ATTEMPT_FILE}.tmp" "$ATTEMPT_FILE"
        echo "$updated"
    ) 200>"$lock_file"

    echo "$new_attempts"
}

# Function to reset validation attempts (on success)
reset_validation_attempts() {
    local pr_number="$1"
    local lock_file="${ATTEMPT_FILE}.lock"

    (
        flock -x 200
        if [ -s "$ATTEMPT_FILE" ]; then
            grep -v "^$pr_number:" "$ATTEMPT_FILE" > "${ATTEMPT_FILE}.tmp" 2>/dev/null || true
            mv "${ATTEMPT_FILE}.tmp" "$ATTEMPT_FILE"
        fi
    ) 200>"$lock_file"
}

write_processed_timestamp() {
    local pr_number="$1"
    local timestamp="$2"
    local lock_file="${PROCESSED_FILE}.lock"

    (
        flock -x 201
        grep -v "^$pr_number:" "$PROCESSED_FILE" > "${PROCESSED_FILE}.tmp" 2>/dev/null || true
        echo "$pr_number:$timestamp" >> "${PROCESSED_FILE}.tmp"
        mv "${PROCESSED_FILE}.tmp" "$PROCESSED_FILE"
    ) 201>"$lock_file"
}

run_with_timeout() {
    local duration="$1"
    shift

    if command -v timeout >/dev/null 2>&1; then
        timeout "$duration" "$@"
    else
        log "⚠️ 'timeout' command not found; running without explicit limit for $1"
        "$@"
    fi
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

    run_with_timeout "$timeout_duration" "$@"
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

# Function to notify about validation completion
notify_validation_completion() {
    local pr_number="$1"
    local status="$2"  # success, failure, timeout
    local details="$3"

    case "$status" in
        "success")
            log "✅ Comment validation completed successfully for PR #$pr_number"
            ;;
        "failure")
            log "❌ Comment validation failed for PR #$pr_number. Details: $details"
            ;;
        "timeout")
            log "⏰ Comment validation timed out for PR #$pr_number after ${COMMENT_TIMEOUT}s"
            ;;
        *)
            log "📝 Comment validation completed with status: $status for PR #$pr_number"
            ;;
    esac
}

# Post comment asking AI bots to review PR
post_ai_bot_review_request() {
    local pr_number="$1"

    log "💬 Requesting AI bot reviews for PR #$pr_number"

    # Check if comment already posted for current commit (similar to Codex check)
    local pr_state_json
    local head_sha=""
    local should_skip=false

    if pr_state_json=$(gh pr view "$pr_number" --repo "$GH_REPO" --json headRefOid,comments 2>/dev/null); then
        head_sha=$(echo "$pr_state_json" | jq -r '.headRefOid // ""')

        if [ -z "$head_sha" ]; then
             log "⚠️ Unable to determine head SHA for PR #$pr_number; skipping to avoid marker-less comment"
             notify_validation_completion "$pr_number" "failure" "Could not determine head SHA"
             return 1
        fi
        
        # Check if we already posted a comment with marker for this commit
        local marker="<!-- comment-validation-commit:$head_sha -->"
        if echo "$pr_state_json" | jq -r '.comments[]?.body // ""' | grep -qF "$marker"; then
            log "♻️ Comment validation already posted for commit $head_sha on PR #$pr_number; skipping"
            notify_validation_completion "$pr_number" "success" ""
            return 0
        fi
    else
        log "⚠️ Unable to fetch PR state; proceeding with comment (no idempotency check)"
        # Proceed without marker - transient gh pr view failures shouldn't block posting
        head_sha=""
    fi

    # Comment asking AI bots (not Codex) to review
    local comment_body="Please review this PR for bugs, security issues, and ensure all review comments are properly addressed.

@coderabbit-ai @greptileai @bugbot @copilot

Please check:
- Serious bugs and security vulnerabilities
- All unresolved review comments have been addressed
- Code quality and best practices"

    # Add marker if we have head_sha
    if [ -n "$head_sha" ]; then
        comment_body=$(printf "%s\n\n<!-- comment-validation-commit:%s -->" "$comment_body" "$head_sha")
    fi

    local tmp_body
    tmp_body=$(mktemp)
    printf "%s" "$comment_body" > "$tmp_body"

    execute_with_timeout "$COMMENT_TIMEOUT" "$pr_number" "AI bot review request comment" \
        gh pr comment "$pr_number" --repo "$GH_REPO" --body-file "$tmp_body"
    local comment_result=$?

    rm -f "$tmp_body"

    case $comment_result in
        0)
            notify_validation_completion "$pr_number" "success" ""
            ;;
        2)
            notify_validation_completion "$pr_number" "timeout" ""
            ;;
        *)
            notify_validation_completion "$pr_number" "failure" "AI bot review request comment failed"
            ;;
    esac

    return $comment_result
}

# Main processing logic
log "🚀 Starting comment validation processing"

# Get PRs updated in last 24 hours (excluding drafts)
RECENT_PRS=$(gh pr list --repo "$GH_REPO" --state open --limit 20 --json number,updatedAt,isDraft | \
    jq -r '.[] | select(.isDraft == false) | select((.updatedAt | fromdateiso8601) > (now - 86400)) | .number')

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

    # Comment validation automation
    ATTEMPT_COUNT=$(get_validation_attempts "$PR")

    log "💬 Processing PR #$PR for comment validation (attempt count: $ATTEMPT_COUNT)"

    if [ $ATTEMPT_COUNT -lt $MAX_VALIDATION_ATTEMPTS ]; then
        # Attempt to post AI bot review request
        NEW_ATTEMPT_COUNT=$(increment_validation_attempts "$PR")
        log "💬 Validation attempt $NEW_ATTEMPT_COUNT/$MAX_VALIDATION_ATTEMPTS for PR #$PR"

        post_ai_bot_review_request "$PR"
        result=$?

        if [ $result -eq 0 ]; then
            # Processing succeeded - mark as completed
            TIMESTAMP=$(date +%s)
            write_processed_timestamp "$PR" "$TIMESTAMP"
            reset_validation_attempts "$PR"
            log "✅ Successfully posted AI bot review request for PR #$PR"
            PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
        elif [ $result -eq 2 ]; then
            # Timeout - don't count as failure, will retry later
            log "⏰ Validation attempt $NEW_ATTEMPT_COUNT timed out for PR #$PR - will retry next cycle"
            # Decrement attempt count since timeout shouldn't count as attempt
            DECREMENTED_COUNT=$((NEW_ATTEMPT_COUNT - 1))
            if [ $DECREMENTED_COUNT -lt 0 ]; then
                DECREMENTED_COUNT=0
            fi
            if [ $DECREMENTED_COUNT -gt 0 ]; then
                grep -v "^$PR:" "$ATTEMPT_FILE" > "${ATTEMPT_FILE}.tmp" 2>/dev/null || true
                echo "$PR:$DECREMENTED_COUNT" >> "${ATTEMPT_FILE}.tmp"
                mv "${ATTEMPT_FILE}.tmp" "$ATTEMPT_FILE"
            else
                reset_validation_attempts "$PR"
            fi
        else
            log "❌ Validation attempt $NEW_ATTEMPT_COUNT failed for PR #$PR"
        fi
    else
        # Max attempts reached - send email notification
        log "📧 Max validation attempts reached for PR #$PR - sending email notification"
        send_email_notification "$PR" "validation_max_attempts" "Could not complete validation after $ATTEMPT_COUNT attempts" "$ATTEMPT_COUNT"

        # Reset attempts to allow future processing
        reset_validation_attempts "$PR"
    fi
done

log "🏁 Comment validation processing complete (processed: $PROCESSED_COUNT)"
