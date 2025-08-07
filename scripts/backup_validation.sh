#!/bin/bash

# Backup Validation Script with Cron Setup
# Validates memory backups and claude directory backups daily
# Sends email notifications with status from backup-checker@worldarchitect.ai
#
# USAGE:
#   ./backup_validation.sh                    # Run validation
#   ./backup_validation.sh --setup-cron      # Setup 4-hourly cron job
#   ./backup_validation.sh --remove-cron     # Remove cron job
#   ./backup_validation.sh --help            # Show help
#
# EMAIL SETUP:
#   export EMAIL_USER="your-email@gmail.com"
#   export EMAIL_PASS="your-gmail-app-password"
#
# For Gmail App Password: https://myaccount.google.com/apppasswords

set -euo pipefail

# Load configuration function
load_config() {
    local config_file="$SCRIPT_DIR/backup_validation.conf"
    local user_config="$HOME/.backup_validation.conf"
    
    # Load default configuration file
    if [ -f "$config_file" ]; then
        log "Loading configuration from $config_file"
        source "$config_file"
    else
        log "WARNING: Default config file not found at $config_file"
    fi
    
    # Load user-specific overrides if they exist
    if [ -f "$user_config" ]; then
        log "Loading user configuration overrides from $user_config"
        source "$user_config"
    fi
    
    # Validate critical configuration
    validate_config
}

# Validate configuration
validate_config() {
    local config_errors=0
    
    # Check required directories exist or can be created
    if [ -n "${DROPBOX_BACKUP_DIR:-}" ]; then
        local backup_parent=$(dirname "$DROPBOX_BACKUP_DIR")
        if [ ! -d "$backup_parent" ]; then
            log "ERROR: Backup parent directory does not exist: $backup_parent"
            config_errors=$((config_errors + 1))
        fi
    else
        log "ERROR: DROPBOX_BACKUP_DIR not configured"
        config_errors=$((config_errors + 1))
    fi
    
    # Check email service configuration
    if [ -z "${EMAIL_SERVICE:-}" ]; then
        log "WARNING: EMAIL_SERVICE not configured, defaulting to gmail"
        EMAIL_SERVICE="gmail"
    fi
    
    # Validate email service credentials based on service type
    case "${EMAIL_SERVICE:-gmail}" in
        gmail)
            if [ -z "${EMAIL_USER:-}" ] || [ -z "${EMAIL_PASS:-}" ]; then
                log "WARNING: Gmail credentials not configured (EMAIL_USER, EMAIL_PASS)"
            fi
            ;;
        mailgun)
            if [ -z "${MAILGUN_USERNAME:-}" ] || [ -z "${MAILGUN_PASSWORD:-}" ]; then
                log "WARNING: Mailgun credentials not configured (MAILGUN_USERNAME, MAILGUN_PASSWORD)"
            fi
            ;;
        sendgrid)
            if [ -z "${SENDGRID_API_KEY:-}" ]; then
                log "WARNING: SendGrid API key not configured (SENDGRID_API_KEY)"
            fi
            ;;
        ses)
            if [ -z "${AWS_SES_USERNAME:-}" ] || [ -z "${AWS_SES_PASSWORD:-}" ]; then
                log "WARNING: AWS SES credentials not configured (AWS_SES_USERNAME, AWS_SES_PASSWORD)"
            fi
            ;;
        sendmail)
            # No additional validation needed for sendmail
            ;;
        *)
            log "ERROR: Unknown email service: ${EMAIL_SERVICE}"
            config_errors=$((config_errors + 1))
            ;;
    esac
    
    if [ $config_errors -gt 0 ]; then
        log "CRITICAL: $config_errors configuration errors found. Please check your configuration."
        exit 1
    fi
}

# Basic configuration (will be overridden by config file)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default configuration values (overridden by config file)
LOG_FILE="/tmp/backup_validation_$(date +%Y%m%d).log"
EMAIL_RECIPIENT="backup-checker@worldarchitect.ai"
EMAIL_FROM="claude-backup@worldarchitect.ai"
EMAIL_SERVICE="gmail"
MEMORY_CACHE_DIR="$HOME/.cache/claude-learning"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
DROPBOX_BACKUP_DIR="${DROPBOX_DIR:-/mnt/c/Users/$(whoami)}/Dropbox/claude_backup"
GOOGLE_DRIVE_SYNC_DIR="${GOOGLE_DRIVE_DIR:-/mnt/c/Users/$(whoami)}/My Drive/.tmp.drivedownload"

