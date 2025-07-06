#!/bin/bash

# integrate.sh - Updates from main and creates fresh dev branch
# This script implements the standard integration pattern for the project

set -e  # Exit on any error

echo "🔄 Starting integration process..."

# Check for unmerged changes on current branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "⚠️  WARNING: You are on branch '$current_branch'"
    
    # Check if current branch has uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "❌ ERROR: You have uncommitted changes on '$current_branch'"
        echo "   Please commit or stash your changes before integrating."
        exit 1
    fi
    
    # Check if current branch has unpushed commits
    if git log origin/main..HEAD --oneline | grep -q .; then
        echo "⚠️  WARNING: Branch '$current_branch' has unpushed commits:"
        git log origin/main..HEAD --oneline | head -5
        echo ""
        echo "   Consider merging these changes to main or creating a PR before integrating."
        echo "   Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "❌ Integration cancelled."
            exit 1
        fi
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

echo "✅ Integration complete! You are now on a fresh '$branch_name' branch with latest main changes."
echo "📍 Current branch: $(git branch --show-current)" 