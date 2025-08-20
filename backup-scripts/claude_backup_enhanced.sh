#!/bin/bash

# Claude Directory Backup Script
# Backs up ~/.claude to Dropbox folder (synced by both Dropbox and Google Drive)
# Runs hourly via cron and sends email alerts on failure
#
# USAGE:
#   ./claude_backup_enhanced.sh [destination]              # Run backup to specified destination
#   ./claude_backup_enhanced.sh --setup-cron [destination] # Setup cron job with destination
#   ./claude_backup_enhanced.sh --remove-cron             # Remove cron job
#   ./claude_backup_enhanced.sh --help                    # Show help
#
# EMAIL SETUP:
#   export EMAIL_USER="your-email@gmail.com"
#   export EMAIL_PASS="your-gmail-app-password"
#   export BACKUP_EMAIL="your-email@gmail.com"  # Where to send failure alerts

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="/tmp/claude_backup_$(date +%Y%m%d).log"

# Source directory
SOURCE_DIR="$HOME/.claude"

# Get device name for backup folder suffix
DEVICE_NAME=$(hostname -s | tr ' ' '-' | tr '[:upper:]' '[:lower:]')

# Destination directory - now supports parameter override
# If parameter provided, append device suffix to it, otherwise use default
DEFAULT_BACKUP_DIR="$HOME/Library/CloudStorage/Dropbox/claude_backup_$DEVICE_NAME"
if [ -n "${1:-}" ] && [[ "${1:-}" != --* ]]; then
    # Parameter provided and it's not a flag - append device suffix
    BACKUP_DESTINATION="${1%/}/claude_backup_$DEVICE_NAME"
else
    # No parameter or it's a flag - use default or environment variable
    BACKUP_DESTINATION="${DROPBOX_DIR:-$DEFAULT_BACKUP_DIR}"
fi

# Email configuration
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
EMAIL_FROM="claude-backup@worldarchitect.ai"
# Set these environment variables:
# export EMAIL_USER="your-email@gmail.com"
# export EMAIL_PASS="your-app-password"
# export BACKUP_EMAIL="your-email@gmail.com"

# Backup results
BACKUP_STATUS="SUCCESS"
declare -a BACKUP_RESULTS=()

# Logging function
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
}

# Add backup result
add_result() {
    local status="$1"
    local operation="$2"
    local details="$3"

    BACKUP_RESULTS+=("$status|$operation|$details")

    if [ "$status" != "SUCCESS" ]; then
        BACKUP_STATUS="FAILURE"
    fi

    log "$status: $operation - $details"
}

# Check prerequisites
check_prerequisites() {
    log "=== Checking Prerequisites ==="

    # Check if source directory exists
    if [ ! -d "$SOURCE_DIR" ]; then
        add_result "ERROR" "Source Check" "Claude directory $SOURCE_DIR does not exist"
        return 1
    fi

    add_result "SUCCESS" "Source Check" "Claude directory found at $SOURCE_DIR"

    # Check if rsync is available
    if ! command -v rsync >/dev/null 2>&1; then
        add_result "ERROR" "Prerequisites" "rsync command not available"
        return 1
    fi

    add_result "SUCCESS" "Prerequisites" "rsync command available"

    # Check destination parent directory exists or can be created
    local parent_dir=$(dirname "$BACKUP_DESTINATION")
    if [ ! -d "$parent_dir" ]; then
        if ! mkdir -p "$parent_dir" 2>/dev/null; then
            add_result "WARNING" "Destination Path" "Parent directory $parent_dir not accessible"
        else
            add_result "SUCCESS" "Destination Path" "Parent directory created at $parent_dir"
        fi
    else
        add_result "SUCCESS" "Destination Path" "Parent directory accessible at $parent_dir"
    fi
}

# Perform rsync backup
backup_to_destination() {
    local dest_dir="$1"
    local dest_name="$2"

    log "=== Backing up to $dest_name ==="

    # Create destination directory if it doesn't exist
    if ! mkdir -p "$dest_dir" 2>/dev/null; then
        add_result "ERROR" "$dest_name Backup" "Failed to create destination directory: $dest_dir"
        return 1
    fi

    # Perform selective rsync backup (only essential directories and files)
    if rsync -av \
        --include='settings.json' \
        --include='settings.json.backup*' \
        --include='settings.local.json' \
        --include='projects' \
        --include='projects/**' \
        --include='local' \
        --include='local/**' \
        --include='hooks' \
        --include='hooks/**' \
        --exclude='*' \
        "$SOURCE_DIR/" "$dest_dir/" >/dev/null 2>&1; then

        local file_count=$(find "$dest_dir" -type f | wc -l)
        add_result "SUCCESS" "$dest_name Backup" "Synced to $dest_dir ($file_count files)"
        return 0
    else
        add_result "ERROR" "$dest_name Backup" "rsync failed to $dest_dir"
        return 1
    fi
}