# Email service configurations (defaults)
GMAIL_SMTP_SERVER="smtp.gmail.com"
GMAIL_SMTP_PORT="587"
MAILGUN_SMTP_SERVER="smtp.mailgun.org" 
MAILGUN_SMTP_PORT="587"
SENDGRID_SMTP_SERVER="smtp.sendgrid.net"
SENDGRID_SMTP_PORT="587"
AWS_SES_SMTP_SERVER="email-smtp.us-east-1.amazonaws.com"
AWS_SES_SMTP_PORT="587"

# Validation settings defaults
MEMORY_FILE_MAX_AGE_HOURS="168"
BACKUP_FILE_MAX_AGE_HOURS="2"
# Uses existing TEST_EMAIL credentials from ~/.bashrc:
# export EMAIL_USER="$TEST_EMAIL"
# export EMAIL_PASS="$TEST_PASSWORD"  # Needs to be Gmail App Password

# Validation results
declare -a VALIDATION_RESULTS=()
OVERALL_STATUS="PASS"

# Logging function
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
}

# Add validation result
add_result() {
    local status="$1"
    local component="$2"
    local details="$3"

    VALIDATION_RESULTS+=("$status|$component|$details")

    if [ "$status" != "PASS" ]; then
        OVERALL_STATUS="FAIL"
    fi

    log "$status: $component - $details"
}

# Validate memory backup
validate_memory_backup() {
    log "=== Validating Memory Backup ==="

    # Check if memory cache directory exists
    if [ ! -d "$MEMORY_CACHE_DIR" ]; then
        add_result "FAIL" "Memory Cache Directory" "Directory $MEMORY_CACHE_DIR does not exist"
        return
    fi

    add_result "PASS" "Memory Cache Directory" "Directory exists at $MEMORY_CACHE_DIR"

    # Check key memory files
    local memory_files=("learning_memory.json" "auto_corrections.json" "current_session.json")

    for file in "${memory_files[@]}"; do
        local file_path="$MEMORY_CACHE_DIR/$file"

        if [ ! -f "$file_path" ]; then
            add_result "WARN" "Memory File" "$file is missing"
            continue
        fi

        # Check file age (should be recent)
        local file_age=$(stat -c %Y "$file_path")
        local current_time=$(date +%s)
        local age_hours=$(( (current_time - file_age) / 3600 ))

        if [ $age_hours -gt $MEMORY_FILE_MAX_AGE_HOURS ]; then
            add_result "WARN" "Memory File Age" "$file is $age_hours hours old (max: ${MEMORY_FILE_MAX_AGE_HOURS}h)"
        else
            add_result "PASS" "Memory File" "$file exists and is recent (${age_hours}h old)"
        fi

        # Validate JSON structure
        if command -v python3 >/dev/null 2>&1; then
            if python3 -m json.tool "$file_path" >/dev/null 2>&1; then
                add_result "PASS" "Memory JSON" "$file has valid JSON structure"
            else
                add_result "FAIL" "Memory JSON" "$file has invalid JSON structure"
            fi
        fi

        # Check file size (should not be empty)
        local file_size=$(stat -c %s "$file_path")
        if [ $file_size -eq 0 ]; then
            add_result "FAIL" "Memory File Size" "$file is empty"
        else
            add_result "PASS" "Memory File Size" "$file is ${file_size} bytes"
        fi
    done

    # Check backup subdirectory
    local backup_dir="$MEMORY_CACHE_DIR/backups"
    if [ -d "$backup_dir" ]; then
        local backup_count=$(find "$backup_dir" -type f | wc -l)
        add_result "PASS" "Memory Backups" "$backup_count backup files found"
    else
        add_result "WARN" "Memory Backups" "Backup subdirectory not found"
    fi
}

