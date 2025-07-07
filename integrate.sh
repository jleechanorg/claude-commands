#!/bin/bash

# integrate.sh - Updates from main and creates fresh dev branch
# This script implements the standard integration pattern for the project
# 
# Usage: ./integrate.sh [--force]
#   --force: Override hard stops for uncommitted/unpushed changes

set -e  # Exit on any error

# Check for force flag
FORCE_MODE=false
if [[ "$1" == "--force" ]]; then
    FORCE_MODE=true
    echo "🚨 FORCE MODE: Overriding safety checks"
fi

echo "🔄 Starting integration process..."

# Check for unmerged changes on current branch
current_branch=$(git branch --show-current)
should_delete_branch=false
if [ "$current_branch" != "main" ]; then
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

echo "4. Creating timestamp for unique branch name..."
timestamp=$(date +%s)
branch_name="dev${timestamp}"
echo "   New branch will be: $branch_name"

echo "5. Creating fresh dev branch from main..."
git checkout -b "$branch_name"

# Delete the old branch if it was clean
if [ "$should_delete_branch" = true ] && [ "$current_branch" != "main" ]; then
    echo "6. Deleting clean branch '$current_branch'..."
    git branch -d "$current_branch"
    echo "✅ Deleted clean branch '$current_branch'"
fi

echo "✅ Integration complete! You are now on a fresh '$branch_name' branch with latest main changes."
echo "📍 Current branch: $(git branch --show-current)" 
