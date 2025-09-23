#!/bin/bash
# automation.sh - Shared automation context detection library
#
# Purpose: Centralized logic for detecting automation context across hooks
#
# Usage: source "$(dirname "$0")/lib/automation.sh"
#        is_automation_context && echo "automation detected"

# Function to check if this is an automation context
is_automation_context() {
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

    # Standardized automation pattern matching
    local automation_pattern='(^|[/_-])(automation|auto(mation)?|bot|copilot|claude)($|[/_-])'

    # Check branch names for automation patterns (word boundary matching to avoid false positives)
    if [[ "$current_branch" =~ $automation_pattern ]]; then
        return 0
    fi

    # Check if we're in a PR context with automation labels (guard both gh and jq)
    if command -v gh >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        local pr_info
        pr_info=$(gh pr view --json title,labels 2>/dev/null || echo "{}")
        if echo "$pr_info" | jq -r '.labels[]?.name // empty' 2>/dev/null | grep -Eqi "$automation_pattern"; then
            return 0
        fi
        if echo "$pr_info" | jq -r '.title // empty' 2>/dev/null | grep -Eqi "$automation_pattern"; then
            return 0
        fi
    fi

    # Check recent commits for automation patterns (guard for initial commits)
    if git rev-parse --verify HEAD >/dev/null 2>&1 && git log --oneline -5 2>/dev/null | grep -Eqi '\[AI automation\]'; then
        return 0
    fi

    return 1
}
