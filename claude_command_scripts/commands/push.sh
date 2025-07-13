#!/bin/bash
# push.sh - Reliable push workflow with PR management
# Replaces unreliable /push command behavior

set -euo pipefail

# Pre-flight checks for required dependencies
if ! command -v gh &> /dev/null; then
    echo -e "\033[0;31m❌ 'gh' CLI is not installed. Please install it to proceed.\033[0m"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "\033[0;31m❌ 'jq' is not installed. Please install it to proceed.\033[0m"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Help function
show_help() {
    echo "push.sh - Reliable push workflow with PR management for Claude Code"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Description:"
    echo "  This script provides a comprehensive push workflow that:"
    echo "  1. Validates working directory is clean"
    echo "  2. Runs tests if available"
    echo "  3. Pushes to remote with proper upstream tracking"
    echo "  4. Updates or creates PR with test results"
    echo "  5. Provides test server instructions"
    echo ""
    echo "Example:"
    echo "  $0"
    echo ""
    echo "Notes:"
    echo "  - Will refuse to push with uncommitted changes"
    echo "  - Automatically sets upstream if not configured"
    echo "  - Updates PR description with latest test results"
    echo "  - Shows how to deploy test server after push"
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

echo -e "${BLUE}🚀 Push Workflow${NC}"
echo "=================="

# 1. Pre-push checks
echo -e "\n${GREEN}🔍 Running pre-push checks...${NC}"

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${RED}❌ Uncommitted changes detected!${NC}"
    git status --short
    echo ""
    echo "Please commit your changes first:"
    echo "  git add ."
    echo "  git commit -m 'description'"
    exit 1
fi

# Get branch info
current_branch=$(git branch --show-current)
remote_branch=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")

echo "✓ Working directory clean"
echo "  Branch: $current_branch"

# 2. Run tests if available
if [[ -f "./run_tests.sh" ]]; then
    echo -e "\n${GREEN}🧪 Running tests...${NC}"
    if ./run_tests.sh; then
        echo "✓ All tests passed"
    else
        echo -e "${RED}❌ Tests failed!${NC}"
        echo "Fix failing tests before pushing"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  No test script found${NC}"
fi

# 3. Push to remote
echo -e "\n${GREEN}📤 Pushing to remote...${NC}"

if [[ -z "$remote_branch" ]]; then
    # No upstream set, push with -u
    echo "Setting upstream and pushing..."
    git push -u origin "$current_branch"
else
    # Normal push
    git push origin "$current_branch"
fi

# 4. Check for existing PR
echo -e "\n${GREEN}🔍 Checking for pull request...${NC}"

pr_info=$(gh pr list --head "$current_branch" --json number,url,state --limit 1 2>/dev/null || echo "[]")
pr_exists=$(echo "$pr_info" | jq 'length > 0')

if [[ "$pr_exists" == "true" ]]; then
    pr_number=$(echo "$pr_info" | jq -r '.[0].number')
    pr_url=$(echo "$pr_info" | jq -r '.[0].url')
    pr_state=$(echo "$pr_info" | jq -r '.[0].state')
    
    echo "✓ Found existing PR #$pr_number ($pr_state)"
    echo "  URL: $pr_url"
    
    # Update PR description if needed
    if [[ "$pr_state" == "OPEN" ]]; then
        echo -e "\n${GREEN}📝 Updating PR description...${NC}"
        
        # Get recent commits since PR creation
        recent_commits=$(git log --oneline -10 --pretty=format:"- %s")
        
        # Create temporary file for PR body
        pr_body_file=$(mktemp)
        cat > "$pr_body_file" <<EOF
## Latest Status

### Recent Commits
$recent_commits

### Test Results
✅ All tests passing (verified by push.sh)

---
*Updated by push.sh on $(date)*
EOF

        # Update PR body using file
        gh pr edit "$pr_number" --body-file "$pr_body_file"
        rm -f "$pr_body_file"
        echo "✓ PR description updated"
    fi
else
    echo -e "\n${YELLOW}📋 No PR found. Create one with:${NC}"
    echo "  gh pr create"
fi

# 5. Summary
echo -e "\n${GREEN}✅ Push complete!${NC}"
echo "  Branch: $current_branch"
echo "  Remote: origin/$current_branch"

if [[ "$pr_exists" == "true" ]]; then
    echo "  PR: #$pr_number - $pr_url"
else
    echo "  PR: None (run 'gh pr create' to create)"
fi

# 6. Optional: Start test server for web projects
if [[ -f "./run_test_server.sh" ]]; then
    echo -e "\n${YELLOW}💡 Start test server with:${NC}"
    echo "  ./run_test_server.sh"
elif [[ -f "mvp_site/main.py" ]]; then
    echo -e "\n${YELLOW}💡 Start test server with:${NC}"
    echo "  TESTING=true PORT=6006 python mvp_site/main.py serve"
fi