# Validate claude directory backup
# Validate Google Drive sync health
validate_google_drive_sync() {
    log "=== Validating Google Drive Sync Health ==="

    # Check for Google Drive temporary sync directory (indicates active syncing)
    local google_drive_tmp="$GOOGLE_DRIVE_SYNC_DIR"
    
    if [ ! -d "$google_drive_tmp" ]; then
        add_result "WARN" "Google Drive Sync" "No .tmp.drivedownload directory found - sync may not be active"
        return
    fi

    # Check for recent sync activity (files created in last hour)
    local recent_sync_files=$(find "$google_drive_tmp" -mmin -60 -type f 2>/dev/null | wc -l)
    local total_sync_files=$(ls "$google_drive_tmp" 2>/dev/null | wc -l)
    
    if [ "$recent_sync_files" -gt 0 ]; then
        add_result "PASS" "Google Drive Sync" "Active sync detected - $recent_sync_files files in last hour (total: $total_sync_files)"
    elif [ "$total_sync_files" -gt 0 ]; then
        add_result "WARN" "Google Drive Sync" "Sync directory exists with $total_sync_files files but no recent activity"
    else
        add_result "WARN" "Google Drive Sync" "Sync directory exists but is empty"
    fi

    # Check if sync is processing large amounts of data (indicator of backup sync)
    local large_sync_files=$(find "$google_drive_tmp" -size +1M -type f 2>/dev/null | wc -l)
    if [ "$large_sync_files" -gt 0 ]; then
        add_result "PASS" "Google Drive Large Files" "$large_sync_files large files being synced (backup activity)"
    fi

    # Validate sync health by checking file age distribution
    if [ "$total_sync_files" -gt 100 ]; then
        add_result "PASS" "Google Drive Activity" "High sync activity detected ($total_sync_files temporary files)"
    elif [ "$total_sync_files" -gt 10 ]; then
        add_result "PASS" "Google Drive Activity" "Moderate sync activity detected ($total_sync_files temporary files)"
    elif [ "$total_sync_files" -gt 0 ]; then
        add_result "WARN" "Google Drive Activity" "Low sync activity detected ($total_sync_files temporary files)"
    fi
}

