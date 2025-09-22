#!/bin/bash

# Claude Directory Backup Script
# Backs up ~/.claude to Dropbox folder with device-specific naming
# Runs hourly via cron and sends email alerts on failure
#
# USAGE:
#   ./claude_backup.sh [destination]              # Run backup to specified destination
#   ./claude_backup.sh --setup-cron [destination] # Setup cron job with destination
#   ./claude_backup.sh --remove-cron             # Remove cron job
#   ./claude_backup.sh --help                    # Show help
#
# EMAIL SETUP:
#   export EMAIL_USER="your-email@gmail.com"
#   export EMAIL_PASS="your-gmail-app-password"
#   export BACKUP_EMAIL="your-email@gmail.com"  # Where to send failure alerts

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Security: Create secure temp directory with proper permissions (700)
SECURE_TEMP=$(mktemp -d)
chmod 700 "$SECURE_TEMP"
LOG_FILE="$SECURE_TEMP/claude_backup_$(date +%Y%m%d).backup_log"

# Logging function (defined early to avoid ordering issues)
backup_log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
}

# Source directory
SOURCE_DIR="$HOME/.claude"

# Security: Hostname validation function
validate_hostname() {
    local host="$1"
    if [[ ! "$host" =~ ^[a-zA-Z0-9.-]+$ ]]; then
        backup_log "ERROR: Invalid hostname detected: $host"
        exit 1
    fi
}

