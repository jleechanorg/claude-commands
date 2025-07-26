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
    echo ""
    echo "Description:"
    echo "  This script safely cleans up local git branches by:"
    echo "  1. Checking for associated PRs (won't delete branches with open PRs)"
    echo "  2. Identifying branches with unpushed commits"
    echo "  3. Preserving main/master and current branch"
    echo "  4. Showing clear status for each branch before deletion"
    echo ""
    echo "Safety features:"
    echo "  - Never deletes main/master branch"
    echo "  - Never deletes current branch"
    echo "  - Warns about branches with open PRs"
    echo "  - Shows unpushed commits before deletion"
    echo "  - Dry-run mode for safe preview"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run    # Preview what would be deleted"
    echo "  $0              # Interactive cleanup with confirmations"
    echo "  $0 --force      # Delete without confirmations (dangerous!)"
    exit 0
}

# Parse arguments
DRY_RUN=false
FORCE=false

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
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--force]"
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

# Offer to prune remotes
echo -e "\n${BLUE}💡 Tip:${NC} To clean up deleted remote branches, run:"
echo "  git remote prune origin"
