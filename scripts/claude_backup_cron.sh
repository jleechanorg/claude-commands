#!/bin/bash
# Cron wrapper for claude backup enhanced
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

cd "/Users/jleechan/projects/worldarchitect.ai/worktree_backip"
exec "/Users/jleechan/projects/worldarchitect.ai/worktree_backip/scripts/claude_backup.sh" "/Users/jleechan/Library/CloudStorage/Dropbox"
