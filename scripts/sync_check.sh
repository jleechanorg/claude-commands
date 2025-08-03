#!/bin/bash
# sync_check.sh - Smart Post-Command Sync Check
#
# Purpose: Automatically detect and push unpushed git commits to prevent
#          local changes from getting stuck without being synchronized to remote.
#
# Usage:
#   ~/projects/worldarchitect.ai/scripts/sync_check.sh
#   source ~/projects/worldarchitect.ai/scripts/sync_check.sh && sync_check
#
# Features:
#   - Works from any directory (finds git root automatically)
#   - Robust error handling for edge cases
#   - Clear, actionable feedback with visual indicators
#   - Safe: only pushes when unpushed commits are detected
#   - Idempotent: safe to run multiple times

set -euo pipefail

# ANSI color codes for better visibility
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging function with timestamp and color
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')

    case "$level" in
        "INFO")    printf '%b\n' "${BLUE}[${timestamp}] ℹ️  ${message}${NC}" ;;
        "WARN")    printf '%b\n' "${YELLOW}[${timestamp}] ⚠️  ${message}${NC}" ;;
        "ERROR")   printf '%b\n' "${RED}[${timestamp}] ❌ ${message}${NC}" ;;
        "SUCCESS") printf '%b\n' "${GREEN}[${timestamp}] ✅ ${message}${NC}" ;;
    esac
}

# Main sync check function
sync_check() {
    log "INFO" "🔍 Smart Sync Check - Detecting unpushed commits..."

    # 1. Find git repository root
    local git_root
    if ! git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
        log "WARN" "Not in a git repository - skipping sync check"
        return 0
    fi

    log "INFO" "📁 Git repository: $(basename "$git_root")"

    # 2. Get current branch
    local current_branch
    if ! current_branch=$(git branch --show-current 2>/dev/null); then
        log "WARN" "Detached HEAD state detected - skipping sync check"
        return 0
    fi

    if [[ -z "$current_branch" ]]; then
        log "WARN" "Unable to determine current branch - skipping sync check"
        return 0
    fi

    log "INFO" "🌿 Current branch: $current_branch"

    # 3. Check for upstream tracking branch
    local upstream_branch
    if ! upstream_branch=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null); then
        log "WARN" "No upstream tracking branch found for '$current_branch'"
        log "INFO" "💡 Set upstream with: git push -u origin $current_branch"
        return 0
    fi

    log "INFO" "⬆️  Upstream: $upstream_branch"

    # 4. Check for unpushed commits
    local unpushed_commits
    if ! unpushed_commits=$(git log @{upstream}..HEAD --oneline 2>/dev/null); then
        log "ERROR" "Failed to compare with upstream branch"
        return 1
    fi

    # 5. Handle results
    if [[ -z "$unpushed_commits" ]]; then
        log "SUCCESS" "Repository is in sync - no unpushed commits detected"
        return 0
    fi

    # Unpushed commits found - show them and push
    local commit_count
    commit_count=$(echo "$unpushed_commits" | wc -l)

    log "WARN" "🔄 Found $commit_count unpushed commit(s):"
    echo "$unpushed_commits" | while IFS= read -r commit; do
        echo "   📝 $commit"
    done

    log "INFO" "🚀 Auto-pushing to $upstream_branch..."

    # 6. Attempt to push
    if git push origin HEAD 2>/dev/null; then
        log "SUCCESS" "Push completed successfully! 🎉"
        log "INFO" "🔗 Remote repository is now synchronized"
    else
        log "ERROR" "Push failed - manual intervention may be required"
        log "INFO" "💡 Try: git push origin HEAD --force-with-lease (if safe)"
        return 1
    fi

    return 0
}

# Execute sync_check if script is run directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    sync_check "$@"
fi