# Security: Path validation function to prevent path traversal attacks
validate_path() {
    local path="$1"
    local context="$2"

    # Check for path traversal patterns (fixed regex)
    if [[ "$path" =~ \.\./ ]] || [[ "$path" =~ /\.\. ]]; then
        backup_log "ERROR: Path traversal attempt detected in $context: $path"
        exit 1
    fi

    # Check for null bytes (fixed detection method)
    if [[ -n "$path" && ${#path} -ne $(printf '%s' "$path" | wc -c) ]]; then
        backup_log "ERROR: Null byte detected in $context: $path"
        exit 1
    fi

    # Canonicalize path if it exists, otherwise validate parent
    local canonical_path
    if [[ -e "$path" ]]; then
        canonical_path=$(realpath "$path" 2>/dev/null)
        if [[ $? -ne 0 ]]; then
            backup_log "ERROR: Failed to canonicalize existing path in $context: $path"
            exit 1
        fi
    else
        # For non-existing paths, validate the parent directory structure
        local parent_dir=$(dirname "$path")
        if [[ -e "$parent_dir" ]]; then
            canonical_path=$(realpath "$parent_dir" 2>/dev/null)
            if [[ $? -ne 0 ]]; then
                backup_log "ERROR: Failed to canonicalize parent directory in $context: $parent_dir"
                exit 1
            fi
        fi
    fi

    # Path validation successful (removed backup_log call to fix ordering issue)
}

# Portable function to get cleaned hostname (Mac and PC compatible)
get_clean_hostname() {
    local HOSTNAME=""

    # Try Mac-specific way first
    if command -v scutil >/dev/null 2>&1; then
        # Mac: Use LocalHostName if set, otherwise fallback to hostname
        HOSTNAME=$(scutil --get LocalHostName 2>/dev/null)
        if [ -z "$HOSTNAME" ]; then
            HOSTNAME=$(hostname)
        fi
    else
        # Non-Mac: Use hostname
        HOSTNAME=$(hostname)
    fi

    # Security: Validate hostname to prevent shell injection
    validate_hostname "$HOSTNAME"

    # Clean up: lowercase, replace spaces with '-'
    echo "$HOSTNAME" | tr ' ' '-' | tr '[:upper:]' '[:lower:]'
}

# Use hardcoded folder name for consistency across all devices
BACKUP_FOLDER_NAME="claude_conversations"

# Destination directory - now supports parameter override with consistent folder name
# If parameter provided, append folder name to it, otherwise use default
DEFAULT_BACKUP_DIR="$HOME/Library/CloudStorage/Dropbox/$BACKUP_FOLDER_NAME"
if [ -n "${1:-}" ] && [[ "${1:-}" != --* ]]; then
    # Parameter provided and it's not a flag - append device suffix
    # Security: Validate input parameter to prevent path traversal
    validate_path "${1}" "command line destination parameter"
    BACKUP_DESTINATION="${1%/}/$BACKUP_FOLDER_NAME"
else
    # No parameter or it's a flag - use env base dir (if set) WITH device suffix, else default
    if [ -n "${DROPBOX_DIR:-}" ]; then
        # Security: Validate environment variable path
        validate_path "${DROPBOX_DIR}" "DROPBOX_DIR environment variable"
        BACKUP_DESTINATION="${DROPBOX_DIR%/}/$BACKUP_FOLDER_NAME"
    else
        BACKUP_DESTINATION="$DEFAULT_BACKUP_DIR"
    fi
fi

# Security: Validate final destination path
validate_path "$BACKUP_DESTINATION" "final backup destination"

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

# (backup_log function moved to top of script)

# Add backup result
add_result() {
    local status="$1"
    local operation="$2"
    local details="$3"

    BACKUP_RESULTS+=("$status|$operation|$details")

    if [ "$status" != "SUCCESS" ]; then
        BACKUP_STATUS="FAILURE"
    fi

    backup_log "$status: $operation - $details"
}

# Check prerequisites
check_prerequisites() {
    backup_log "=== Checking Prerequisites ==="

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

    backup_log "=== Backing up to $dest_name ==="

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
    # Security: Use secure temp directory instead of world-readable /tmp
    local report_file="$SECURE_TEMP/claude_backup_failure_$(date +%Y%m%d_%H%M%S).txt"

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
Backup Destination: $BACKUP_DESTINATION
Log File: $LOG_FILE

TROUBLESHOOTING:
===============
- Verify macOS CloudStorage path: ls -la "$HOME/Library/CloudStorage/Dropbox"
- Verify rsync installation: which rsync
- Check source directory: ls -la $SOURCE_DIR
- Review full backup_log: cat $LOG_FILE

========================================
Generated by Claude Backup System
Scheduled every hour via cron (0 * * * *)
========================================
EOF

    echo "$report_file"
}

# Send failure email notification
send_failure_email() {
    local report_file="$1"

    backup_log "=== Sending Failure Email Notification ==="

    # Check if email credentials are configured
    if [ -z "${EMAIL_USER:-}" ] || [ -z "${EMAIL_PASS:-}" ] || [ -z "${BACKUP_EMAIL:-}" ]; then
        add_result "WARNING" "Email Config" "Email credentials not configured - saving report only"
        backup_log "Failure report saved to: $report_file"
        return
    fi

    # Try to send email using curl with Gmail SMTP
    if command -v curl >/dev/null 2>&1; then
        if curl --url "smtp://$SMTP_SERVER:$SMTP_PORT" \
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
    backup_log "Starting Claude backup at $(date)"

    # Check prerequisites
    if ! check_prerequisites; then
        backup_log "Prerequisites check failed, aborting backup"
        return 1
    fi

    # Backup to specified destination
    backup_to_destination "$BACKUP_DESTINATION" "Backup"

    # Send email notification only on failure
    if [ "$BACKUP_STATUS" != "SUCCESS" ]; then
        local report_file=$(generate_failure_email)
        send_failure_email "$report_file"
    fi

    backup_log "Claude backup completed with status: $BACKUP_STATUS"

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
Claude Directory Backup Script (runs every 4 hours by default)

USAGE:
    $0 [destination]              # Run backup to destination (default: ~/Library/CloudStorage/Dropbox/claude_conversations)
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
    Default: ~/Library/CloudStorage/Dropbox/claude_conversations
    Custom: Specify any destination as first parameter

SELECTIVE SYNC INCLUDES:
    ✅ settings.json (Claude Code configuration)
    ✅ projects/ (all project sessions - 2.4GB)
    ✅ local/ (Claude installations and packages - 179MB)
    ✅ hooks/ (custom hooks)
    ❌ Excludes: shell-snapshots, todos, conversations, cache files

FEATURES:
    ✅ Automated backups via cron every hour (0 * * * *)
    ✅ rsync selective sync (no --delete for safety)
    ✅ Email alerts on backup failures only
    ✅ Selective sync of essential data only
    ✅ Comprehensive backup_logging

LOGS:
    Backup: $SECURE_TEMP/claude_backup_YYYYMMDD.backup_log (secure)
    Cron: $SECURE_TEMP/claude_backup_cron.backup_log (secure)
    Alerts: ./tmp/backup_alerts/ (when email fails)

From: claude-backup@worldarchitect.ai
EOF
}

# Helper function to extract parent directory of suffixed backup path
# This prevents the double suffix bug when setting up cron without explicit destination
extract_base_directory() {
    local suffixed_path="$1"

    # Validate input
    if [[ -z "$suffixed_path" ]]; then
        echo "Error: No path provided to extract_base_directory" >&2
        return 1
    fi

    # Use dirname to get parent directory
    local base_dir
    base_dir="$(dirname "$suffixed_path")"

    # Validate result
    if [[ -z "$base_dir" ]] || [[ "$base_dir" == "." ]]; then
        echo "Error: Failed to extract base directory from $suffixed_path" >&2
        return 1
    fi

    echo "$base_dir"
    return 0
}

# Setup cron job
setup_cron() {
    local cron_destination="${2:-}"

    # If no destination provided, extract base directory to avoid double suffix bug
    # The main script always appends the device suffix, so we must pass the parent directory
    # Example problem: DEFAULT_BACKUP_DIR="/path/claude_conversations" + main script suffix = "/path/claude_conversations/claude_conversations"
    if [[ -z "$cron_destination" ]]; then
        cron_destination="$(extract_base_directory "$BACKUP_DESTINATION")"
        if [[ $? -ne 0 ]] || [[ -z "$cron_destination" ]]; then
            echo "Error: Failed to extract base directory from $BACKUP_DESTINATION" >&2
            return 1
        fi
    fi

    echo "Setting up hourly Claude backup cron job with consistent folder naming..."

    # Create wrapper script for cron environment
    local wrapper_script="$SCRIPT_DIR/claude_backup_cron.sh"
    cat > "$wrapper_script" << EOF
#!/bin/bash
# Cron wrapper for claude backup enhanced with secure credential handling
export PATH="/usr/local/bin:/usr/bin:/bin:\$PATH"
export SHELL="/bin/bash"

# Security: Use secure credential retrieval instead of environment variables
# Credentials should be stored securely using the system keychain/credential manager
get_secure_credential() {
    local key="\$1"
    # Try macOS keychain first
    if command -v security >/dev/null 2>&1; then
        security find-generic-password -s "claude-backup-\$key" -w 2>/dev/null || echo ""
    elif command -v secret-tool >/dev/null 2>&1; then
        # Linux Secret Service
        secret-tool lookup service "claude-backup" key "\$key" 2>/dev/null || echo ""
    else
        # Fallback to environment variables (less secure)
        case "\$key" in
            user) echo "\${EMAIL_USER:-}" ;;
            pass) echo "\${EMAIL_PASS:-}" ;;
            email) echo "\${BACKUP_EMAIL:-}" ;;
        esac
    fi
}

# Get credentials securely
export EMAIL_USER=\$(get_secure_credential "user")
export EMAIL_PASS=\$(get_secure_credential "pass")
export BACKUP_EMAIL=\$(get_secure_credential "email")

cd "$PROJECT_ROOT"
exec "$SCRIPT_DIR/claude_backup.sh" "$cron_destination"
EOF
    chmod +x "$wrapper_script"

    # Remove existing cron job if it exists (handle empty crontab gracefully)
    if crontab -l >/dev/null 2>&1; then
        (crontab -l | grep -v "claude_backup") | crontab - 2>/dev/null || true
    fi

    # Add new cron job for every 4 hours (handle empty crontab gracefully)
    # Security: Use secure temp directory for backup_logs
    local cron_entry="0 * * * * $wrapper_script > \$SECURE_TEMP/claude_backup_cron.backup_log 2>&1"
    {
        crontab -l 2>/dev/null || true
        echo "$cron_entry"
    } | crontab -

    echo "✅ Cron job setup complete!"
    echo "   Schedule: Every hour (0 * * * *)"
    echo "   Script: $wrapper_script"
    echo "   Destination: $cron_destination"
    echo "   Backup folder: $BACKUP_FOLDER_NAME"
    echo "   Log: \$SECURE_TEMP/claude_backup_cron.backup_log (secure location)"
    echo ""
    echo "To configure failure email alerts:"
    echo "   export EMAIL_USER=\"your-email@gmail.com\""
    echo "   export EMAIL_PASS=\"your-gmail-app-password\""
    echo "   export BACKUP_EMAIL=\"your-email@gmail.com\""
}

# Remove cron job
remove_cron() {
    echo "Removing Claude backup cron job..."
    (crontab -l 2>/dev/null || true) | grep -v "claude_backup" | crontab - 2>/dev/null || true

    # Remove wrapper script
    local wrapper_script="$SCRIPT_DIR/claude_backup_cron.sh"
    rm -f "$wrapper_script"

    echo "✅ Cron job removed"
}

# Only run CLI when script is executed directly (not when sourced)
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
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
            echo "Error: Unknown option '$1'" >&2
            echo "Use --help for usage information" >&2
            show_help >&2
            exit 2
            ;;
        *)
            # Run backup (default or with destination parameter)
            run_backup
            ;;
    esac
fi
