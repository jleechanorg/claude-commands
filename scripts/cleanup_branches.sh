#!/bin/bash

# A two-stage script to intelligently clean up local Git branches.
#
# STAGE 1: Deletes local branches that have already been safely merged.
# STAGE 2: Deletes local branches with no associated GitHub Pull Request.
#
# PREREQUISITES for Stage 2:
# 1. GitHub CLI ('gh') must be installed ('gh auth login').
# 2. 'jq' must be installed ('sudo apt install jq' or 'brew install jq').

# --- CONFIGURATION ---
# Add any other primary branches you want to protect from all deletion.
PROTECTED_BRANCHES='main|master|develop|dev'

# --- ANSI Color Codes ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- HELPER FUNCTION to check for prerequisites ---
check_prereqs() {
    if ! command -v gh &> /dev/null || ! command -v jq &> /dev/null || ! gh auth status &> /dev/null; then
        echo -e "${RED}Prerequisites for Stage 2 are not met.${NC}"
        echo "Please ensure 'gh' (and 'jq') are installed and you are logged in ('gh auth login')."
        read -p "Do you want to skip Stage 2 and only clean up merged branches? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborting."
            exit 1
        fi
        return 1
    fi
    return 0
}

# ==============================================================================
# --- STAGE 1: CLEANUP MERGED BRANCHES ---
# ==============================================================================
echo -e "${CYAN}--- STAGE 1: Deleting MERGED Branches ---${NC}"
echo "This is a safe cleanup of branches whose work is already in your main/develop branch."
echo ""

# The `grep` command filters out the current branch (marked with '*') and protected branches.
MERGED_BRANCHES_TO_DELETE=$(git branch --merged | grep -vE "^\*|${PROTECTED_BRANCHES}")

if [ -z "$MERGED_BRANCHES_TO_DELETE" ]; then
    echo -e "${GREEN}No merged branches to clean up.${NC}"
else
    echo -e "${YELLOW}The following local branches have been merged and will be deleted:${NC}"
    echo -e "${RED}${MERGED_BRANCHES_TO_DELETE}${NC}"
    echo ""
    read -p "Proceed with deleting these ${#MERGED_BRANCHES_TO_DELETE[@]} merged branches? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "${MERGED_BRANCHES_TO_DELETE}" | xargs git branch -d
        echo -e "${GREEN}Stage 1 cleanup complete.${NC}"
    else
        echo "Skipping Stage 1."
    fi
fi

# ==============================================================================
# --- STAGE 2: CLEANUP BRANCHES WITHOUT PULL REQUESTS ---
# ==============================================================================
echo ""
echo -e "${CYAN}--- STAGE 2: Deleting Branches WITHOUT Pull Requests ---${NC}"
echo "This will check for local-only branches and branches on GitHub with no PR."
echo ""

# Check for 'gh' and 'jq' and ask to skip if they are not present
check_prereqs
STAGE2_SKIPPED=$?

if [ $STAGE2_SKIPPED -eq 0 ]; then
    git remote update --prune > /dev/null 2>&1
    echo "Analyzing..."

    NO_PR_BRANCHES_TO_DELETE=()
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

    # Exclude protected branches AND the current branch from the list to check
    LOCAL_BRANCHES_TO_CHECK=$(git branch --format='%(refname:short)' | grep -vE "$PROTECTED_BRANCHES|${CURRENT_BRANCH}")

    for branch in $LOCAL_BRANCHES_TO_CHECK; do
        # Check if the branch exists on the 'origin' remote
        if git rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
            pr_check=$(gh pr list --head "$branch" --state all --json number --limit 1)
            if [ "$(echo "$pr_check" | jq 'length')" -eq 0 ]; then
                NO_PR_BRANCHES_TO_DELETE+=("$branch")
            fi
        else
            # It's a local-only branch, so it has no PR.
            NO_PR_BRANCHES_TO_DELETE+=("$branch")
        fi
    done

    if [ ${#NO_PR_BRANCHES_TO_DELETE[@]} -eq 0 ]; then
        echo -e "${GREEN}No branches without pull requests were found.${NC}"
    else
        echo -e "${YELLOW}The following branches have no PR and will be deleted:${NC}"
        for branch in "${NO_PR_BRANCHES_TO_DELETE[@]}"; do echo -e "  ${RED}$branch${NC}"; done
        echo ""
        read -p "Proceed with deleting these ${#NO_PR_BRANCHES_TO_DELETE[@]} branches? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for branch in "${NO_PR_BRANCHES_TO_DELETE[@]}"; do git branch -D "$branch"; done
            echo -e "${GREEN}Stage 2 cleanup complete.${NC}"
        else
            echo "Skipping Stage 2."
        fi
    fi
fi

echo ""
echo -e "${GREEN}All cleanup operations finished.${NC}"