# Validate claude backup folder (single Dropbox location synced by both services)
validate_claude_backup_folders() {
    log "=== Validating Claude Backup Folder ==="

    local backup_dir="$DROPBOX_BACKUP_DIR"

    if [ ! -d "$backup_dir" ]; then
        add_result "FAIL" "Dropbox Claude Backup" "Directory $backup_dir does not exist"
        return
    fi

    # Check if directory has files
    local file_count=$(find "$backup_dir" -type f 2>/dev/null | wc -l)
    if [ "$file_count" -eq 0 ]; then
        add_result "FAIL" "Dropbox Claude Backup" "Directory is empty"
        return
    fi

    add_result "PASS" "Dropbox Claude Backup" "Directory exists with $file_count files"

    # Check backup freshness (should be updated hourly by cron)
    local newest_file=$(find "$backup_dir" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$newest_file" ]; then
        local file_age=$(stat -c %Y "$newest_file")
        local current_time=$(date +%s)
        local age_hours=$(( (current_time - file_age) / 3600 ))

        # Claude backup runs hourly, so files should be updated within configured hours
        if [ $age_hours -gt $BACKUP_FILE_MAX_AGE_HOURS ]; then
            add_result "WARN" "Dropbox Claude Freshness" "Newest file is $age_hours hours old (max: ${BACKUP_FILE_MAX_AGE_HOURS}h)"
        else
            add_result "PASS" "Dropbox Claude Freshness" "Files updated recently (${age_hours}h ago)"
        fi
    fi

    # Verify key claude files/directories are present (selective backup)
    local key_items=("settings.json" "projects" "local" "hooks")
    local missing_items=0
    local present_items=()

    for key_item in "${key_items[@]}"; do
        if [ ! -e "$backup_dir/$key_item" ]; then
            missing_items=$((missing_items + 1))
        else
            present_items+=("$key_item")
        fi
    done

    if [ $missing_items -gt 0 ]; then
        add_result "WARN" "Dropbox Claude Content" "$missing_items essential items missing from selective backup"
    else
        add_result "PASS" "Dropbox Claude Content" "All essential items present: ${present_items[*]}"
    fi

    # Verify selective backup (check unwanted files are excluded)
    local unwanted_files=("shell-snapshots" "todos" "conversations" ".anthropic" "statsig")
    local unwanted_found=0

    for unwanted in "${unwanted_files[@]}"; do
        if [ -e "$backup_dir/$unwanted" ]; then
            unwanted_found=$((unwanted_found + 1))
        fi
    done

    if [ $unwanted_found -gt 0 ]; then
        add_result "WARN" "Dropbox Selective Backup" "$unwanted_found unwanted files found (cleanup needed)"
    else
        add_result "PASS" "Dropbox Selective Backup" "Clean selective backup (no unwanted files)"
    fi

    # Always check Google Drive sync status for the Dropbox backup folder
    validate_google_drive_sync
}

# Validate memory backup with GitHub repo sync check
validate_memory_github_sync() {
    log "=== Validating Memory GitHub Sync ==="

    # Check if we're in a git repository
    if [ ! -d "$PROJECT_ROOT/.git" ]; then
        add_result "WARN" "Memory Git Sync" "Not in a git repository, skipping sync check"
        return
    fi

    (
        cd "$PROJECT_ROOT" || return

        # Check for dotfiles_backup directory (where memory files should be synced)
        if [ ! -d "dotfiles_backup" ]; then
            add_result "WARN" "Memory Git Sync" "dotfiles_backup directory not found"
            return
        fi

    # Check if there are any memory-related files in the backup
    local memory_files=$(find dotfiles_backup -name "*memory*" -o -name "*learning*" -o -name "*corrections*" 2>/dev/null | wc -l)
    if [ $memory_files -eq 0 ]; then
        add_result "WARN" "Memory Git Sync" "No memory files found in dotfiles_backup"
        return
    fi

    add_result "PASS" "Memory Git Sync" "Found $memory_files memory-related files in backup"

    # Check if backup files are recent (backup_dotfiles.sh should run regularly)
    local newest_backup=$(find dotfiles_backup -name "*memory*" -o -name "*learning*" -o -name "*corrections*" 2>/dev/null | xargs ls -t | head -1)
    if [ -n "$newest_backup" ]; then
        local file_age=$(stat -c %Y "$newest_backup")
        local current_time=$(date +%s)
        local age_days=$(( (current_time - file_age) / 86400 ))

        if [ $age_days -gt 7 ]; then
            add_result "WARN" "Memory Sync Freshness" "Newest memory backup is $age_days days old"
        else
            add_result "PASS" "Memory Sync Freshness" "Memory backup is recent (${age_days} days old)"
        fi
    fi

        # Check git status for uncommitted backup changes
        if git status --porcelain dotfiles_backup/ | grep -q "dotfiles_backup/"; then
            add_result "WARN" "Memory Git Status" "Uncommitted changes in dotfiles_backup directory"
        else
            add_result "PASS" "Memory Git Status" "No uncommitted changes in backup directory"
        fi
    )
}

validate_claude_backup() {
    log "=== Validating Claude Directory Backup ==="

    if [ ! -d "$CLAUDE_DIR" ]; then
        add_result "FAIL" "Claude Directory" "Directory $CLAUDE_DIR does not exist"
        return
    fi

    add_result "PASS" "Claude Directory" "Directory exists at $CLAUDE_DIR"

    # Check for backup files
    local backup_files=(
        "$CLAUDE_DIR/settings.json.backup"
        "$PROJECT_ROOT/CLAUDE.md.backup"
    )

    for backup_file in "${backup_files[@]}"; do
        if [ -f "$backup_file" ]; then
            local file_age=$(stat -c %Y "$backup_file")
            local current_time=$(date +%s)
            local age_days=$(( (current_time - file_age) / 86400 ))

            if [ $age_days -gt 7 ]; then
                add_result "WARN" "Claude Backup Age" "$(basename "$backup_file") is $age_days days old"
            else
                add_result "PASS" "Claude Backup" "$(basename "$backup_file") exists and is recent"
            fi
        else
            add_result "WARN" "Claude Backup" "$(basename "$backup_file") not found"
        fi
    done

    # Check if backup creation process is working
    if [ -f "$PROJECT_ROOT/backup_dotfiles.sh" ]; then
        add_result "PASS" "Backup Script" "backup_dotfiles.sh script exists"

        # Check if script is executable
        if [ -x "$PROJECT_ROOT/backup_dotfiles.sh" ]; then
            add_result "PASS" "Backup Script Permissions" "backup_dotfiles.sh is executable"
        else
            add_result "WARN" "Backup Script Permissions" "backup_dotfiles.sh is not executable"
        fi
    else
        add_result "FAIL" "Backup Script" "backup_dotfiles.sh script not found"
    fi
}

# Validate system prerequisites
validate_prerequisites() {
    log "=== Validating System Prerequisites ==="

    # Check required commands
    local required_commands=("git" "python3" "curl" "sendmail")

    for cmd in "${required_commands[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            add_result "PASS" "System Command" "$cmd is available"
        else
            add_result "WARN" "System Command" "$cmd is not available"
        fi
    done

    # Check git repository status
    if [ -d "$PROJECT_ROOT/.git" ]; then
        add_result "PASS" "Git Repository" "Project is a git repository"

        # Check if there are uncommitted backup changes
        cd "$PROJECT_ROOT"
        if git status --porcelain | grep -E "(backup|\.backup)" >/dev/null 2>&1; then
            add_result "WARN" "Git Status" "Uncommitted backup files detected"
        else
            add_result "PASS" "Git Status" "No uncommitted backup files"
        fi
    else
        add_result "FAIL" "Git Repository" "Project is not a git repository"
    fi
}

# Test backup restoration capability
test_backup_restoration() {
    log "=== Testing Backup Restoration Capability ==="

    # Create temporary test directory
    local test_dir="/tmp/backup_test_$$"
    mkdir -p "$test_dir"

    # Test memory backup restoration
    if [ -f "$MEMORY_CACHE_DIR/learning_memory.json" ]; then
        if cp "$MEMORY_CACHE_DIR/learning_memory.json" "$test_dir/test_memory.json" 2>/dev/null; then
            add_result "PASS" "Memory Restore Test" "Memory file can be copied/restored"
        else
            add_result "FAIL" "Memory Restore Test" "Memory file cannot be copied"
        fi
    fi

    # Test claude backup restoration
    if [ -f "$CLAUDE_DIR/settings.json.backup" ]; then
        if cp "$CLAUDE_DIR/settings.json.backup" "$test_dir/test_settings.json" 2>/dev/null; then
            add_result "PASS" "Claude Restore Test" "Claude backup file can be copied/restored"
        else
            add_result "FAIL" "Claude Restore Test" "Claude backup file cannot be copied"
        fi
    fi

    # Cleanup test directory
    rm -rf "$test_dir"
}

# Generate email report
generate_email_report() {
    local report_file="/tmp/backup_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Subject: Daily Backup Validation Report - $(date '+%Y-%m-%d')
From: backup-checker@worldarchitect.ai
To: $EMAIL_RECIPIENT

========================================
WORLDARCHITECT.AI BACKUP VALIDATION REPORT
$(date '+%Y-%m-%d %H:%M:%S')
========================================

OVERALL STATUS: $OVERALL_STATUS

DETAILED RESULTS:
================
EOF

    for result in "${VALIDATION_RESULTS[@]}"; do
        IFS='|' read -r status component details <<< "$result"
        printf "%-6s | %-25s | %s\n" "$status" "$component" "$details" >> "$report_file"
    done

    cat >> "$report_file" << EOF

SUMMARY:
========
Total Checks: ${#VALIDATION_RESULTS[@]}
Passed: $(passed=0; for entry in "${VALIDATION_RESULTS[@]}"; do [[ "${entry%%|*}" == "PASS" ]] && ((passed++)); done; echo $passed)
Warnings: $(warned=0; for entry in "${VALIDATION_RESULTS[@]}"; do [[ "${entry%%|*}" == "WARN" ]] && ((warned++)); done; echo $warned)
Failed: $(failed=0; for entry in "${VALIDATION_RESULTS[@]}"; do [[ "${entry%%|*}" == "FAIL" ]] && ((failed++)); done; echo $failed)

LOG LOCATION: $LOG_FILE

========================================
Generated by WorldArchitect.AI Backup Validation System
========================================
EOF

    echo "$report_file"
}

# Send email via specific service
send_email_via_service() {
    local service="$1"
    local report_file="$2"
    
    case "$service" in
        gmail)
            send_email_gmail "$report_file"
            ;;
        mailgun)
            send_email_mailgun "$report_file"
            ;;
        sendgrid)
            send_email_sendgrid "$report_file"
            ;;
        ses)
            send_email_ses "$report_file"
            ;;
        sendmail)
            send_email_sendmail "$report_file"
            ;;
        *)
            log "ERROR: Unknown email service: $service"
            return 1
            ;;
    esac
}

