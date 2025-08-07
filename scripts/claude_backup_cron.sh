#!/bin/bash
# Cron wrapper for claude backup
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export SHELL="/bin/bash"
# Load existing email credentials from .bashrc
source "$HOME/.bashrc"
export EMAIL_USER="$TEST_EMAIL"
export EMAIL_PASS="$TEST_PASSWORD"
export BACKUP_EMAIL="$TEST_EMAIL"
# Determine project root based on script location
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"
exec "$SCRIPT_DIR/claude_backup.sh"
