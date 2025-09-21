# /sync - Synchronize Local Branch with PR

## Description
Synchronizes local branch with a GitHub PR by fetching, switching/creating branch, and ensuring local copy matches remote PR state.

## Usage
- `/sync <pr_number>` - Sync with PR by number
- `/sync <pr_url>` - Sync with PR by GitHub URL

## Implementation

```bash
# Parse input to extract PR number
if [[ "$1" =~ ^[0-9]+$ ]]; then
    PR_NUMBER="$1"
elif [[ "$1" =~ github\.com.*pull/([0-9]+) ]]; then
    PR_NUMBER=$(echo "$1" | grep -o 'pull/[0-9]*' | cut -d'/' -f2)
else
    echo "L Invalid input. Use PR number or GitHub PR URL"
    exit 1
fi

echo "= Syncing with PR #$PR_NUMBER..."

# Get PR info using gh CLI
PR_INFO=$(gh pr view "$PR_NUMBER" --json headRefName,baseRefName,headRepository 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "L Failed to fetch PR #$PR_NUMBER info"
    exit 1
fi

# Extract branch information
HEAD_BRANCH=$(echo "$PR_INFO" | jq -r '.headRefName')
BASE_BRANCH=$(echo "$PR_INFO" | jq -r '.baseRefName')
HEAD_REPO=$(echo "$PR_INFO" | jq -r '.headRepository.owner.login')

echo "=Ë PR #$PR_NUMBER: $HEAD_BRANCH -> $BASE_BRANCH"

# Fetch all remote refs
echo "= Fetching remote refs..."
git fetch origin

# Check if local branch exists
if git rev-parse --verify "$HEAD_BRANCH" >/dev/null 2>&1; then
    echo "= Switching to existing branch: $HEAD_BRANCH"
    git checkout "$HEAD_BRANCH"
else
    echo "<• Creating new branch: $HEAD_BRANCH"
    git checkout -b "$HEAD_BRANCH"
fi

# Set upstream tracking to origin
echo "= Setting upstream tracking..."
git branch --set-upstream-to=origin/"$HEAD_BRANCH" "$HEAD_BRANCH"

# Pull latest changes
echo " Pulling latest changes..."
if git pull origin "$HEAD_BRANCH" 2>/dev/null; then
    echo " Successfully pulled changes"
else
    echo "  Pull failed, trying to reset to remote state..."
    git reset --hard origin/"$HEAD_BRANCH"
fi

# Verify sync status
echo "= Verifying sync status..."
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/"$HEAD_BRANCH" 2>/dev/null || echo "unknown")

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    echo " Local branch perfectly synced with remote"
else
    echo "  Local/remote mismatch detected"
    echo "   Local:  $LOCAL_COMMIT"
    echo "   Remote: $REMOTE_COMMIT"
fi

# Show current status
echo "=Ê Current status:"
git status --short
echo "=Í Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo "<¯ Synced with PR #$PR_NUMBER ($HEAD_BRANCH)"
```

## Success Criteria
-  Branch exists locally and matches remote
-  All changes from PR are present
-  Clean working directory
-  Upstream tracking configured