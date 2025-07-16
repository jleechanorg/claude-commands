#!/usr/bin/env bash
# Backup Script Version Check Utility
# Used by /learn command to verify backup script is up to date

check_backup_script_version() {
    local repo_dir="${1:-$(pwd)}"
    local repo_script="$repo_dir/memory/backup_memory.sh"
    local deployed_script="$HOME/backup_memory.sh"
    
    if [ ! -f "$repo_script" ]; then
        echo "❌ ERROR: Repo backup script not found at $repo_script"
        return 1
    fi
    
    if [ ! -f "$deployed_script" ]; then
        echo "❌ ERROR: Deployed backup script not found at $deployed_script"
        echo "💡 To fix: cp $repo_script $deployed_script && chmod +x $deployed_script"
        return 1
    fi
    
    local repo_version=$(grep "# VERSION:" "$repo_script" | cut -d' ' -f3)
    local deployed_version=$(grep "# VERSION:" "$deployed_script" | cut -d' ' -f3)
    
    if [ -z "$repo_version" ] || [ -z "$deployed_version" ]; then
        echo "❌ ERROR: Cannot determine script versions"
        return 1
    fi
    
    if [ "$repo_version" != "$deployed_version" ]; then
        echo "❌ WARNING: Backup script version mismatch!"
        echo "   Repo version: $repo_version"
        echo "   Deployed version: $deployed_version"
        echo "💡 To fix: cp $repo_script $deployed_script"
        return 1
    else
        echo "✅ Backup script versions match: $repo_version"
        return 0
    fi
}

# If called directly, run the check
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    check_backup_script_version "$@"
fi