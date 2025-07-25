#!/bin/bash

# Auto-resolve conflicts when PR is created/pushed
# Usage: ./scripts/auto_resolve_conflicts.sh [pr_number]

set -e

PR_NUMBER=${1:-$(gh pr view --json number --jq '.number' 2>/dev/null || echo "")}

if [ -z "$PR_NUMBER" ]; then
    echo "❌ No PR number provided and not in PR branch"
    exit 1
fi

echo "🔄 Auto-resolving conflicts for PR #$PR_NUMBER"

# Check if PR has conflicts
MERGE_STATE=$(gh pr view $PR_NUMBER --json mergeStateStatus --jq '.mergeStateStatus')

if [ "$MERGE_STATE" != "DIRTY" ]; then
    echo "✅ PR #$PR_NUMBER has no conflicts (state: $MERGE_STATE)"
    exit 0
fi

echo "⚠️  PR #$PR_NUMBER has conflicts, attempting auto-resolution..."

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Fetch latest main
echo "📥 Fetching latest main..."
git fetch origin main

# Attempt merge
echo "🔀 Attempting to merge main into $CURRENT_BRANCH..."
if git merge origin/main --no-edit; then
    echo "✅ Auto-merge successful!"
else
    echo "⚠️  Merge conflicts detected, attempting auto-resolution..."

    # Try to auto-resolve common conflict patterns
    for file in $(git diff --name-only --diff-filter=U); do
        echo "🔧 Auto-resolving conflicts in $file"

        # Common patterns for learnings.md
        if [[ "$file" == *"learnings.md"* ]]; then
            # Keep both sides of learning content, remove conflict markers
            sed -i '/^<<<<<<< HEAD$/d' "$file"
            sed -i '/^=======$/d' "$file"
            sed -i '/^>>>>>>> origin\/main$/d' "$file"

            # Remove duplicate section headers
            awk '!seen[$0]++' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"

            git add "$file"
            echo "✅ Auto-resolved $file"
        fi

        # Common patterns for CLAUDE.md
        if [[ "$file" == "CLAUDE.md" ]]; then
            # Prefer HEAD version for most conflicts
            git checkout --ours "$file"
            git add "$file"
            echo "✅ Auto-resolved $file (kept our version)"
        fi
    done

    # Check if all conflicts resolved
    if git diff --name-only --diff-filter=U | grep -q .; then
        echo "❌ Some conflicts couldn't be auto-resolved:"
        git diff --name-only --diff-filter=U
        echo "Manual intervention required"
        exit 1
    fi

    # Commit the resolution
    git commit -m "resolve: Auto-resolve merge conflicts

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
fi

# Push the resolution
echo "📤 Pushing conflict resolution..."
git push origin HEAD:$CURRENT_BRANCH

# Verify PR is now mergeable
echo "✅ Checking PR merge status..."
NEW_STATE=$(gh pr view $PR_NUMBER --json mergeStateStatus --jq '.mergeStateStatus')
echo "📊 PR #$PR_NUMBER merge state: $NEW_STATE"

if [ "$NEW_STATE" = "CLEAN" ]; then
    echo "🎉 PR #$PR_NUMBER is now mergeable!"
else
    echo "⚠️  PR #$PR_NUMBER still has issues (state: $NEW_STATE)"
    exit 1
fi
