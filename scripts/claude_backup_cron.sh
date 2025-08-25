#!/bin/bash
# Cron wrapper for claude backup enhanced
set -euo pipefail
# Minimal cron-safe trap
trap '{
  ts="$(date "+%Y-%m-%d %H:%M:%S")"
  echo "[$ts] [cron][err] Failure at line $LINENO" >> "${CRON_LOG:-/tmp/claude_backup_cron.log}"
}' ERR
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export SHELL="/bin/bash"

# Load environment variables from ~/.bashrc for cron compatibility
if [ -f "$HOME/.bashrc" ]; then
    # Source bashrc in non-interactive mode to get environment variables
    set +e +u +o pipefail
    source "$HOME/.bashrc" 2>/dev/null || true
    set -euo pipefail
fi

# Preserve email credentials from environment if available
# These should be set in ~/.bashrc:
# export EMAIL_USER="your-email@gmail.com"
# export EMAIL_PASS="your-gmail-app-password"  
# export BACKUP_EMAIL="your-email@gmail.com"
[ -n "${EMAIL_USER:-}" ] && export EMAIL_USER="$EMAIL_USER"
[ -n "${EMAIL_PASS:-}" ] && export EMAIL_PASS="$EMAIL_PASS"
[ -n "${BACKUP_EMAIL:-}" ] && export BACKUP_EMAIL="$BACKUP_EMAIL"

# Resolve project root dynamically for portability
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set up secure logging directory for cron operations
LOG_DIR="$PROJECT_ROOT/tmp"
mkdir -p "$LOG_DIR" && chmod 700 "$LOG_DIR"
CRON_LOG="$LOG_DIR/claude_backup_cron.log"

# Use environment variable for Dropbox path, with sane default
DEFAULT_DROPBOX_BASE="$HOME/Library/CloudStorage/Dropbox"
DROPBOX_BASE="${1:-"$DEFAULT_DROPBOX_BASE"}"

# Validate Dropbox base directory exists
if [[ ! -d "$DROPBOX_BASE" ]]; then
  echo "[cron][warn] Dropbox base missing: $DROPBOX_BASE; falling back to $DEFAULT_DROPBOX_BASE" >&2
  DROPBOX_BASE="$DEFAULT_DROPBOX_BASE"
fi

# Log cron execution start
{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting claude backup cron wrapper"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dropbox base: $DROPBOX_BASE"
    
    # Use ~/.local/bin/ installation if available, otherwise use worktree version
    if [ -x "$HOME/.local/bin/claude_backup.sh" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Using installed version: $HOME/.local/bin/claude_backup.sh"
        exec "$HOME/.local/bin/claude_backup.sh" "$DROPBOX_BASE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Using worktree version: $PROJECT_ROOT/scripts/claude_backup.sh"
        exec "$PROJECT_ROOT/scripts/claude_backup.sh" "$DROPBOX_BASE"
    fi
} >> "$CRON_LOG" 2>&1
