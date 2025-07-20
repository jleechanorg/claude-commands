#!/bin/bash

# integrate.sh - Updates from main and creates fresh dev branch
# This script implements the standard integration pattern for the project
# 
# Usage: ./integrate.sh [branch-name] [--force] [--new-branch]
#   branch-name: Optional custom branch name (default: dev{timestamp})
#   --force: Override hard stops for uncommitted/unpushed changes
#   --new-branch: Skip deleting the current branch (just create new branch)
#
# Examples:
#   ./integrate.sh              # Creates dev{timestamp} branch
#   ./integrate.sh feature/foo  # Creates feature/foo branch
#   ./integrate.sh --force      # Force mode with dev{timestamp}
#   ./integrate.sh newb --force # Creates newb branch in force mode
#   ./integrate.sh --new-branch # Creates new dev{timestamp} without deleting current
#   ./integrate.sh --new-branch feature/bar # Creates feature/bar without deleting current

set -e  # Exit on any error

# Parse arguments
FORCE_MODE=false
NEW_BRANCH_MODE=false
CUSTOM_BRANCH_NAME=""

# First pass: look for --new-branch and get its optional value
for ((i=1; i<=$#; i++)); do
    if [[ "${!i}" == "--new-branch" ]]; then
        NEW_BRANCH_MODE=true
        echo "🌿 NEW BRANCH MODE: Will not delete current branch"
        # Check if next argument exists and is not a flag
        next_idx=$((i + 1))
        if [ $next_idx -le $# ] && [[ "${!next_idx}" != --* ]]; then
            CUSTOM_BRANCH_NAME="${!next_idx}"
        fi
    fi
done

# Second pass: handle other arguments
for arg in "$@"; do
    if [[ "$arg" == "--force" ]]; then
        FORCE_MODE=true
        echo "🚨 FORCE MODE: Overriding safety checks"
    elif [[ "$arg" == "--new-branch" ]]; then
        # Already handled in first pass
        continue
    elif [ -z "$CUSTOM_BRANCH_NAME" ] && [[ "$arg" != --* ]]; then
        # Only set branch name if not already set by --new-branch
        CUSTOM_BRANCH_NAME="$arg"
    fi
done

echo "🔄 Starting integration process..."

# Stop test server for current branch if running
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "🛑 Stopping test server for branch '$current_branch'..."
    ./test_server_manager.sh stop "$current_branch" 2>/dev/null || true
fi

# Check for unmerged changes on current branch
should_delete_branch=false
if [ "$current_branch" != "main" ] && [ "$NEW_BRANCH_MODE" = false ]; then
    echo "⚠️  WARNING: You are on branch '$current_branch'"
    
    # Check if current branch has uncommitted changes - HARD STOP
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "❌ HARD STOP: You have uncommitted changes on '$current_branch'"
        echo "   Staged changes:"
        git diff --cached --name-only | sed 's/^/     /'
        echo "   Unstaged changes:"
        git diff --name-only | sed 's/^/     /'
        echo ""
        if [ "$FORCE_MODE" = true ]; then
            echo "🚨 FORCE MODE: Proceeding anyway (changes will be lost)"
        else
            echo "   Please commit or stash your changes before integrating."
            echo "   Use: git add -A && git commit -m \"your message\""
            echo "   Or:  git stash"
            echo "   Or:  ./integrate.sh --force (to abandon changes)"
            exit 1
        fi
    fi
    
    # Check if current branch has unpushed commits - HARD STOP
    if git status --porcelain=v1 -b | grep -q "ahead"; then
        # Extract commit count from git status output
        commit_count=$(git status --porcelain=v1 -b | grep "ahead" | sed 's/.*ahead \([0-9]*\).*/\1/')
        echo "❌ HARD STOP: Branch '$current_branch' has $commit_count unpushed commit(s):"
        echo ""
        echo "   📋 COMMIT SUMMARY:"
        git log --oneline -n "$commit_count" | head -10 | sed 's/^/     /'
        echo ""
        echo "   📊 FILES CHANGED:"
        git diff --name-only HEAD~"$commit_count" | head -10 | sed 's/^/     /'
        echo ""
        if [ "$FORCE_MODE" = true ]; then
            echo "🚨 FORCE MODE: Proceeding anyway (unpushed commits will be abandoned)"
        else
            echo "   Please push these changes or create a PR before integrating."
            echo "   Use: git push origin HEAD:$current_branch"
            echo "   Or:  gh pr create"
            echo "   Or:  ./integrate.sh --force (to abandon commits)"
            exit 1
        fi
    else
        # Branch is clean (no uncommitted changes, no unpushed commits)
        should_delete_branch=true
        echo "✅ Branch '$current_branch' is clean and will be deleted after integration"
    fi
fi

echo "1. Switching to main branch..."
git checkout main

echo "2. Pulling latest changes from origin..."
git pull

# Check if there are any local branches that haven't been pushed
echo "3. Checking for unmerged local branches..."
unpushed_branches=$(git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads | grep -v "main" | grep "\[ahead" || true)
if [ -n "$unpushed_branches" ]; then
    echo "⚠️  WARNING: Found branches with unpushed commits:"
    echo "$unpushed_branches"
    echo ""
fi

echo "4. Determining branch name..."
if [ -n "$CUSTOM_BRANCH_NAME" ]; then
    branch_name="$CUSTOM_BRANCH_NAME"
    echo "   Using custom branch name: $branch_name"
else
    timestamp=$(date +%s)
    branch_name="dev${timestamp}"
    echo "   Using timestamp-based branch name: $branch_name"
fi

echo "5. Creating fresh branch from main..."
git checkout -b "$branch_name"

# Delete the old branch if it was clean (and not in --new-branch mode)
if [ "$should_delete_branch" = true ] && [ "$current_branch" != "main" ] && [ "$NEW_BRANCH_MODE" = false ]; then
    echo "6. Checking if branch '$current_branch' can be safely deleted..."
    
    # Check multiple conditions to determine if branch is safe to delete
    branch_can_be_deleted=false
    deletion_reason=""
    
    # Check 1: Is it merged into local main?
    if git branch --merged main | grep -q "^[[:space:]]*$current_branch$"; then
        branch_can_be_deleted=true
        deletion_reason="merged into local main"
    # Check 2: Is it merged into remote main?
    elif git ls-remote --heads origin | grep -q "refs/heads/$current_branch" && \
         git branch -r --merged origin/main | grep -q "origin/$current_branch"; then
        branch_can_be_deleted=true
        deletion_reason="merged into remote main"
    # Check 3: Does it have a merged PR?
    elif command -v gh >/dev/null 2>&1 && \
         gh pr list --state merged --head "$current_branch" --json number -q '.[0].number' >/dev/null 2>&1; then
        branch_can_be_deleted=true
        deletion_reason="has merged PR"
    fi
    
    if [ "$branch_can_be_deleted" = true ]; then
        echo "   ✓ Branch is safe to delete ($deletion_reason)"
        echo "   Deleting branch '$current_branch'..."
        git branch -D "$current_branch"
        echo "✅ Deleted clean branch '$current_branch'"
    else
        echo "⚠️  Branch '$current_branch' could not be verified as merged"
        echo "   The branch was clean locally but may have unmerged changes"
        echo "   To force delete: git branch -D $current_branch"
    fi
fi

echo "✅ Integration complete! You are now on a fresh '$branch_name' branch with latest main changes."
echo "📍 Current branch: $(git branch --show-current)" 
