#!/bin/bash
# branch-cleanup.sh - Safe branch cleanup with PR checking
# Replaces unreliable /bclean command

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Branch Cleanup Tool${NC}"
echo "======================"

# Help function
show_help() {
    echo "branch-cleanup.sh - Safe branch cleanup with PR checking for Claude Code"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --dry-run      Show what would be deleted without actually deleting"
    echo "  --force        Skip confirmation prompts (use with caution)"
    echo "  --days N       Age threshold for worktree cleanup (default: 2 days)"
    echo ""
    echo "Description:"
    echo "  This script safely cleans up local git branches and worktrees by:"
    echo "  1. Checking for associated PRs (won't delete branches with open PRs)"
    echo "  2. Identifying branches with unpushed commits"
    echo "  3. Preserving main/master and current branch"
    echo "  4. Showing clear status for each branch before deletion"
    echo "  5. Cleaning up stale worktrees based on commit age"
    echo ""
    echo "Safety features:"
    echo "  - Never deletes main/master branch"
    echo "  - Never deletes current branch"
    echo "  - Warns about branches with open PRs"
    echo "  - Shows unpushed commits before deletion"
    echo "  - Preserves worktrees with uncommitted changes"
    echo "  - Configurable age threshold for worktrees"
    echo "  - Dry-run mode for safe preview"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run         # Preview what would be deleted"
    echo "  $0                   # Interactive cleanup with confirmations"
    echo "  $0 --force           # Delete without confirmations (dangerous!)"
    echo "  $0 --days 7          # Clean worktrees older than 7 days"
    echo "  $0 --dry-run --days 1  # Preview cleanup of 1-day-old worktrees"
    exit 0
}

# Parse arguments
DRY_RUN=false
FORCE=false
WORKTREE_DAYS=2

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --days)
            WORKTREE_DAYS="$2"
            if ! [[ "$WORKTREE_DAYS" =~ ^[0-9]+$ ]]; then
                echo "Error: --days must be a positive integer"
                exit 1
            fi
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--force] [--days N]"
            echo "Use --help for more information"
            exit 1
            ;;
    esac
done

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}🔍 DRY RUN MODE - No branches will be deleted${NC}\n"
fi

# Get current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Ensure we're not on a branch we might delete
if [[ "$current_branch" != "main" ]] && [[ "$current_branch" != "master" ]]; then
    echo -e "${YELLOW}⚠️  Warning: You're on branch '$current_branch'${NC}"
    echo "   Switching to main to avoid conflicts..."
    git checkout main 2>/dev/null || git checkout master 2>/dev/null || {
        echo -e "${RED}❌ Could not switch to main/master branch${NC}"
        exit 1
    }
fi

echo -e "\n${GREEN}🔍 Scanning for branches to clean...${NC}"

# Get all local branches except main/master
branches_to_check=$(git branch --format='%(refname:short)' | grep -v -E '^(main|master)$')

# Arrays to track branches
declare -a safe_to_delete=()
declare -a has_pr=()
declare -a unmerged=()

# Check each branch
for branch in $branches_to_check; do
    # Skip if no branch (empty line)
    [[ -z "$branch" ]] && continue
    
    echo -n "Checking $branch... "
    
    # Check if branch has unpushed commits
    if git rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
        unpushed=$(git rev-list "origin/$branch..$branch" --count 2>/dev/null || echo "0")
    else
        unpushed="no remote"
    fi
    
    # Check for associated PR
    pr_info=$(gh pr list --head "$branch" --json number,state --limit 1 2>/dev/null || echo "[]")
    pr_exists=$(echo "$pr_info" | jq 'length > 0')
    
    if [[ "$pr_exists" == "true" ]]; then
        pr_number=$(echo "$pr_info" | jq -r '.[0].number')
        pr_state=$(echo "$pr_info" | jq -r '.[0].state')
        echo -e "${YELLOW}PR #$pr_number ($pr_state)${NC}"
        has_pr+=("$branch - PR #$pr_number ($pr_state)")
    elif [[ "$unpushed" != "0" ]] && [[ "$unpushed" != "no remote" ]]; then
        echo -e "${YELLOW}$unpushed unpushed commits${NC}"
        unmerged+=("$branch - $unpushed unpushed commits")
    else
        # Check if merged to main
        if git merge-base --is-ancestor "$branch" main 2>/dev/null; then
            echo -e "${GREEN}merged to main${NC}"
            safe_to_delete+=("$branch")
        else
            echo -e "${YELLOW}not merged${NC}"
            unmerged+=("$branch - not merged to main")
        fi
    fi
