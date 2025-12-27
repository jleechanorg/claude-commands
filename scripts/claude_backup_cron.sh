#!/bin/bash
# Portable Cron Wrapper for Claude Backup
# This script is installed in a stable location and references the main backup script
set -euo pipefail

# Security: Create secure temp directory for logs with proper cleanup
SECURE_TEMP=$(mktemp -d)
chmod 700 "$SECURE_TEMP"
trap 'echo "[cron] $(date +%F\ %T) error at line $LINENO" >> "$SECURE_TEMP/claude_backup_cron.log"; rm -rf "$SECURE_TEMP"' ERR
trap 'rm -rf "$SECURE_TEMP"' EXIT

export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export SHELL="/bin/bash"

# Security: Path validation function
validate_path() {
    local path="$1"
    local context="$2"

    # Check for path traversal patterns
    if [[ "$path" =~ \.\./|/\.\. ]]; then
        echo "ERROR: Path traversal attempt detected in $context: $path" >&2
        exit 1
    fi

    # Check for null bytes
    if [[ "$path" =~ $'\x00' ]]; then
        echo "ERROR: Null byte detected in $context: $path" >&2
        exit 1
    fi
}

# Preserve email credentials from environment (with validation)
[ -n "${EMAIL_USER:-}" ] && export EMAIL_USER="$EMAIL_USER"
[ -n "${EMAIL_PASS:-}" ] && export EMAIL_PASS="$EMAIL_PASS"
[ -n "${BACKUP_EMAIL:-}" ] && export BACKUP_EMAIL="$BACKUP_EMAIL"

# Use the installed backup script with provided or default Dropbox location
DROPBOX_BASE="${1:-$HOME/Library/CloudStorage/Dropbox}"

# Security: Validate the Dropbox base directory path
validate_path "$DROPBOX_BASE" "DROPBOX_BASE parameter"

# Validate Dropbox base directory exists
if [[ ! -d "$DROPBOX_BASE" ]]; then
  echo "Dropbox base directory not found: $DROPBOX_BASE" >&2
  echo "Falling back to default: $HOME/Library/CloudStorage/Dropbox" >&2
  DROPBOX_BASE="$HOME/Library/CloudStorage/Dropbox"
  validate_path "$DROPBOX_BASE" "fallback Dropbox directory"
fi

# Security: Validate backup script exists and is executable
if [[ ! -x "$HOME/.local/bin/claude_backup.sh" ]]; then
    echo "ERROR: Backup script not found or not executable: $HOME/.local/bin/claude_backup.sh" >&2
    exit 1
fi

# Run the installed backup script with secure logging
# Note: Don't use exec here - it prevents EXIT trap from firing and cleaning up temp dir
"$HOME/.local/bin/claude_backup.sh" "$DROPBOX_BASE" >> "$SECURE_TEMP/claude_backup_cron.log" 2>&1