# Gmail SMTP delivery
send_email_gmail() {
    local report_file="$1"
    
    if [ -z "${EMAIL_USER:-}" ] || [ -z "${EMAIL_PASS:-}" ]; then
        log "Gmail credentials not configured (EMAIL_USER, EMAIL_PASS)"
        return 1
    fi
    
    if command -v curl >/dev/null 2>&1; then
        if curl --url "smtp://$GMAIL_SMTP_SERVER:$GMAIL_SMTP_PORT" \
               --ssl-reqd \
               --mail-from "$EMAIL_USER" \
               --mail-rcpt "$EMAIL_RECIPIENT" \
               --user "$EMAIL_USER:$EMAIL_PASS" \
               --upload-file "$report_file" >/dev/null 2>&1; then
            log "Email sent successfully via Gmail SMTP"
            return 0
        fi
    fi
    
    return 1
}

# Mailgun SMTP delivery
send_email_mailgun() {
    local report_file="$1"
    
    if [ -z "${MAILGUN_USERNAME:-}" ] || [ -z "${MAILGUN_PASSWORD:-}" ]; then
        log "Mailgun credentials not configured (MAILGUN_USERNAME, MAILGUN_PASSWORD)"
        return 1
    fi
    
    if command -v curl >/dev/null 2>&1; then
        if curl --url "smtp://$MAILGUN_SMTP_SERVER:$MAILGUN_SMTP_PORT" \
               --ssl-reqd \
               --mail-from "${EMAIL_FROM}" \
               --mail-rcpt "$EMAIL_RECIPIENT" \
               --user "$MAILGUN_USERNAME:$MAILGUN_PASSWORD" \
               --upload-file "$report_file" >/dev/null 2>&1; then
            log "Email sent successfully via Mailgun SMTP"
            return 0
        fi
    fi
    
    return 1
}

