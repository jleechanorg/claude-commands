#!/bin/bash
# Cron wrapper for claude backup enhanced
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export SHELL="/bin/bash"

# Load environment variables from ~/.bashrc for cron compatibility
if [ -f "$HOME/.bashrc" ]; then
    # Source bashrc in non-interactive mode to get environment variables
    set +e  # Temporarily disable exit on error for sourcing
    source "$HOME/.bashrc" 2>/dev/null
    set -e  # Re-enable exit on error
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

# Use environment variable for Dropbox path, with sane default
DEFAULT_DROPBOX_BASE="$HOME/Library/CloudStorage/Dropbox"
DROPBOX_BASE="${1:-"$DEFAULT_DROPBOX_BASE"}"

# Validate Dropbox base directory exists
if [[ ! -d "$DROPBOX_BASE" ]]; then
  echo "[cron][warn] Dropbox base missing: $DROPBOX_BASE; falling back to $DEFAULT_DROPBOX_BASE" >&2
  DROPBOX_BASE="$DEFAULT_DROPBOX_BASE"
fi

# Use ~/.local/bin/ installation if available, otherwise use worktree version
if [ -x "$HOME/.local/bin/claude_backup.sh" ]; then
    # Use installed version in stable location
    exec "$HOME/.local/bin/claude_backup.sh" "$DROPBOX_BASE"
else
    # Fallback to worktree version if installed version not available  
    exec "$PROJECT_ROOT/scripts/claude_backup.sh" "$DROPBOX_BASE"
fi