# Generate failure email report
generate_failure_email() {
    local report_file="/tmp/claude_backup_failure_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Subject: ALERT: Claude Backup Failure - $(date '+%Y-%m-%d %H:%M')
From: $EMAIL_FROM
To: ${BACKUP_EMAIL:-backup-alerts@worldarchitect.ai}

========================================
CLAUDE BACKUP FAILURE ALERT
$(date '+%Y-%m-%d %H:%M:%S')
========================================

BACKUP STATUS: $BACKUP_STATUS

DETAILED RESULTS:
================
EOF

    for result in "${BACKUP_RESULTS[@]}"; do
        IFS='|' read -r status operation details <<< "$result"
        printf "%-8s | %-20s | %s\n" "$status" "$operation" "$details" >> "$report_file"
    done

    cat >> "$report_file" << EOF

SUMMARY:
========
Source Directory: $SOURCE_DIR
Backup Target: $BACKUP_DESTINATION
Device: $DEVICE_NAME
Log File: $LOG_FILE

TROUBLESHOOTING:
===============
- Verify rsync installation: which rsync
- Check source directory: ls -la $SOURCE_DIR
- Check destination access: ls -la $(dirname "$BACKUP_DESTINATION")
- Review full log: cat $LOG_FILE

========================================
Generated by Claude Backup System
Run every hour via cron
========================================
EOF

    echo "$report_file"
}

# Send failure email notification
send_failure_email() {
    local report_file="$1"

    log "=== Sending Failure Email Notification ==="

    # Check if email credentials are configured
    if [ -z "${EMAIL_USER:-}" ] || [ -z "${EMAIL_PASS:-}" ] || [ -z "${BACKUP_EMAIL:-}" ]; then
        add_result "WARNING" "Email Config" "Email credentials not configured - saving report only"
        log "Failure report saved to: $report_file"
        return
    fi

    # Try to send email using curl with Gmail SMTP
    if command -v curl >/dev/null 2>&1; then
        if curl --url "smtps://$SMTP_SERVER:$SMTP_PORT" \
               --ssl-reqd \
               --mail-from "$EMAIL_USER" \
               --mail-rcpt "$BACKUP_EMAIL" \
               --user "$EMAIL_USER:$EMAIL_PASS" \
               --upload-file "$report_file" >/dev/null 2>&1; then
            add_result "SUCCESS" "Email Alert" "Failure notification sent successfully"
            return
        fi
    fi

    # Fallback: Save to project directory for manual review
    local manual_dir="$PROJECT_ROOT/tmp/backup_alerts"
    mkdir -p "$manual_dir"
    cp "$report_file" "$manual_dir/claude_backup_failure_$(date +%Y%m%d_%H%M%S).txt"
    add_result "WARNING" "Email Alert" "Email not sent - report saved to $manual_dir for manual review"
}

# Main backup function
run_backup() {
    log "Starting Claude backup at $(date)"

    # Check prerequisites
    if ! check_prerequisites; then
        log "Prerequisites check failed, aborting backup"
        return 1
    fi

    # Backup to specified destination
    backup_to_destination "$BACKUP_DESTINATION" "Backup"

    # Send email notification only on failure
    if [ "$BACKUP_STATUS" != "SUCCESS" ]; then
        local report_file=$(generate_failure_email)
        send_failure_email "$report_file"
    fi

    log "Claude backup completed with status: $BACKUP_STATUS"

    # Return appropriate exit code
    if [ "$BACKUP_STATUS" = "SUCCESS" ]; then
        return 0
    else
        return 1
    fi
}

