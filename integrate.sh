#!/bin/bash
# integrate.sh - This script helps developers integrate the latest changes from main and start fresh on a new branch.
# This script implements the standard integration pattern for the project
# 
# Usage: ./integrate.sh [branch-name] [--force] [--new-branch] [--help]
#   branch-name: Optional custom branch name (default: dev{timestamp})
#   --force: Override hard stops for uncommitted/unpushed changes
#   --new-branch: Skip deleting the current branch (just create new branch)
#   --help: Show detailed help information
#
# Examples:
#   ./integrate.sh              # Creates dev{timestamp} branch
#   ./integrate.sh feature/foo  # Creates feature/foo branch
#   ./integrate.sh --force      # Force mode with dev{timestamp}
#   ./integrate.sh newb --force # Creates newb branch in force mode
#   ./integrate.sh --new-branch # Creates new dev{timestamp} without deleting current
#   ./integrate.sh --new-branch feature/bar # Creates feature/bar without deleting current

set -euo pipefail  # Exit on any error with stricter error handling

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "integrate.sh - Integration workflow for WorldArchitect.AI development"
    echo ""
    echo "Usage: $0 [branch-name] [--force] [--new-branch] [--help]"
    echo ""
    echo "Arguments:"
    echo "  branch-name   Optional custom branch name (default: dev{timestamp})"
    echo ""
    echo "Options:"
    echo "  --force       Override safety checks for uncommitted/unpushed changes"
    echo "  --new-branch  Create new branch without deleting current one"
    echo "  --help        Show this help message"
    echo ""
    echo "Description:"
    echo "  This script provides a comprehensive integration workflow that:"
    echo "  1. Handles uncommitted changes (stash or require commit)"
    echo "  2. Manages unpushed commits (require push or force abandon)"
    echo "  3. Syncs with origin/main (including PR creation for protected branches)"
    echo "  4. Creates fresh development branch from latest main"
    echo "  5. Optionally cleans up old branches"
    echo ""
    echo "Examples:"
    echo "  $0                           # Standard integration with dev{timestamp}"
    echo "  $0 feature/new-auth         # Custom branch name"
    echo "  $0 --force                  # Force integration (abandon local changes)"
    echo "  $0 --new-branch             # Keep current branch, create new one"
    echo "  $0 hotfix/urgent --force    # Force with custom name"
    echo ""
    echo "Safety Features:"
    echo "  - Hard stops for uncommitted changes (unless --force)"
    echo "  - Hard stops for unpushed commits (unless --force)"
    echo "  - Automatic PR creation for protected main branches"
    echo "  - Smart branch cleanup based on merge status"
    echo "  - Test server management integration"
    exit 0
}

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
        echo -e "${RED}🚨 FORCE MODE: Overriding safety checks${NC}"
    elif [[ "$arg" == "--new-branch" ]]; then
        # Already handled in first pass
        continue
    elif [[ "$arg" == "--help" ]] || [[ "$arg" == "-h" ]]; then
        show_help
    elif [ -z "$CUSTOM_BRANCH_NAME" ] && [[ "$arg" != --* ]]; then
        # Only set branch name if not already set by --new-branch
        CUSTOM_BRANCH_NAME="$arg"
    fi
done

echo -e "${GREEN}🔄 Starting integration process...${NC}"

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
        echo -e "${RED}❌ HARD STOP: You have uncommitted changes on '$current_branch'${NC}"
        echo "   Staged changes:"
        git diff --cached --name-only | sed 's/^/     /'
        echo "   Unstaged changes:"
        git diff --name-only | sed 's/^/     /'
        echo ""
        if [ "$FORCE_MODE" = true ]; then
            echo -e "${RED}🚨 FORCE MODE: Proceeding anyway (changes will be lost)${NC}"
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
        echo -e "${RED}❌ HARD STOP: Branch '$current_branch' has $commit_count unpushed commit(s):${NC}"
        echo ""
        echo "   📋 COMMIT SUMMARY:"
        git log --oneline -n "$commit_count" | head -10 | sed 's/^/     /'
        echo ""
        echo "   📊 FILES CHANGED:"
        git diff --name-only HEAD~"$commit_count" | head -10 | sed 's/^/     /'
        echo ""
        if [ "$FORCE_MODE" = true ]; then
            echo -e "${RED}🚨 FORCE MODE: Proceeding anyway (unpushed commits will be abandoned)${NC}"
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
        echo -e "${GREEN}✅ Branch '$current_branch' is clean and will be deleted after integration${NC}"
    fi