# SendGrid SMTP delivery
send_email_sendgrid() {
    local report_file="$1"
    
    if [ -z "${SENDGRID_API_KEY:-}" ]; then
        log "SendGrid API key not configured (SENDGRID_API_KEY)"
        return 1
    fi
    
    if command -v curl >/dev/null 2>&1; then
        if curl --url "smtp://$SENDGRID_SMTP_SERVER:$SENDGRID_SMTP_PORT" \
               --ssl-reqd \
               --mail-from "${EMAIL_FROM}" \
               --mail-rcpt "$EMAIL_RECIPIENT" \
               --user "apikey:$SENDGRID_API_KEY" \
               --upload-file "$report_file" >/dev/null 2>&1; then
            log "Email sent successfully via SendGrid SMTP"
            return 0
        fi
    fi
    
    return 1
}

# AWS SES SMTP delivery
send_email_ses() {
    local report_file="$1"
    
    if [ -z "${AWS_SES_USERNAME:-}" ] || [ -z "${AWS_SES_PASSWORD:-}" ]; then
        log "AWS SES credentials not configured (AWS_SES_USERNAME, AWS_SES_PASSWORD)"
        return 1
    fi
    
    if command -v curl >/dev/null 2>&1; then
        if curl --url "smtp://$AWS_SES_SMTP_SERVER:$AWS_SES_SMTP_PORT" \
               --ssl-reqd \
               --mail-from "${EMAIL_FROM}" \
               --mail-rcpt "$EMAIL_RECIPIENT" \
               --user "$AWS_SES_USERNAME:$AWS_SES_PASSWORD" \
               --upload-file "$report_file" >/dev/null 2>&1; then
            log "Email sent successfully via AWS SES SMTP"
            return 0
        fi
    fi
    
    return 1
}

