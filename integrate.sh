#!/bin/bash
# integrate.sh - This script helps developers integrate the latest changes from main and start fresh on a new branch.
# This script implements the standard integration pattern for the project
# 
# Usage: ./integrate.sh [branch-name] [--force] [--new-branch]
#   branch-name: Optional custom branch name (default: dev{timestamp})
#   --force: Override hard stops for uncommitted/unpushed changes and integration PR warnings
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

# Source ~/.bashrc to ensure environment is properly set up
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Show help if requested
show_help() {
    cat << 'EOF'
integrate.sh - Integration workflow for fresh branch creation

USAGE:
    ./integrate.sh [branch-name] [--force] [--new-branch] [--help]

ARGUMENTS:
    branch-name     Optional custom branch name (default: dev{timestamp})

OPTIONS:
    --force         Override hard stops for uncommitted/unpushed changes and integration PR warnings
    --new-branch    Skip deleting the current branch (just create new branch)
    --help          Show this help message

EXAMPLES:
    ./integrate.sh                    # Creates dev{timestamp} branch
    ./integrate.sh feature/foo        # Creates feature/foo branch  
    ./integrate.sh --force            # Force mode with dev{timestamp}
    ./integrate.sh newb --force       # Creates newb branch in force mode
    ./integrate.sh --new-branch       # Creates new dev{timestamp} without deleting current
    ./integrate.sh --new-branch bar   # Creates bar branch without deleting current

SAFETY FEATURES:
    • Hard stops for uncommitted changes (override with --force)
    • Hard stops for unpushed commits (override with --force)
    • Warnings for integration PR conflicts (override with --force)
    • Smart branch deletion only when safe (merged/clean branches)
    • Automatic PR creation for divergent main histories

WORKFLOW:
    1. Check current branch safety (uncommitted/unpushed changes)
    2. Switch to main branch
    3. Smart sync with origin/main (handles divergence)
    4. Check for problematic integration PRs
    5. Create fresh branch from updated main
    6. Optionally delete old branch if safe

EOF
}

# Parse arguments
FORCE_MODE=false
NEW_BRANCH_MODE=false
CUSTOM_BRANCH_NAME=""

# Check for help first
for arg in "$@"; do
    if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
        show_help
        exit 0
    fi
done

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

echo "2. Smart sync with origin/main..."
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

# Helper function to check if we need to wait for existing integration-related PRs
check_existing_sync_pr() {
    if command -v gh >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        # Check for sync PRs created by this script (exact title match) - collect into proper JSON array
        existing_sync_prs=$(gh pr list --author "@me" --state open --json number,url,title 2>/dev/null | jq -c '[ .[] | select(.title == "Sync main branch commits (integrate.sh)") ]' || echo '[]')
        sync_count=$(echo "$existing_sync_prs" | jq 'length')
        
        if [ "$sync_count" -gt 0 ]; then
            if [ "$sync_count" -eq 1 ]; then
                # Single sync PR - extract details
                pr_number=$(echo "$existing_sync_prs" | jq -r '.[0].number')
                pr_url=$(echo "$existing_sync_prs" | jq -r '.[0].url')
                echo "⚠️  Found existing sync PR #$pr_number: $pr_url"
                echo "   This PR was created by integrate.sh to sync main branch"
            else
                # Multiple sync PRs - list them all
                echo "⚠️  Found $sync_count existing sync PRs created by integrate.sh:"
                echo "$existing_sync_prs" | jq -r '.[] | "   PR #\(.number): \(.url)"'
                echo "   Please merge these PRs first, then re-run integrate.sh"
            fi
            
            if [ "$FORCE_MODE" = true ]; then
                echo "🚨 FORCE MODE: Proceeding with integration despite sync PR(s)"
                return 0
            else
                if [ "$sync_count" -eq 1 ]; then
                    pr_number=$(echo "$existing_sync_prs" | jq -r '.[0].number')
                    echo "   Please merge this PR first, then re-run integrate.sh"
                    echo "   Or run: gh pr merge $pr_number --merge"
                else
                    echo "   Please merge these PRs first, then re-run integrate.sh"
                fi
                echo "   Or use: ./integrate.sh --force (to proceed anyway)"
                exit 1
            fi
        fi
        
        # Check for any open PRs that modify integrate.sh or integration workflows (informational only)
        integration_prs=$(gh pr list --state open --limit 50 --json number,url,title,files 2>/dev/null | jq -c '[ .[] | select(.files[]?.filename | test("integrate\\.sh|integration")) ]' || echo '[]')
        pr_count=$(echo "$integration_prs" | jq 'length')
        
        if [ "$pr_count" -gt 0 ]; then
            echo "ℹ️  Found $pr_count open PR(s) modifying integration workflows:"
            echo "$integration_prs" | jq -r '.[] | "   PR #\(.number): \(.title) - \(.url)"'
            echo ""
            echo "   These PRs modify integration infrastructure but don't block your current branch."
            echo "   Integration will proceed normally."
            echo ""
        fi
    elif command -v gh >/dev/null 2>&1; then
        # Fallback when jq is not available - only check for exact sync PRs
        echo "ℹ️  Checking for integration conflicts (jq not available, using basic check)..."
        sync_prs=$(gh pr list --author "@me" --state open --search "Sync main branch commits" 2>/dev/null || true)
        if [ -n "$sync_prs" ]; then
            echo "⚠️  Found potential sync PR(s). If integration fails, try:"
            echo "   ./integrate.sh --force"
        fi
    fi
}

# Check for existing sync PRs before proceeding
check_existing_sync_pr

# Detect relationship between local main and origin/main
if git merge-base --is-ancestor HEAD origin/main; then
    # Local main is behind origin/main → safe fast-forward
    echo "✅ Fast-forwarding to latest origin/main"
    if ! git merge --ff-only origin/main; then
        echo "❌ Error: Fast-forward merge with origin/main failed. Please resolve manually." >&2
        exit 1
    fi
    
elif git merge-base --is-ancestor origin/main HEAD; then
    # Local main is ahead of origin/main → create PR for commits
    echo "✅ Local main ahead, creating PR to sync"
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
            echo "✅ Created PR: $pr_url"
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
            echo "✅ Created merge PR: $pr_url"
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