fi

echo -e "\n${GREEN}1. Switching to main branch...${NC}"
git checkout main

echo -e "\n${GREEN}2. Smart sync with origin/main...${NC}"
if ! git fetch origin main; then
    echo "❌ Error: Failed to fetch updates from origin/main."
    echo "   Possible causes: network issues, authentication problems, or repository unavailability."
    echo "   Please check your connection and credentials, and try again."
    exit 1
fi

# Helper function to extract GitHub repository URL from git remote
get_github_repo_url() {
    git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/' | sed 's/.git$//'
}

# Helper function to check if we need to wait for existing sync PR
check_existing_sync_pr() {
    if command -v gh >/dev/null 2>&1; then
        # Check for existing sync PRs that might be pending
        existing_pr=$(gh pr list --author "@me" --state open --search "Sync main branch commits (integrate.sh)" --json number,url --jq '.[0] | select(.number != null)' 2>/dev/null || true)
        if [ -n "$existing_pr" ]; then
            pr_number=$(echo "$existing_pr" | jq -r '.number')
            pr_url=$(echo "$existing_pr" | jq -r '.url')
            echo "⚠️  Found existing sync PR #$pr_number: $pr_url"
            echo "   Please merge this PR first, then re-run integrate.sh"
            echo "   Or run: gh pr merge $pr_number --merge"
            exit 1
        fi
    fi
}

# Check for existing sync PRs before proceeding
check_existing_sync_pr

# Detect relationship between local main and origin/main
if git merge-base --is-ancestor HEAD origin/main; then
    # Local main is behind origin/main → safe fast-forward
    echo -e "${GREEN}✅ Fast-forwarding to latest origin/main${NC}"
    if ! git merge --ff-only origin/main; then
        echo "❌ Error: Fast-forward merge with origin/main failed. Please resolve manually." >&2
        exit 1
    fi
    
elif git merge-base --is-ancestor origin/main HEAD; then
    # Local main is ahead of origin/main → create PR for commits
    echo -e "${GREEN}✅ Local main ahead, creating PR to sync${NC}"
    commit_count=$(git rev-list --count origin/main..HEAD)
    echo "   Found $commit_count commits ahead of origin/main"
    
    # Generate timestamp for branch naming
    timestamp=$(date +%Y%m%d-%H%M%S)
    
    # Create temporary branch for PR
    sync_branch="sync-main-$timestamp"
    echo "   Creating sync branch: $sync_branch"
    
    if ! git checkout -b "$sync_branch"; then
        echo "❌ Error: Failed to create sync branch" >&2
        exit 1
    fi
    
    if ! git push -u origin HEAD; then
        echo "❌ Error: Failed to push sync branch" >&2
        exit 1
    fi
    
    # Create PR if gh is available
    if command -v gh >/dev/null 2>&1; then
        pr_title="Sync main branch commits (integrate.sh)"
        # Dynamic commit listing based on count
        commit_limit=${PR_COMMIT_LIMIT:-10}
        if [ "$commit_count" -le "$commit_limit" ]; then
            commit_list=$(git log --oneline origin/main..HEAD)
        else
            commit_list=$(git log --oneline origin/main..HEAD | head -"$commit_limit")
            commit_list="$commit_list
   ...and $((commit_count - commit_limit)) more commits not shown"
        fi
        
        pr_body="Auto-generated PR to sync $commit_count commits that were ahead on local main.

This PR was created by integrate.sh to handle repository branch protection rules.

Commits included:
$commit_list

Please review and merge to complete the integration process."
        
        if pr_url=$(gh pr create --title "$pr_title" --body "$pr_body" 2>/dev/null); then
            echo -e "${GREEN}✅ Created PR: $pr_url${NC}"
            echo "   Please review and merge the PR, then re-run integrate.sh"
            exit 0
        else
            echo "⚠️  Could not create PR automatically. Please create one manually:"
            echo "   Branch: $sync_branch"
            echo "   URL: https://github.com/$(get_github_repo_url)/compare/$sync_branch"
            exit 1
        fi
    else
        echo "⚠️  gh CLI not available. Please create PR manually:"
        echo "   Branch: $sync_branch"
        echo "   URL: https://github.com/$(get_github_repo_url)/compare/$sync_branch"
        exit 1
    fi
    
