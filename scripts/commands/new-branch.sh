#!/bin/bash
# new-branch.sh - Create new branch with consistent naming
# Replaces unreliable /nb command

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Help/Usage function
show_help() {
    echo "new-branch.sh - Create new branch with consistent naming for Claude Code"
    echo ""
    echo "Usage: $0 [TYPE] [DESCRIPTION] [OPTIONS]"
    echo ""
    echo "Types:"
    echo "  feature   - New feature branch (feature/description)"
    echo "  fix       - Bug fix branch (fix/description)"
    echo "  update    - Update/refactor branch (update/description)"
    echo "  test      - Testing branch (test/description)"
    echo "  docs      - Documentation branch (docs/description)"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  --from BRANCH    Create from specific branch (default: main)"
    echo "  --no-push        Don't push to remote"
    echo "  --pr             Create PR immediately after push"
    echo ""
    echo "Description:"
    echo "  This script creates branches with consistent naming conventions:"
    echo "  - Handles uncommitted changes via stashing"
    echo "  - Updates base branch before branching"
    echo "  - Optionally pushes to remote and creates PR"
    echo "  - Provides clear next steps"
    echo ""
    echo "Examples:"
    echo "  $0                              # Creates dev[timestamp] branch"
    echo "  $0 feature user-authentication  # Creates feature/user-authentication"
    echo "  $0 fix login-bug --pr          # Creates fix/login-bug and PR"
    echo "  $0 update api --from develop   # Branch from develop instead of main"
    echo ""
    echo "If no arguments provided, creates a dev[timestamp] branch."
    exit 0
}

# Backward compatible usage function
usage() {
    show_help
}

# Defaults
BRANCH_TYPE=""
DESCRIPTION=""
FROM_BRANCH="main"
PUSH_TO_REMOTE=true
CREATE_PR=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --from)
            FROM_BRANCH="$2"
            shift 2
            ;;
        --no-push)
            PUSH_TO_REMOTE=false
            shift
            ;;
        --pr)
            CREATE_PR=true
            shift
            ;;
        feature|fix|update|test|docs)
            BRANCH_TYPE="$1"
            shift
            ;;
        *)
            if [[ -z "$BRANCH_TYPE" ]]; then
                # If no type specified, treat as description
                DESCRIPTION="$1"
            elif [[ -z "$DESCRIPTION" ]]; then
                DESCRIPTION="$1"
            else
                echo -e "${RED}❌ Unknown argument: $1${NC}"
                usage
            fi
            shift
            ;;
    esac
done

echo -e "${BLUE}🌿 New Branch Creator${NC}"
echo "===================="

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}📦 Stashing uncommitted changes...${NC}"
    stash_message="new-branch auto-stash $(date +%Y%m%d_%H%M%S)"
    git stash push -m "$stash_message"
    echo "  Stashed as: $stash_message"
fi

# Generate branch name
if [[ -z "$BRANCH_TYPE" ]] && [[ -z "$DESCRIPTION" ]]; then
    # No arguments - create dev branch
    timestamp=$(date +%Y%m%d%H%M%S)
    NEW_BRANCH="dev${timestamp}"
    echo "Creating development branch..."
elif [[ -n "$BRANCH_TYPE" ]] && [[ -n "$DESCRIPTION" ]]; then
    # Type and description provided
    # Clean description: lowercase, replace spaces with dashes
    clean_desc=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
    NEW_BRANCH="${BRANCH_TYPE}/${clean_desc}"
else
    echo -e "${RED}❌ Must provide both type and description, or neither${NC}"
    usage
fi

# Update base branch
echo -e "\n${GREEN}📥 Updating $FROM_BRANCH...${NC}"
git checkout "$FROM_BRANCH"
git pull origin "$FROM_BRANCH" --rebase

# Create new branch
echo -e "\n${GREEN}🌿 Creating branch: $NEW_BRANCH${NC}"
git checkout -b "$NEW_BRANCH"

# Push to remote if requested
if [[ "$PUSH_TO_REMOTE" == "true" ]]; then
    echo -e "\n${GREEN}📤 Pushing to remote...${NC}"
    git push -u origin "$NEW_BRANCH"

    # Create PR if requested
    if [[ "$CREATE_PR" == "true" ]]; then
        echo -e "\n${GREEN}🔗 Creating pull request...${NC}"

        # Generate PR title
        if [[ -n "$BRANCH_TYPE" ]]; then
            pr_title="${BRANCH_TYPE}: ${DESCRIPTION}"
        else
            pr_title="Development branch $(date +%Y-%m-%d)"
        fi

        # Create PR
        gh pr create \
            --title "$pr_title" \
            --body "## Summary

Created by new-branch.sh

### Branch: $NEW_BRANCH
### Base: $FROM_BRANCH

## Changes
- [ ] Implementation pending

## Testing
- [ ] Tests to be added" \
            --base "$FROM_BRANCH"

        # Get PR info
        pr_info=$(gh pr list --head "$NEW_BRANCH" --json number,url --limit 1)
        pr_number=$(echo "$pr_info" | jq -r '.[0].number')
        pr_url=$(echo "$pr_info" | jq -r '.[0].url')

        echo -e "${GREEN}✅ PR #$pr_number created${NC}"
        echo "  URL: $pr_url"
    fi
fi

# Summary
echo -e "\n${GREEN}✅ Branch created successfully!${NC}"
echo "  Branch: $NEW_BRANCH"
echo "  Based on: $FROM_BRANCH"
if [[ "$PUSH_TO_REMOTE" == "true" ]]; then
    echo "  Remote: origin/$NEW_BRANCH"
fi

# Check for stashed changes
if git stash list | grep -q "new-branch auto-stash"; then
    echo -e "\n${YELLOW}💡 You have stashed changes${NC}"
    echo "  To restore: git stash pop"
fi

# Next steps
echo -e "\n${BLUE}Next steps:${NC}"
echo "  1. Make your changes"
echo "  2. git add . && git commit -m 'description'"
if [[ "$PUSH_TO_REMOTE" == "false" ]]; then
    echo "  3. git push -u origin $NEW_BRANCH"
    echo "  4. gh pr create"
else
    echo "  3. git push"
    if [[ "$CREATE_PR" == "false" ]]; then
        echo "  4. gh pr create"
    fi
fi
