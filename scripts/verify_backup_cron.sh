#!/bin/bash

# Backup System Verification Script
# Checks if the Claude backup system is properly configured and operational

set -euo pipefail

# Function to verify backup system health
verify_backup_system() {
    local status=0
    
    echo "=== Claude Backup System Verification ==="
    
    # Check if cron job exists
    if crontab -l 2>/dev/null | grep -q "claude_backup"; then
        echo "✅ Cron job configured"
    else
        echo "❌ Cron job missing"
        status=1
    fi
    
    # Check if backup script exists
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -x "$SCRIPT_DIR/claude_backup.sh" ]; then
        echo "✅ Backup script executable"
    else
        echo "❌ Backup script missing"
        status=1
    fi
    
    # Check if destination is accessible
    if [ -d "$HOME/Library/CloudStorage/Dropbox" ]; then
        echo "✅ Backup destination accessible"
    else
        echo "❌ Backup destination missing"
        status=1
    fi
    
    if [ $status -eq 0 ]; then
        echo "✅ Backup system is healthy"
    else
        echo "❌ Backup system needs attention"
    fi
    
    return $status
}

# Run verification if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    verify_backup_system
fi
