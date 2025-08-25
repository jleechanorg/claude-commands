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

# Use ~/.local/bin/ installation instead of worktree-dependent paths
if [ -x "$HOME/.local/bin/claude_backup.sh" ]; then
    # Use installed version in stable location
    exec "$HOME/.local/bin/claude_backup.sh" "/Users/jleechan/Library/CloudStorage/Dropbox"
else
    # Fallback to worktree version if installed version not available
    cd "/Users/jleechan/projects/worldarchitect.ai/worktree_backip"
    exec "/Users/jleechan/projects/worldarchitect.ai/worktree_backip/scripts/claude_backup.sh" "/Users/jleechan/Library/CloudStorage/Dropbox"
fi