# Show help
show_help() {
    cat << EOF
Claude Directory Backup Script with Hourly Cron

USAGE:
    $0 [destination]              # Run backup to destination (default: ~/Library/CloudStorage/Dropbox/claude_backup_$DEVICE_NAME)
    $0 --setup-cron [destination] # Setup cron job with destination
    $0 --remove-cron             # Remove cron job
    $0 --help                    # Show this help

EMAIL SETUP (for failure alerts):
    export EMAIL_USER="your-email@gmail.com"
    export EMAIL_PASS="your-gmail-app-password"
    export BACKUP_EMAIL="your-email@gmail.com"

    For Gmail App Password: https://myaccount.google.com/apppasswords

BACKUP TARGETS:
    Source: ~/.claude (selective sync)
    Default: ~/Library/CloudStorage/Dropbox/claude_backup_$DEVICE_NAME
    Custom: Specify any destination as first parameter

SELECTIVE SYNC INCLUDES:
    ✅ settings.json (Claude Code configuration)
    ✅ projects/ (all project sessions - 2.4GB)
    ✅ local/ (Claude installations and packages - 179MB)
    ✅ hooks/ (custom hooks)
    ❌ Excludes: shell-snapshots, todos, conversations, cache files

FEATURES:
    ✅ Hourly automated backups via cron
    ✅ rsync selective sync (no --delete for safety)
    ✅ Email alerts on backup failures only
    ✅ Selective sync of essential data only
    ✅ Comprehensive logging

LOGS:
    Backup: /tmp/claude_backup_YYYYMMDD.log
    Cron: /tmp/claude_backup_cron.log
    Alerts: ./tmp/backup_alerts/ (when email fails)

From: claude-backup@worldarchitect.ai
EOF
}

# Setup cron job
setup_cron() {
    local cron_destination="${2:-$BACKUP_DESTINATION}"
    echo "Setting up hourly Claude backup cron job..."

    # Create wrapper script for cron environment
    local wrapper_script="$SCRIPT_DIR/claude_backup_cron_enhanced.sh"
    cat > "$wrapper_script" << EOF
#!/bin/bash
# Cron wrapper for claude backup enhanced
export PATH="/usr/local/bin:/usr/bin:/bin:\$PATH"
export SHELL="/bin/bash"
# Load existing email credentials from .bashrc if available
if [ -f "\$HOME/.bashrc" ]; then
    source "\$HOME/.bashrc"
    export EMAIL_USER="\${TEST_EMAIL:-\$EMAIL_USER}"
    export EMAIL_PASS="\${TEST_PASSWORD:-\$EMAIL_PASS}"
    export BACKUP_EMAIL="\${TEST_EMAIL:-\$BACKUP_EMAIL}"
fi
cd "$PROJECT_ROOT"
exec "$SCRIPT_DIR/claude_backup_enhanced.sh" "$cron_destination"
EOF
    chmod +x "$wrapper_script"

    # Remove existing cron job if it exists
    (crontab -l 2>/dev/null | grep -v "claude_backup_enhanced") | crontab - 2>/dev/null || true

    # Add new cron job for every hour
    local cron_entry="0 * * * * $wrapper_script > /tmp/claude_backup_cron.log 2>&1"
    (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -

    echo "✅ Cron job setup complete!"
    echo "   Schedule: Every hour (0 * * * *)"
    echo "   Script: $wrapper_script"
    echo "   Destination: $cron_destination"
    echo "   Device suffix: $DEVICE_NAME"
    echo "   Log: /tmp/claude_backup_cron.log"
    echo ""
    echo "To configure failure email alerts:"
    echo "   export EMAIL_USER=\"your-email@gmail.com\""
    echo "   export EMAIL_PASS=\"your-gmail-app-password\""
    echo "   export BACKUP_EMAIL=\"your-email@gmail.com\""
}

# Remove cron job
remove_cron() {
    echo "Removing Claude backup cron job..."
    (crontab -l 2>/dev/null | grep -v "claude_backup_enhanced") | crontab - 2>/dev/null || true

    # Remove wrapper script
    local wrapper_script="$SCRIPT_DIR/claude_backup_cron_enhanced.sh"
    rm -f "$wrapper_script"

    echo "✅ Cron job removed"
}

# Parse command line arguments
case "${1:-}" in
    --setup-cron)
        setup_cron "$@"
        exit 0
        ;;
    --remove-cron)
        remove_cron
        exit 0
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
    --*)
        echo "Error: Unknown option '$1'"
        echo "Use --help for usage information"
        exit 1
        ;;
    *)
        # Run backup (default or with destination parameter)
        run_backup
        ;;
esac
