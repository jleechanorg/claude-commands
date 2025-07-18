#!/bin/bash
# integrate.sh - Reliable integration workflow
# Replaces unreliable /integrate command behavior with deterministic script

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "integrate.sh - Reliable integration workflow for Claude Code"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Description:"
    echo "  This script provides a deterministic integration workflow that:"
    echo "  1. Stashes any uncommitted changes"
    echo "  2. Updates the main branch from origin"
    echo "  3. Creates a new dev[timestamp] branch"
    echo "  4. Provides clear next steps"
    echo ""
    echo "Example:"
    echo "  $0"
    echo ""
    echo "Notes:"
    echo "  - Uncommitted changes are automatically stashed with descriptive names"
    echo "  - Uses 'git pull --rebase' to avoid merge commits"
    echo "  - Creates timestamp-based branch names for uniqueness"
    exit 0
}

# Parse command line arguments
if [[ $# -gt 0 ]]; then
    case "$1" in
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
fi

echo -e "${GREEN}🔄 Starting integration workflow...${NC}"

# 1. Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}📦 Stashing uncommitted changes...${NC}"
    stash_message="integrate.sh auto-stash $(date +%Y%m%d_%H%M%S)"
    # Include untracked files to ensure clean checkout
    git stash push -u -m "$stash_message"
    echo "  Stashed as: $stash_message (including untracked files)"
else
    echo "✓ Working directory clean"
fi

# 2. Save current branch name (for reference)
current_branch=$(git branch --show-current)
echo "  Current branch: $current_branch"

# 3. Update main branch
echo -e "\n${GREEN}📥 Updating main branch...${NC}"
git checkout main

# Pull with rebase to avoid merge commits
git pull origin main --rebase

# 4. Create new development branch
timestamp=$(date +%Y%m%d%H%M%S)
new_branch="dev${timestamp}"
git checkout -b "$new_branch"

# 5. Show summary
echo -e "\n${GREEN}✅ Integration complete!${NC}"
echo "  Previous branch: $current_branch"
echo "  New branch: $new_branch"
echo ""
echo "Next steps:"
echo "  - Start working on your feature"
echo "  - When ready: git add . && git commit -m 'feat: description'"
echo "  - Create PR: gh pr create"

# Check if there was a stash
if git stash list | grep -q "integrate.sh auto-stash"; then
    echo -e "\n${YELLOW}💡 Note: You have stashed changes${NC}"
    echo "  To restore: git stash pop"
fi