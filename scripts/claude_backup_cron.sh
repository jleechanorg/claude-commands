#!/bin/bash
# Cron wrapper for claude backup enhanced
# Usage: claude_backup_cron.sh [DROPBOX_BASE_DIR]
# Default DROPBOX_BASE_DIR: $HOME/Library/CloudStorage/Dropbox
# Logs: /tmp/claude_backup_cron.log
set -euo pipefail
trap 'echo "[cron] $(date +%F\ %T) error at line $LINENO" >> /tmp/claude_backup_cron.log' ERR
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export SHELL="/bin/bash"

# Preserve email credentials from environment if available
# These must be set in the user's environment before setting up cron:
# export EMAIL_USER="your-email@gmail.com"
# export EMAIL_PASS="your-gmail-app-password"  
# export BACKUP_EMAIL="your-email@gmail.com"
[ -n "${EMAIL_USER:-}" ] && export EMAIL_USER="$EMAIL_USER"
[ -n "${EMAIL_PASS:-}" ] && export EMAIL_PASS="$EMAIL_PASS"
[ -n "${BACKUP_EMAIL:-}" ] && export BACKUP_EMAIL="$BACKUP_EMAIL"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DROPBOX_BASE="${1:-"$HOME/Library/CloudStorage/Dropbox"}"

# Validate Dropbox base directory
if [[ ! -d "$DROPBOX_BASE" ]]; then
  echo "Dropbox base directory not found: $DROPBOX_BASE" >&2
  echo "Falling back to default: \$HOME/Library/CloudStorage/Dropbox" >&2
  DROPBOX_BASE="$HOME/Library/CloudStorage/Dropbox"
fi

# Run the backup script from project root and log output
exec "$PROJECT_ROOT/scripts/claude_backup.sh" "$DROPBOX_BASE" >> /tmp/claude_backup_cron.log 2>&1
