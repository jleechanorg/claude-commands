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
    # Fetch all remote refs
    echo "🔄 Fetching remote refs..."
    git fetch origin

    # Try to switch to matching local branch name first
    if git rev-parse --verify "$HEAD_BRANCH" >/dev/null 2>&1; then
        # Check if branch is available (not checked out in another worktree)
        if git checkout "$HEAD_BRANCH" 2>/dev/null; then
            echo "🔄 Switched to existing branch: $HEAD_BRANCH"
        else
            echo "⚠️ Branch $HEAD_BRANCH exists but is checked out in another worktree"
            echo "🔄 Staying on current branch and syncing with remote content"
            CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
            echo "📍 Using current branch: $CURRENT_BRANCH"
            # Update HEAD_BRANCH to current for tracking setup
            HEAD_BRANCH="$CURRENT_BRANCH"
        fi
    else
        # Check if we need to switch from current branch to match remote name
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        if [ "$CURRENT_BRANCH" != "$HEAD_BRANCH" ]; then
            echo "🔄 Creating local branch to match remote: $HEAD_BRANCH"
            git checkout -b "$HEAD_BRANCH"
        fi
    fi

    # Set upstream tracking to origin (use original remote branch name) when not already configured
    if ! git rev-parse --abbrev-ref --symbolic-full-name "${HEAD_BRANCH}@{u}" >/dev/null 2>&1; then
        echo "🔗 Setting upstream tracking..."
        if ! git branch --set-upstream-to=origin/"$REMOTE_BRANCH" "$HEAD_BRANCH" >/dev/null 2>&1; then
            echo "⚠️ Unable to set upstream to origin/$REMOTE_BRANCH automatically" >&2
        fi
    fi

    # Pull latest changes
    echo "⬇️ Pulling latest changes..."
    if git pull origin "$REMOTE_BRANCH" 2>/dev/null; then
        echo "✅ Successfully pulled changes"
    else
        echo "⚠️ Pull failed, trying to reset to remote state..."
        git reset --hard origin/"$REMOTE_BRANCH"
    fi
fi

# Verify sync status
echo "🔍 Verifying sync status..."
LOCAL_COMMIT=$(git rev-parse HEAD)
UPSTREAM_REF=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
if [ -n "$UPSTREAM_REF" ]; then
    REMOTE_COMMIT=$(git rev-parse "$UPSTREAM_REF" 2>/dev/null || echo "unknown")
else
    REMOTE_COMMIT=$(git rev-parse origin/"$REMOTE_BRANCH" 2>/dev/null || echo "unknown")
fi

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
echo "✨ Synced with PR #$PR_NUMBER (${UPSTREAM_REF:-origin/$REMOTE_BRANCH})"
```

## Success Criteria
- ✅ Branch exists locally and matches remote
- ✅ All changes from PR are present
- ✅ Clean working directory
- ✅ Upstream tracking configured