# System sendmail delivery
send_email_sendmail() {
    local report_file="$1"
    
    if command -v sendmail >/dev/null 2>&1; then
        if sendmail "$EMAIL_RECIPIENT" < "$report_file" 2>/dev/null; then
            log "Email sent successfully via sendmail"
            return 0
        fi
    fi
    
    return 1
}

# Main email notification function with fallback support
send_email_notification() {
    local report_file="$1"

    log "=== Sending Email Notification ==="
    log "Using email service: $EMAIL_SERVICE"

    local email_sent=false
    
    # Try primary email service
    if send_email_via_service "$EMAIL_SERVICE" "$report_file"; then
        email_sent=true
        add_result "PASS" "Email Delivery" "Email sent successfully via $EMAIL_SERVICE"
    else
        log "Primary email service ($EMAIL_SERVICE) failed, trying fallbacks..."
        
        # Try fallback services in order
        local fallback_services=("sendmail")
        
        # Add other services as fallbacks (excluding the one that already failed)
        case "$EMAIL_SERVICE" in
            gmail) fallback_services+=("mailgun" "sendgrid" "ses") ;;
            mailgun) fallback_services+=("gmail" "sendgrid" "ses") ;;
            sendgrid) fallback_services+=("gmail" "mailgun" "ses") ;;
            ses) fallback_services+=("gmail" "mailgun" "sendgrid") ;;
            sendmail) fallback_services=("gmail" "mailgun" "sendgrid" "ses") ;;
        esac
        
        for fallback_service in "${fallback_services[@]}"; do
            if send_email_via_service "$fallback_service" "$report_file"; then
                email_sent=true
                add_result "PASS" "Email Delivery" "Email sent via fallback service: $fallback_service"
                break
            fi
        done
    fi

    # Final fallback: Save to file for manual review
    if [ "$email_sent" = false ]; then
        local manual_dir="$PROJECT_ROOT/tmp/backup_reports"
        mkdir -p "$manual_dir"
        cp "$report_file" "$manual_dir/backup_report_$(date +%Y%m%d_%H%M%S).txt"
        add_result "WARN" "Email Delivery" "All email services failed - report saved to $manual_dir for manual review"
    fi
}

