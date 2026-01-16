---
description: /sync - Synchronize Local Branch with PR
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps sequentially.

## 📋 REFERENCE DOCUMENTATION

# /sync - Synchronize Local Branch with PR

## Description

Synchronizes local branch with a GitHub PR by fetching, switching/creating branch, and ensuring local copy matches remote PR state.

## Usage

- `/sync <pr_number>` - Sync with PR by number
- `/sync <pr_url>` - Sync with PR by GitHub URL

## Implementation

```bash

# Check for required tools

if ! command -v gh >/dev/null 2>&1; then
    echo "❌ Error: GitHub CLI (gh) is required but not installed"
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "❌ Error: jq is required but not installed"
    exit 1
fi

# ALWAYS fetch latest info from remote first - ensures we know about ALL branches
# Fail hard if any remote fetch fails so we don't end up partially pruned
echo "🔄 Fetching latest info from all remotes..."
if ! git fetch --all --prune; then
    echo "❌ Error: Failed to fetch from all remotes. Please resolve git remote issues and try again."
    exit 1
fi
echo "✅ Remote refs updated"

# Parse input to extract PR number

if [[ "$1" =~ ^[0-9]+$ ]]; then
    PR_NUMBER="$1"
elif [[ "$1" =~ github\.com.*pull/([0-9]+) ]]; then
    PR_NUMBER=$(echo "$1" | grep -o 'pull/[0-9]*' | cut -d'/' -f2)
else
    echo "❌ Invalid input. Use PR number or GitHub PR URL"
    exit 1
fi

echo "🔄 Syncing with PR #$PR_NUMBER..."

# Get PR info using gh CLI

PR_INFO=$(gh pr view "$PR_NUMBER" --json headRefName,baseRefName,headRepository 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch PR #$PR_NUMBER info"
    exit 1
fi

# Extract branch information

HEAD_BRANCH=$(echo "$PR_INFO" | jq -r '.headRefName')
BASE_BRANCH=$(echo "$PR_INFO" | jq -r '.baseRefName')
HEAD_REPO=$(echo "$PR_INFO" | jq -r '.headRepository.owner.login')
REMOTE_BRANCH="$HEAD_BRANCH"  # Store original remote branch name

echo "📋 PR #$PR_NUMBER: $HEAD_BRANCH -> $BASE_BRANCH"

# Handle fork PRs using gh pr checkout

if [ "$HEAD_REPO" != "$(gh api repos/:owner/:repo --jq .owner.login)" ]; then
    echo "🔗 Fork detected, using gh pr checkout for proper remote setup..."
    gh pr checkout "$PR_NUMBER"
else
    # Remote refs already fetched at start - proceed with branch operations

    # ALWAYS try to switch to a local branch mirroring the remote branch name
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    SWITCHED_TO_TARGET=false  # Track if we successfully switched to target branch

    # Check if local branch with target name already exists
    if git show-ref --verify --quiet "refs/heads/$HEAD_BRANCH"; then
        # Local branch exists - try to checkout
        if git checkout "$HEAD_BRANCH" 2>/dev/null; then
            echo "🔄 Switched to existing branch: $HEAD_BRANCH"
            SWITCHED_TO_TARGET=true
        else
            # Branch locked in another worktree - find which one
            # Note: git worktree list --porcelain outputs branch as refs/heads/branch-name
            # Use substr to capture full path including spaces (everything after "worktree ")
            WORKTREE_INFO=$(git worktree list --porcelain 2>/dev/null | awk -v br="refs/heads/$HEAD_BRANCH" '/^worktree /{path=substr($0,10)} /^branch / && $2==br {print path}' )
            if [ -z "$WORKTREE_INFO" ]; then
                WORKTREE_INFO="unknown location"
            fi
            echo "⚠️ Branch $HEAD_BRANCH is checked out elsewhere: $WORKTREE_INFO"
            echo "🔄 Attempting to resolve branch conflict with remote..."

            if [ "$WORKTREE_INFO" != "unknown location" ]; then
                # Delete the blocking local branch if possible (only works if not checked out)
                if git branch -D "$HEAD_BRANCH" 2>/dev/null; then
                    echo "✅ Removed stale local branch reference"
                    # Now create fresh branch from remote
                    if git checkout -b "$HEAD_BRANCH" "origin/$REMOTE_BRANCH" 2>/dev/null; then
                        echo "✅ Created fresh local branch: $HEAD_BRANCH"
                        SWITCHED_TO_TARGET=true
                    else
                        echo "❌ Failed to create fresh local branch: $HEAD_BRANCH"
                        echo "🔄 Syncing content on current branch instead..."
                        if ! git fetch origin "$REMOTE_BRANCH"; then
                            echo "❌ Failed to fetch origin/$REMOTE_BRANCH"
                            exit 1
                        fi
                        if ! git reset --hard "origin/$REMOTE_BRANCH"; then
                            echo "❌ Failed to reset to remote state"
                            exit 1
                        fi
                        echo "✅ Content synced to remote state"
                        HEAD_BRANCH="$CURRENT_BRANCH"
                    fi
                else
                    echo "⚠️ Unable to delete $HEAD_BRANCH; it may be active in another worktree"
                    # Cannot delete the blocking branch, so sync content on current branch instead
                    if ! git fetch origin "$REMOTE_BRANCH"; then
                        echo "❌ Failed to fetch origin/$REMOTE_BRANCH"
                        exit 1
                    fi
                    if ! git reset --hard "origin/$REMOTE_BRANCH"; then
                        echo "❌ Failed to reset to remote state"
                        exit 1
                    fi
                    echo "✅ Content synced to remote state"
                    # This is our last resort - stay on current branch but with correct content
                    echo "⚠️ Cannot switch to $HEAD_BRANCH - branch is actively in use elsewhere"
                    echo "📍 Stayed on $CURRENT_BRANCH and replaced content from origin/$REMOTE_BRANCH. If this was intentional local work, consider force-pushing or stashing your changes."
                    HEAD_BRANCH="$CURRENT_BRANCH"
                fi
            else
                echo "❌ Checkout failed for $HEAD_BRANCH and no worktree conflict was detected. Please clean your working tree or stash changes before retrying."
                exit 1
            fi
        fi
    else
        # No local branch exists - create it from remote
        if [ "$CURRENT_BRANCH" != "$HEAD_BRANCH" ]; then
            echo "🔄 Creating local branch to mirror remote: $HEAD_BRANCH"
            if git checkout -b "$HEAD_BRANCH" "origin/$REMOTE_BRANCH" 2>/dev/null; then
                echo "✅ Switched to new local branch: $HEAD_BRANCH"
                SWITCHED_TO_TARGET=true
            else
                echo "❌ Failed to create branch $HEAD_BRANCH"
                echo "🔄 Syncing content on current branch instead..."
                if ! git fetch origin "$REMOTE_BRANCH"; then
                    echo "❌ Failed to fetch origin/$REMOTE_BRANCH"
                    exit 1
                fi
                if ! git reset --hard "origin/$REMOTE_BRANCH"; then
                    echo "❌ Failed to reset to remote state"
                    exit 1
                fi
                echo "✅ Content synced to remote state"
                HEAD_BRANCH="$CURRENT_BRANCH"
            fi
        else
            # Edge case: Already on a branch with target name but ref doesn't exist
            # (can happen with corrupted refs or detached HEAD with matching name)
            echo "ℹ️ Already on target branch name; ensuring content is up to date..."
            SWITCHED_TO_TARGET=true
            if ! git fetch origin "$REMOTE_BRANCH"; then
                echo "❌ Failed to fetch origin/$REMOTE_BRANCH"
                exit 1
            fi
            if ! git reset --hard "origin/$REMOTE_BRANCH"; then
                echo "❌ Failed to reset to remote state"
                exit 1
            fi
            echo "✅ Content synced to remote state on $CURRENT_BRANCH"
        fi
    fi

    # Set upstream tracking only if we successfully switched to target branch
    # (Don't corrupt upstream tracking on fallback branches)
    if [ "$SWITCHED_TO_TARGET" = "true" ]; then
        echo "🔗 Setting upstream tracking..."
        git branch --set-upstream-to=origin/"$REMOTE_BRANCH" "$HEAD_BRANCH"

        # Pull latest changes
        echo "⬇️ Pulling latest changes..."
        if git pull origin "$REMOTE_BRANCH" 2>/dev/null; then
            echo "✅ Successfully pulled changes"
        else
            echo "⚠️ Pull failed, trying to reset to remote state..."
            if ! git reset --hard origin/"$REMOTE_BRANCH"; then
                echo "❌ Failed to reset to remote state"
                exit 1
            fi
            echo "✅ Reset to remote state successful"
        fi
    else
        echo "⚠️ Skipping upstream tracking (fell back to $HEAD_BRANCH, not target branch)"
        echo "📍 Content synced but branch name differs from PR branch"
    fi
fi

# Verify sync status

echo "🔍 Verifying sync status..."
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/"$REMOTE_BRANCH" 2>/dev/null || echo "unknown")

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    echo "✅ Local branch perfectly synced with remote"
else
    echo "⚠️ Local/remote mismatch detected"
    echo "   Local:  $LOCAL_COMMIT"
    echo "   Remote: $REMOTE_COMMIT"
fi

# Show current status

echo "📊 Current status:"
git status --short
echo "📍 Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo "✨ Synced with PR #$PR_NUMBER ($REMOTE_BRANCH)"
```

## Success Criteria

- ✅ Branch exists locally and matches remote
- ✅ All changes from PR are present
- ✅ Clean working directory
- ✅ Upstream tracking configured
