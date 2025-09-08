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
LOG_FILE="$SECURE_TEMP/claude_backup_$(date +%Y%m%d).log"

# Source directory
SOURCE_DIR="$HOME/.claude"

# Exit codes
SUCCESS=0
ERROR=1
PARTIAL_SUCCESS=23

# Security: Hostname validation function
validate_hostname() {
    local host="$1"
    if [[ ! "$host" =~ ^[a-zA-Z0-9.-]+$ ]]; then
        echo "ERROR: Invalid hostname detected: $host" >&2
        return 1
    fi
    return 0
}

# Security: Path validation function to prevent path traversal attacks
validate_path() {
    local path="$1"
    local context="$2"

    # Check for path traversal patterns
    if [[ "$path" =~ \.\./|/\.\. ]]; then
        echo "ERROR: Path traversal attempt detected in $context: $path" >&2
        return 1
    fi

    # Check for null bytes.
    # Previous approach used a regex to detect null bytes, but this could
    # incorrectly flag valid paths containing certain escape sequences or binary data,
    # resulting in false positives. This approach uses byte length comparison for reliability.
    if [ "${#path}" -ne "$(printf '%s' "$path" | wc -c)" ]; then
        echo "ERROR: Null byte detected in $context: $path" >&2
        return 1
    fi

    # Canonicalize path if it exists, otherwise validate parent
    local canonical_path
    if [[ -e "$path" ]]; then
        canonical_path=$(realpath "$path" 2>/dev/null)
        if [[ $? -ne 0 ]]; then
            echo "ERROR: Failed to canonicalize existing path in $context: $path" >&2
            return 1
        fi
    else
        # For non-existing paths, validate the parent directory structure
        local parent_dir=$(dirname "$path")
        if [[ -e "$parent_dir" ]]; then
            canonical_path=$(realpath "$parent_dir" 2>/dev/null)
            if [[ $? -ne 0 ]]; then
                echo "ERROR: Failed to canonicalize parent directory in $context: $parent_dir" >&2
                return 1
            fi
        fi
    fi

    # Path validation completed successfully
    return 0
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

# Initialize backup destination - called lazily to prevent sourcing issues
init_destination() {
    DEVICE_NAME="$(get_clean_hostname)" || return 1
    
    # Platform-specific default backup directories
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: Use CloudStorage Dropbox path
        DEFAULT_BACKUP_DIR="$HOME/Library/CloudStorage/Dropbox/claude_backup_$DEVICE_NAME"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        # Linux/Ubuntu: Try common Dropbox locations, fallback to Documents
        if [ -d "$HOME/Dropbox" ]; then
            DEFAULT_BACKUP_DIR="$HOME/Dropbox/claude_backup_$DEVICE_NAME"
        elif [ -d "$HOME/Documents" ]; then
            DEFAULT_BACKUP_DIR="$HOME/Documents/claude_backup_$DEVICE_NAME"
        else
            DEFAULT_BACKUP_DIR="$HOME/claude_backup_$DEVICE_NAME"
        fi
    else
        # Other systems: fallback to home directory
        DEFAULT_BACKUP_DIR="$HOME/claude_backup_$DEVICE_NAME"
    fi

    if [ -n "${1:-}" ] && [[ "${1:-}" != --* ]]; then
        # Parameter provided and it's not a flag - append device suffix
        # Security: Validate input parameter to prevent path traversal
        validate_path "${1}" "command line destination parameter" || return 2
        BACKUP_DESTINATION="${1%/}/claude_backup_$DEVICE_NAME"
    else
        # No parameter or it's a flag - use env base dir (if set) WITH device suffix, else default
        if [ -n "${DROPBOX_DIR:-}" ]; then
            # Security: Validate environment variable path
            validate_path "${DROPBOX_DIR}" "DROPBOX_DIR environment variable" || return 2
            BACKUP_DESTINATION="${DROPBOX_DIR%/}/claude_backup_$DEVICE_NAME"
        else
            BACKUP_DESTINATION="$DEFAULT_BACKUP_DIR"
        fi
    fi

    # Security: Validate final destination path
    validate_path "$BACKUP_DESTINATION" "final backup destination" || return 2
}

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

# Logging function (renamed to avoid conflict with system log command)
backup_log() {
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

    # First, backup ~/.claude directory with selective rsync
    local rsync_log="$SECURE_TEMP/rsync_${dest_name}_$(date +%Y%m%d_%H%M%S).log"
    local rsync_errors="$SECURE_TEMP/rsync_errors_${dest_name}_$(date +%Y%m%d_%H%M%S).log"

    # Run rsync with proper error logging and extended attributes support
    # Note: macOS rsync doesn't support --log-file, so we capture verbose output instead
    rsync -av \
        --xattrs \
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
        "$SOURCE_DIR/" "$dest_dir/.claude/" > "$rsync_log" 2>"$rsync_errors"

    local rsync_exit=$?

    if [ $rsync_exit -eq 0 ]; then
        # Complete success
        backup_log "rsync completed successfully for .claude directory"
    elif [ $rsync_exit -eq 23 ]; then
        # Partial transfer due to errors - log specific failures
        local failed_count=$(grep -c "failed:" "$rsync_errors" 2>/dev/null || echo "0")
        backup_log "rsync partial transfer: $failed_count files failed"
        backup_log "Failed files details:"
        cat "$rsync_errors" >> "$LOG_FILE" 2>/dev/null
        add_result "WARNING" "$dest_name Rsync" "Partial transfer: $failed_count files failed (see log for details)"
    elif [ $rsync_exit -ne 0 ]; then
        # Complete failure
        backup_log "rsync failed with exit code $rsync_exit"
        backup_log "Error details:"
        cat "$rsync_errors" >> "$LOG_FILE" 2>/dev/null
        add_result "ERROR" "$dest_name Backup" "rsync failed with exit code $rsync_exit (see log for details)"
        return 1
    fi

    # Continue with second rsync for .claude.json files if first was successful or partial
    if [ $rsync_exit -eq 0 ] || [ $rsync_exit -eq 23 ]; then

        # Second, backup ~/.claude.json files from home directory
        local rsync_log2="$SECURE_TEMP/rsync_claude_json_${dest_name}_$(date +%Y%m%d_%H%M%S).log"
        local rsync_errors2="$SECURE_TEMP/rsync_errors_claude_json_${dest_name}_$(date +%Y%m%d_%H%M%S).log"

        rsync -av \
            --xattrs \
            --include='.claude.json' \
            --include='.claude.json.backup*' \
            --exclude='*' \
            "$HOME/" "$dest_dir/" > "$rsync_log2" 2>"$rsync_errors2"

        local rsync_exit2=$?
        local file_count=$(find "$dest_dir" -type f | wc -l)

        if [ $rsync_exit2 -eq 0 ]; then
            backup_log "rsync completed successfully for .claude.json files"
            if [ $rsync_exit -eq 0 ]; then
                add_result "SUCCESS" "$dest_name Backup" "Synced to $dest_dir ($file_count files)"
                return $SUCCESS
            else
                add_result "PARTIAL" "$dest_name Backup" "Partial sync to $dest_dir ($file_count files, some .claude directory files failed)"
                return $PARTIAL_SUCCESS
            fi
        elif [ $rsync_exit2 -eq 23 ]; then
            local failed_count2=$(grep -c "failed:" "$rsync_errors2" 2>/dev/null || echo "0")
            backup_log "rsync partial transfer for .claude.json: $failed_count2 files failed"
            cat "$rsync_errors2" >> "$LOG_FILE" 2>/dev/null
            add_result "WARNING" "$dest_name .claude.json Backup" "Partial transfer: $failed_count2 .claude.json files failed"
            add_result "PARTIAL" "$dest_name Backup" "Partial sync to $dest_dir ($file_count files)"
            return $PARTIAL_SUCCESS
        else
            backup_log "rsync failed for .claude.json files with exit code $rsync_exit2"
            cat "$rsync_errors2" >> "$LOG_FILE" 2>/dev/null
            add_result "ERROR" "$dest_name .claude.json Backup" "Complete failure of .claude.json backup (exit code $rsync_exit2)"
            add_result "PARTIAL" "$dest_name Backup" "Main .claude directory synced, but .claude.json files completely failed"
            return $ERROR
        fi
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
- Verify backup path (macOS): ls -la "$HOME/Library/CloudStorage/Dropbox"
- Verify backup path (Linux): ls -la "$HOME/Dropbox" or "$HOME/Documents"
- Verify rsync installation: which rsync
- Check source directory: ls -la $SOURCE_DIR
- Review full log: cat $LOG_FILE

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

    # Initialize backup destination
    if ! init_destination "$@"; then
        backup_log "Destination initialization failed"
        BACKUP_STATUS="FAILURE"
        local report_file
        report_file="$(generate_failure_email)"
        send_failure_email "$report_file"
        return 1
    fi

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
    $0 [destination]              # Run backup to destination (default: ~/Library/CloudStorage/Dropbox/claude_backup_HOSTNAME)
    $0 --setup-cron [destination] # Setup cron job with destination
    $0 --remove-cron             # Remove cron job
    $0 --help                    # Show this help

EMAIL SETUP (for failure alerts):
    export EMAIL_USER="your-email@gmail.com"
    export EMAIL_PASS="your-gmail-app-password"
    export BACKUP_EMAIL="your-email@gmail.com"

    For Gmail App Password: https://myaccount.google.com/apppasswords

BACKUP TARGETS:
    Source: ~/.claude/ + ~/.claude.json* (dual selective sync)
    Default (macOS): ~/Library/CloudStorage/Dropbox/claude_backup_HOSTNAME
    Default (Linux): ~/Dropbox/claude_backup_HOSTNAME or ~/Documents/claude_backup_HOSTNAME
    Custom: Specify any destination as first parameter

SELECTIVE SYNC INCLUDES:
    ✅ ~/.claude.json (Claude Code configuration file - 1.7MB)
    ✅ ~/.claude.json.backup* (configuration backups)
    ✅ ~/.claude/settings.json (Claude Code configuration)
    ✅ ~/.claude/projects/ (all project sessions - 2.4GB)
    ✅ ~/.claude/local/ (Claude installations and packages - 179MB)
    ✅ ~/.claude/hooks/ (custom hooks)
    ❌ Excludes: shell-snapshots, todos, conversations, cache files

FEATURES:
    ✅ Automated backups via cron every hour (0 * * * *)
    ✅ rsync selective sync (no --delete for safety)
    ✅ Email alerts on backup failures only
    ✅ Selective sync of essential data only
    ✅ Comprehensive logging

LOGS:
    Backup: $SECURE_TEMP/claude_backup_YYYYMMDD.log (secure)
    Cron:   $PROJECT_ROOT/tmp/claude_backup_cron.log (secure)
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
    local cron_destination="$2"

    # If no destination provided, extract base directory to avoid double suffix bug
    # The main script always appends the device suffix, so we must pass the parent directory
    # Example problem: DEFAULT_BACKUP_DIR="/path/claude_backup_device" + main script suffix = "/path/claude_backup_device/claude_backup_device"
    if [[ -z "$cron_destination" ]]; then
        cron_destination="$(extract_base_directory "$BACKUP_DESTINATION")"
        if [[ $? -ne 0 ]] || [[ -z "$cron_destination" ]]; then
            echo "Error: Failed to extract base directory from $BACKUP_DESTINATION" >&2
            return 1
        fi
    fi

    echo "Setting up 4-hour Claude backup cron job with device-specific naming..."

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

    # Add new cron job for hourly backup (handle empty crontab gracefully)
    # Security: Use deterministic secure log path accessible from cron
    local cron_entry="0 * * * * $wrapper_script 2>&1"
    {
        crontab -l 2>/dev/null || true
        echo "$cron_entry"
    } | crontab -

    echo "✅ Cron job setup complete!"
    echo "   Schedule: Every hour (0 * * * *)"
    echo "   Script: $wrapper_script"
    echo "   Destination: $cron_destination"
    echo "   Device suffix: $DEVICE_NAME"
    echo "   Log: Handled by cron wrapper script (secure location)"
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
    # Auto-report on unexpected errors during CLI execution
    on_error() {
        local exit_code=$?
        local line_number=$1

        # Create error report file for email notification
        local error_report="$SECURE_TEMP/error_report_$(date +%s).txt"
        {
            echo "UNEXPECTED SCRIPT FAILURE"
            echo "========================"
            echo "Script: $(basename "${BASH_SOURCE[0]}")"
            echo "Line: $line_number"
            echo "Exit Code: $exit_code"
            echo "Time: $(date)"
            echo "Command: ${BASH_COMMAND:-unknown}"
        } > "$error_report"

        add_result "ERROR" "Unexpected Failure" "Script failed at line $line_number with exit code $exit_code"
        send_failure_email "$error_report" 2>/dev/null || true  # Use correct function name with parameter
        exit $exit_code
    }
    trap 'on_error $LINENO' ERR

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
            run_backup "$@"
            ;;
    esac
fi
