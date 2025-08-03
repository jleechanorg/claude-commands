#!/bin/bash
# common_utils.sh - Common Utilities for WorldArchitect.AI Development Tools
#
# Purpose: Shared functions that can be sourced by various development tools
#          to ensure consistent behavior and reduce code duplication.
#
# Usage: source ~/projects/worldarchitect.ai/scripts/common_utils.sh

# Find WorldArchitect project root from any directory
find_project_root() {
    local current_dir="$PWD"
    local project_root=""

    # Look for CLAUDE.md as indicator of project root
    while [[ "$current_dir" != "/" ]]; do
        if [[ -f "$current_dir/CLAUDE.md" ]]; then
            project_root="$current_dir"
            break
        fi
        current_dir=$(dirname "$current_dir")
    done

    # Fallback: check WORLDARCH_ROOT environment variable or fail early
    if [[ -z "$project_root" ]]; then
        if [[ -n "$WORLDARCH_ROOT" ]]; then
            project_root="$WORLDARCH_ROOT"
            if [[ ! -d "$project_root" ]]; then
                echo "❌ WORLDARCH_ROOT directory does not exist: $project_root" >&2
                return 1
            fi
        else
            echo "❌ WorldArchitect project root not found (set WORLDARCH_ROOT if non-standard)" >&2
            return 1
        fi
    fi

    echo "$project_root"
    return 0
}

# Smart sync check wrapper that can be called from any tool
smart_sync_check() {
    local project_root
    if ! project_root=$(find_project_root); then
        echo "⚠️  Cannot locate project root - skipping sync check" >&2
        return 0
    fi

    local sync_script="$project_root/scripts/sync_check.sh"
    if [[ ! -x "$sync_script" ]]; then
        echo "⚠️  Sync check script not found or not executable - skipping" >&2
        return 0
    fi

    echo ""
    echo "🔄 Post-Command Sync Check"
    echo "=========================="
    "$sync_script"
    echo ""
}

# Quick commit and sync function for tools that create changes
quick_commit_and_sync() {
    local commit_message="$1"

    if [[ -z "$commit_message" ]]; then
        echo "❌ Commit message required" >&2
        return 1
    fi

    # Check if there are changes to commit
    if git diff --quiet && git diff --cached --quiet; then
        echo "✅ No changes to commit"
        smart_sync_check
        return $?
    fi

    # Stage and commit changes
    git add -A
    git commit -m "$commit_message"

    # Run sync check to push if needed
    smart_sync_check
}

# Check if we're in a WorldArchitect project
is_worldarchitect_project() {
    local project_root
    project_root=$(find_project_root 2>/dev/null) || return 1

    # Additional checks for WorldArchitect-specific files
    [[ -f "$project_root/CLAUDE.md" ]] && \
    [[ -d "$project_root/mvp_site" ]] && \
    [[ -f "$project_root/integrate.sh" ]]
}

# Export functions so they can be used by tools that source this file
export -f find_project_root
export -f smart_sync_check
export -f quick_commit_and_sync
export -f is_worldarchitect_project
