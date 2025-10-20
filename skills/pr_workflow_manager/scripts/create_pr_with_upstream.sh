#!/bin/bash
# PR Creation with Upstream Tracking
# Ensures proper git configuration for all pull requests

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Determine default branch (supports main/master)
DEFAULT_BRANCH="main"
if git rev-parse --verify --quiet origin/HEAD >/dev/null 2>&1; then
    DEFAULT_BRANCH=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | cut -d'/' -f2)
elif git rev-parse --verify --quiet origin/master >/dev/null 2>&1; then
    DEFAULT_BRANCH="master"
elif git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
    DEFAULT_BRANCH="main"
fi

if [ -z "$DEFAULT_BRANCH" ]; then
    DEFAULT_BRANCH="main"
fi

echo -e "${BLUE}🚀 PR Workflow Manager${NC}"
echo "=================================="
echo ""

# Validate not on protected branch
if [[ "$CURRENT_BRANCH" == "$DEFAULT_BRANCH" ]] || [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "master" ]]; then
    echo -e "${RED}❌ ERROR: Cannot create PR from protected branch '$CURRENT_BRANCH'${NC}"
    echo -e "${YELLOW}💡 Create a feature branch first:${NC}"
    echo "   git checkout -b feature/your-feature-name"
    exit 1
fi

echo -e "${BLUE}📍 Current branch: $CURRENT_BRANCH${NC}"
echo ""

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    echo -e "${YELLOW}💡 Commit your changes first:${NC}"
    echo "   git add ."
    echo "   git commit -m 'Your commit message'"
    exit 1
fi

# Check if branch has commits compared to default branch
BASE_COMPARE_REF=""
if git rev-parse --verify --quiet "origin/$DEFAULT_BRANCH" >/dev/null 2>&1; then
    BASE_COMPARE_REF="origin/$DEFAULT_BRANCH"
elif git rev-parse --verify --quiet "$DEFAULT_BRANCH" >/dev/null 2>&1; then
    BASE_COMPARE_REF="$DEFAULT_BRANCH"
fi

if [ -n "$BASE_COMPARE_REF" ]; then
    COMMITS_AHEAD=$(git rev-list --count "$BASE_COMPARE_REF"..HEAD 2>/dev/null || echo "0")
else
    echo -e "${YELLOW}⚠️  Warning: Unable to determine default branch comparison reference${NC}"
    COMMITS_AHEAD=$(git rev-list --count HEAD 2>/dev/null || echo "0")
fi

if [ "$COMMITS_AHEAD" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: No commits on this branch compared to $DEFAULT_BRANCH${NC}"
    echo -e "${YELLOW}💡 Make some changes and commit first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Validation passed${NC}"
echo ""

# Push with upstream tracking
echo -e "${BLUE}📤 Pushing branch with upstream tracking...${NC}"
if git push -u origin HEAD; then
    echo -e "${GREEN}✅ Branch pushed successfully${NC}"
else
    echo -e "${RED}❌ Failed to push branch${NC}"
    exit 1
fi
echo ""

# Verify upstream is set
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
if [ -z "$UPSTREAM" ]; then
    echo -e "${YELLOW}⚠️  Upstream not set automatically, setting manually...${NC}"
    git branch --set-upstream-to=origin/"$CURRENT_BRANCH" "$CURRENT_BRANCH"
    echo -e "${GREEN}✅ Upstream tracking configured${NC}"
else
    echo -e "${GREEN}✅ Upstream tracking: $UPSTREAM${NC}"
fi
echo ""

# Create PR
echo -e "${BLUE}📝 Creating pull request...${NC}"
PR_URL=""

# Parse optional arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --title)
            PR_TITLE="$2"
            shift 2
            ;;
        --body)
            PR_BODY="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Build gh pr create command (using array to prevent command injection)
GH_ARGS=("gh" "pr" "create" "--base" "$DEFAULT_BRANCH")
if [ -n "${PR_TITLE:-}" ]; then
    GH_ARGS+=("--title" "$PR_TITLE")
fi
if [ -n "${PR_BODY:-}" ]; then
    GH_ARGS+=("--body" "$PR_BODY")
fi

if PR_OUTPUT=$("${GH_ARGS[@]}" 2>&1); then
    PR_URL=$(echo "$PR_OUTPUT" | grep -o 'https://github.com[^ ]*')
    echo -e "${GREEN}✅ PR created successfully${NC}"
    echo ""
    echo -e "${BLUE}🔗 PR URL: ${GREEN}$PR_URL${NC}"
else
    echo -e "${YELLOW}⚠️  PR creation returned: $PR_OUTPUT${NC}"
    # Try to extract URL even if command had warnings
    if echo "$PR_OUTPUT" | grep -q "https://github.com"; then
        PR_URL=$(echo "$PR_OUTPUT" | grep -o 'https://github.com[^ ]*')
        echo -e "${BLUE}🔗 PR URL: ${GREEN}$PR_URL${NC}"
    fi
fi
echo ""

# Final status check
echo -e "${BLUE}📊 Branch Status${NC}"
echo "=================================="
git branch -vv | grep -F "* $CURRENT_BRANCH "
echo ""

echo -e "${GREEN}✅ PR workflow completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
if [ -n "$PR_URL" ]; then
    echo "  • Review your PR: $PR_URL"
else
    echo "  • ⚠️  PR URL could not be determined automatically; verify on GitHub"
fi
echo "  • Monitor CI checks: gh pr checks"
echo "  • Make updates: git commit && git push"
echo "  • Merge when ready: gh pr merge"