else
    # Branches have diverged → create PR with merged changes
    echo "⚠️  Local main and origin/main have diverged"
    echo "🔄 Creating merge branch to sync histories..."
    
    # Generate timestamp for branch naming  
    timestamp=$(date +%Y%m%d-%H%M%S)
    
    # Create temporary branch for merge PR
    merge_branch="merge-main-$timestamp"
    echo "   Creating merge branch: $merge_branch"
    
    if ! git checkout -b "$merge_branch"; then
        echo "❌ Error: Failed to create merge branch" >&2
        exit 1
    fi
    
    # Perform the merge on the temporary branch
    if ! git merge --no-ff origin/main -m "integrate.sh: Auto-merge divergent main histories

This merge resolves the divergence between local main (with unpushed commits)
and origin/main (with merged PR changes). This prevents the integration script
from failing and requiring manual intervention.

Equivalent to: git merge --no-ff origin/main"; then
        echo "❌ Error: Auto-merge of divergent main histories failed. Please resolve conflicts manually." >&2
        exit 1
    fi
    
    if ! git push -u origin HEAD; then
        echo "❌ Error: Failed to push merge branch" >&2
        exit 1
    fi
    
    # Create PR if gh is available
    if command -v gh >/dev/null 2>&1; then
        pr_title="Merge divergent main histories (integrate.sh)"
        pr_body="Auto-generated PR to merge divergent main histories.

This PR was created by integrate.sh to handle repository branch protection rules
when local main and origin/main have diverged.

This merge resolves the divergence and allows integration to proceed normally.

Please review and merge to complete the integration process."
        
        if pr_url=$(gh pr create --title "$pr_title" --body "$pr_body" 2>/dev/null); then
            echo -e "${GREEN}✅ Created merge PR: $pr_url${NC}"
            echo "   Please review and merge the PR, then re-run integrate.sh"
            exit 0
        else
            echo "⚠️  Could not create PR automatically. Please create one manually:"
            echo "   Branch: $merge_branch"
            echo "   URL: https://github.com/$(get_github_repo_url)/compare/$merge_branch"
            exit 1
        fi
    else
        echo "⚠️  gh CLI not available. Please create PR manually:"
        echo "   Branch: $merge_branch"
        echo "   URL: https://github.com/$(get_github_repo_url)/compare/$merge_branch"
        exit 1
    fi
fi

# Check if there are any local branches that haven't been pushed
echo -e "\n${GREEN}3. Checking for unmerged local branches...${NC}"
unpushed_branches=$(git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads | grep -v "main" | grep "\[ahead" || true)
if [ -n "$unpushed_branches" ]; then
    echo "⚠️  WARNING: Found branches with unpushed commits:"
    echo "$unpushed_branches"
    echo ""
fi

echo -e "\n${GREEN}4. Determining branch name...${NC}"
if [ -n "$CUSTOM_BRANCH_NAME" ]; then
    branch_name="$CUSTOM_BRANCH_NAME"
    echo "   Using custom branch name: $branch_name"
else
    timestamp=$(date +%s)
    branch_name="dev${timestamp}"
    echo "   Using timestamp-based branch name: $branch_name"
fi

echo -e "\n${GREEN}5. Creating fresh branch from main...${NC}"
git checkout -b "$branch_name"

# Delete the old branch if it was clean (and not in --new-branch mode)
if [ "$should_delete_branch" = true ] && [ "$current_branch" != "main" ] && [ "$NEW_BRANCH_MODE" = false ]; then
    echo -e "\n${GREEN}6. Checking if branch '$current_branch' can be safely deleted...${NC}"
    
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
        echo -e "${GREEN}✅ Deleted clean branch '$current_branch'${NC}"
    else
        echo "⚠️  Branch '$current_branch' could not be verified as merged"
        echo "   The branch was clean locally but may have unmerged changes"
        echo "   To force delete: git branch -D $current_branch"
    fi
fi

echo -e "\n${GREEN}✅ Integration complete! You are now on a fresh '$branch_name' branch with latest main changes.${NC}"
echo -e "${GREEN}📍 Current branch: $(git branch --show-current)${NC}" 