done

# Display summary
echo -e "\n${BLUE}📊 Summary${NC}"
echo "=========="
echo "Total branches scanned: $(echo "$branches_to_check" | wc -l)"
echo "Safe to delete: ${#safe_to_delete[@]}"
echo "Have PRs: ${#has_pr[@]}"
echo "Unmerged/unpushed: ${#unmerged[@]}"

# Show branches by category
if [[ ${#safe_to_delete[@]} -gt 0 ]]; then
    echo -e "\n${GREEN}✅ Safe to delete (merged to main):${NC}"
    printf '%s\n' "${safe_to_delete[@]}" | sed 's/^/  - /'
fi

if [[ ${#has_pr[@]} -gt 0 ]]; then
    echo -e "\n${YELLOW}🔗 Have associated PRs (kept):${NC}"
    printf '%s\n' "${has_pr[@]}" | sed 's/^/  - /'
fi

if [[ ${#unmerged[@]} -gt 0 ]]; then
    echo -e "\n${YELLOW}⚠️  Unmerged/unpushed (kept):${NC}"
    printf '%s\n' "${unmerged[@]}" | sed 's/^/  - /'
fi

# Delete safe branches
if [[ ${#safe_to_delete[@]} -gt 0 ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "\n${YELLOW}🔍 DRY RUN: Would delete ${#safe_to_delete[@]} branches${NC}"
    else
        echo -e "\n${YELLOW}🗑️  Preparing to delete ${#safe_to_delete[@]} branches...${NC}"
        
        if [[ "$FORCE" != "true" ]]; then
            echo -n "Continue? (y/N) "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                echo "Cancelled."
                exit 0
            fi
        fi
        
        # Delete branches
        for branch in "${safe_to_delete[@]}"; do
            echo -n "Deleting $branch... "
            if git branch -D "$branch"; then
                echo -e "${GREEN}✓${NC}"
            else
                echo -e "${RED}✗${NC}"
            fi
        done
        
        echo -e "\n${GREEN}✅ Cleanup complete!${NC}"
    fi
else
    echo -e "\n${GREEN}✅ No branches to clean up!${NC}"
fi

# Worktree cleanup section
echo -e "\n${BLUE}🏠 Checking worktrees for cleanup...${NC}"

# Get current worktree path for comparison
CURRENT_WORKTREE=$(git rev-parse --show-toplevel)

# Get all worktrees
WORKTREES=$(git worktree list --porcelain 2>/dev/null | grep '^worktree ' | awk '{print $2}' || echo "")

# Arrays to track worktrees
declare -a worktrees_to_delete=()
declare -a worktrees_kept=()

if [[ -n "$WORKTREES" ]]; then
    for wt in $WORKTREES; do
        # Skip main worktree
        if [[ "$wt" == "$CURRENT_WORKTREE" ]]; then
            continue
        fi
        
        echo -n "Checking worktree $(basename "$wt")... "
        
        # Check if worktree directory exists
        if [[ ! -d "$wt" ]]; then
            echo -e "${RED}missing directory${NC}"
            worktrees_to_delete+=("$wt - missing directory")
            continue
        fi
        
        # Get the branch for this worktree
        WT_BRANCH=$(git --git-dir="$wt/.git" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
        if [[ -z "$WT_BRANCH" ]]; then
            echo -e "${RED}no branch${NC}"
            worktrees_to_delete+=("$wt - no branch")
            continue
        fi
        
        # Check for uncommitted changes
        if [[ -n $(git --git-dir="$wt/.git" --work-tree="$wt" status --porcelain 2>/dev/null) ]]; then
            echo -e "${YELLOW}uncommitted changes${NC}"
            worktrees_kept+=("$wt ($WT_BRANCH) - uncommitted changes")
            continue
        fi
        
        # Check branch's last commit date
        COMMIT_DATE=$(git --git-dir="$wt/.git" log -1 --format="%cI" 2>/dev/null || echo "")
        if [[ -n "$COMMIT_DATE" ]]; then
            COMMIT_AGE_DAYS=$(( ($(date +%s) - $(date -d "$COMMIT_DATE" +%s)) / 86400 ))
            if [[ $COMMIT_AGE_DAYS -gt $WORKTREE_DAYS ]]; then
                echo -e "${GREEN}stale ($COMMIT_AGE_DAYS days old)${NC}"
                worktrees_to_delete+=("$wt ($WT_BRANCH) - $COMMIT_AGE_DAYS days old")
            else
                echo -e "${YELLOW}recent ($COMMIT_AGE_DAYS days old)${NC}"
                worktrees_kept+=("$wt ($WT_BRANCH) - $COMMIT_AGE_DAYS days old")
            fi
        else
            echo -e "${YELLOW}no commits${NC}"
            worktrees_kept+=("$wt ($WT_BRANCH) - no commits")
        fi
    done
else
    echo "No additional worktrees found."
fi

# Display worktree summary
if [[ ${#worktrees_to_delete[@]} -gt 0 ]] || [[ ${#worktrees_kept[@]} -gt 0 ]]; then
    echo -e "\n${BLUE}🏠 Worktree Summary${NC}"
    echo "=================="
    echo "Stale worktrees (>${WORKTREE_DAYS} days): ${#worktrees_to_delete[@]}"
    echo "Active worktrees (kept): ${#worktrees_kept[@]}"
    
    if [[ ${#worktrees_to_delete[@]} -gt 0 ]]; then
        echo -e "\n${GREEN}✅ Stale worktrees (ready for cleanup):${NC}"
        printf '%s\n' "${worktrees_to_delete[@]}" | sed 's/^/  - /'
    fi
    
    if [[ ${#worktrees_kept[@]} -gt 0 ]]; then
        echo -e "\n${YELLOW}🏠 Active worktrees (kept):${NC}"
        printf '%s\n' "${worktrees_kept[@]}" | sed 's/^/  - /'
    fi
fi

# Delete stale worktrees
if [[ ${#worktrees_to_delete[@]} -gt 0 ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "\n${YELLOW}🔍 DRY RUN: Would remove ${#worktrees_to_delete[@]} worktrees${NC}"
    else
        echo -e "\n${YELLOW}🗑️  Preparing to remove ${#worktrees_to_delete[@]} worktrees...${NC}"
        
        if [[ "$FORCE" != "true" ]]; then
            echo -n "Continue with worktree cleanup? (y/N) "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                echo "Worktree cleanup cancelled."
            else
                # Remove worktrees
                for wt_info in "${worktrees_to_delete[@]}"; do
                    wt_path=$(echo "$wt_info" | cut -d' ' -f1)
                    echo -n "Removing worktree $(basename "$wt_path")... "
                    if git worktree remove --force "$wt_path" 2>/dev/null; then
                        echo -e "${GREEN}✓${NC}"
                    else
                        echo -e "${RED}✗${NC}"
                    fi
                done
                echo -e "\n${GREEN}✅ Worktree cleanup complete!${NC}"
            fi
        else
            # Force mode - remove without confirmation
            for wt_info in "${worktrees_to_delete[@]}"; do
                wt_path=$(echo "$wt_info" | cut -d' ' -f1)
                echo -n "Removing worktree $(basename "$wt_path")... "
                if git worktree remove --force "$wt_path" 2>/dev/null; then
                    echo -e "${GREEN}✓${NC}"
                else
                    echo -e "${RED}✗${NC}"
                fi
            done
            echo -e "\n${GREEN}✅ Worktree cleanup complete!${NC}"
        fi
    fi
else
    echo -e "\n${GREEN}✅ No stale worktrees to clean up!${NC}"
fi

# Offer to prune remotes
echo -e "\n${BLUE}💡 Tip:${NC} To clean up deleted remote branches, run:"
echo "  git remote prune origin"