# Main execution
main() {
    log "Starting backup validation at $(date)"
    
    # Load configuration from file
    load_config

    # Create tmp directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/tmp"

    # Run all validation checks
    validate_prerequisites
    validate_memory_backup
    validate_memory_github_sync
    validate_claude_backup_folders
    validate_claude_backup
    test_backup_restoration

    # Generate and send report
    local report_file=$(generate_email_report)
    send_email_notification "$report_file"

    # Final status
    log "Backup validation completed with status: $OVERALL_STATUS"

    # Return appropriate exit code
    if [ "$OVERALL_STATUS" = "PASS" ]; then
        exit 0
    else
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
Backup Validation Script with Configuration Support

USAGE:
    $0                    # Run validation
    $0 --setup-cron      # Setup 4-hourly cron job
    $0 --remove-cron     # Remove cron job
    $0 --help            # Show this help

CONFIGURATION:
    The script uses configuration files for all settings:
    
    1. Default config: scripts/backup_validation.conf
    2. User overrides: ~/.backup_validation.conf (optional)
    
    Key configuration sections:
    - Backup paths (Dropbox, Google Drive, memory cache)
    - Email service settings (Gmail, Mailgun, SendGrid, SES, sendmail)
    - Validation thresholds (file age limits)
    - Logging preferences

EMAIL SERVICES SUPPORTED:
    • Gmail SMTP (requires EMAIL_USER, EMAIL_PASS environment variables)
      - Note: Gmail App Passwords being deprecated in 2025
      - Get App Password: https://myaccount.google.com/apppasswords
      
    • Mailgun SMTP (recommended alternative)
      - Set: MAILGUN_USERNAME, MAILGUN_PASSWORD environment variables
      - Signup: https://mailgun.com (5,000 emails/month free)
      
    • SendGrid SMTP  
      - Set: SENDGRID_API_KEY environment variable
      - Signup: https://sendgrid.com (100 emails/day free)
      
    • AWS SES SMTP
      - Set: AWS_SES_USERNAME, AWS_SES_PASSWORD environment variables
      - Setup in AWS SES console
      
    • System sendmail (local mail server)
      - No credentials needed, uses local mail system

EMAIL CONFIGURATION:
    Set EMAIL_SERVICE in config file or via environment:
    export EMAIL_SERVICE="mailgun"  # gmail, mailgun, sendgrid, ses, sendmail
    
    The system automatically falls back to other services if primary fails.

VALIDATION CHECKS:
    ✅ Memory backups with configurable age thresholds
    ✅ Memory GitHub sync validation (dotfiles_backup/)
    ✅ Claude backup folder with freshness monitoring
    ✅ Google Drive sync health (.tmp.drivedownload activity)
    ✅ Claude directory backups (.claude/*.backup)
    ✅ System prerequisites and restore capability
    ✅ Configurable cron schedule compliance
    ✅ Multi-service email notifications with fallbacks

CONFIGURATION EXAMPLE:
    # Set email service
    echo 'EMAIL_SERVICE="mailgun"' >> ~/.backup_validation.conf
    
    # Set custom backup location
    echo 'DROPBOX_BACKUP_DIR="/custom/path/to/backup"' >> ~/.backup_validation.conf

LOGS:
    Validation: /tmp/backup_validation_YYYYMMDD.log
    Cron: /tmp/backup_validation_cron.log
    Reports: /tmp/backup_report_*.txt
    Config: scripts/backup_validation.conf

From: backup-checker@worldarchitect.ai
EOF
}

# Setup cron job
setup_cron() {
    echo "Setting up daily backup validation cron job..."

    # Create wrapper script for cron environment
    local wrapper_script="$SCRIPT_DIR/backup_validation_cron.sh"
    cat > "$wrapper_script" << EOF
#!/bin/bash
# Cron wrapper for backup validation
export PATH="/usr/local/bin:/usr/bin:/bin:\$PATH"
export SHELL="/bin/bash"
cd "$PROJECT_ROOT"
exec "$SCRIPT_DIR/backup_validation.sh"
EOF
    chmod +x "$wrapper_script"

    # Remove existing cron job if it exists
    (crontab -l 2>/dev/null | grep -v "backup_validation") | crontab - 2>/dev/null || true

    # Add new cron job for every 4 hours
    local cron_entry="0 */4 * * * $wrapper_script > /tmp/backup_validation_cron.log 2>&1"
    (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -

    echo "✅ Cron job setup complete!"
    echo "   Schedule: Every 4 hours (0 */4 * * *)"
    echo "   Script: $wrapper_script"
    echo "   Log: /tmp/backup_validation_cron.log"
    echo ""
    echo "To configure email notifications:"
    echo "   1. Edit scripts/backup_validation.conf or create ~/.backup_validation.conf"
    echo "   2. Set EMAIL_SERVICE (gmail, mailgun, sendgrid, ses, sendmail)"
    echo "   3. Set appropriate credentials via environment variables"
    echo ""
    echo "Example for Mailgun:"
    echo "   export EMAIL_SERVICE=\"mailgun\""
    echo "   export MAILGUN_USERNAME=\"your-mailgun-username\""
    echo "   export MAILGUN_PASSWORD=\"your-mailgun-password\""
}

# Remove cron job
remove_cron() {
    echo "Removing backup validation cron job..."
    (crontab -l 2>/dev/null | grep -v "backup_validation") | crontab - 2>/dev/null || true

    # Remove wrapper script
    local wrapper_script="$SCRIPT_DIR/backup_validation_cron.sh"
    rm -f "$wrapper_script"

    echo "✅ Cron job removed"
}

# Parse command line arguments
case "${1:-}" in
    --setup-cron)
        setup_cron
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
    "")
        # Run validation (default)
        main
        ;;
    *)
        echo "Error: Unknown option '$1'"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
