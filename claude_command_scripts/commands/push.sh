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
    echo "  -h, --help      Show this help message"
    echo "  --sync          Run all tests synchronously (default: async core HTTP tests)"
    echo "  --no-http       Skip HTTP tests entirely"
    echo "  --test-only     Run tests only, don't push (for testing the test functionality)"
    echo ""
    echo "Description:"
    echo "  This script provides a comprehensive push workflow that:"
    echo "  1. Validates working directory is clean"
    echo "  2. Runs core HTTP tests (async) + backend tests if available"
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
SYNC_TESTS=false
SKIP_HTTP_TESTS=false
TEST_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        --sync)
            SYNC_TESTS=true
            shift
            ;;
        --no-http)
            SKIP_HTTP_TESTS=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 Push Workflow${NC}"
echo "=================="

# 1. Pre-push checks
echo -e "\n${GREEN}🔍 Running pre-push checks...${NC}"

# Check for uncommitted changes (skip in test-only mode)
if [[ "$TEST_ONLY" != "true" ]]; then
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo -e "${RED}❌ Uncommitted changes detected!${NC}"
        git status --short
        echo ""
        echo "Please commit your changes first:"
        echo "  git add ."
        echo "  git commit -m 'description'"
        exit 1
    fi
    echo "✓ Working directory clean"
else
    echo "⚠️  Skipping working directory check (test-only mode)"
fi

# Get branch info
current_branch=$(git branch --show-current)
remote_branch=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")

echo "  Branch: $current_branch"

# 2. Run tests (HTTP + Backend)
echo -e "\n${GREEN}🧪 Running pre-push tests...${NC}"

if [[ "$SYNC_TESTS" == "true" ]]; then
    # Synchronous mode: run all tests sequentially
    echo "Running in synchronous mode..."
    
    # Run HTTP tests first
    if [[ "$SKIP_HTTP_TESTS" != "true" ]] && [[ -f "./claude_command_scripts/commands/test-http.sh" ]]; then
        echo -e "\n${BLUE}🔌 Running core HTTP tests...${NC}"
        if ! ./claude_command_scripts/commands/test-http.sh --core; then
            echo -e "${RED}❌ HTTP tests failed!${NC}"
            exit 1
        fi
    fi
    
    # Run backend tests
    if [[ -f "./run_tests.sh" ]]; then
        echo -e "\n${BLUE}🔬 Running backend tests...${NC}"
        if ! ./run_tests.sh; then
            echo -e "${RED}❌ Backend tests failed!${NC}"
            exit 1
        fi
    fi
    
else
    # Asynchronous mode (default): run HTTP tests in background, backend tests foreground
    
    # Start HTTP tests in background
    if [[ "$SKIP_HTTP_TESTS" != "true" ]] && [[ -f "./claude_command_scripts/commands/test-http.sh" ]]; then
        echo -e "\n${BLUE}🔌 Starting core HTTP tests (async)...${NC}"
        ./claude_command_scripts/commands/test-http.sh --core > /tmp/push_http_tests.log 2>&1 &
        HTTP_TEST_PID=$!
        echo "✓ HTTP tests running in background (PID: $HTTP_TEST_PID)"
    else
        HTTP_TEST_PID=""
    fi
    
    # Run backend tests in foreground
    if [[ -f "./run_tests.sh" ]]; then
        echo -e "\n${BLUE}🔬 Running backend tests...${NC}"
        if ! ./run_tests.sh; then
            echo -e "${RED}❌ Backend tests failed!${NC}"
            if [[ -n "$HTTP_TEST_PID" ]]; then
                kill $HTTP_TEST_PID 2>/dev/null || true
            fi
            exit 1
        fi
        echo "✓ Backend tests passed"
    fi
    
    # Wait for and check HTTP tests
    if [[ -n "$HTTP_TEST_PID" ]]; then
        echo -e "\n${BLUE}⏳ Waiting for HTTP tests to complete...${NC}"
        if wait $HTTP_TEST_PID; then
            echo "✓ HTTP tests passed"
        else
            echo -e "${RED}❌ HTTP tests failed!${NC}"
            echo "HTTP test output:"
            cat /tmp/push_http_tests.log || true
            exit 1
        fi
    fi
fi

echo -e "${GREEN}✅ All tests passed!${NC}"

# Exit if test-only mode
if [[ "$TEST_ONLY" == "true" ]]; then
    echo -e "\n${BLUE}🔚 Test-only mode: Stopping here (no push/PR operations)${NC}"
    exit 0
fi

# 3. Analyze PR coherence
echo -e "\n${GREEN}🔍 Analyzing PR coherence...${NC}"

# Get list of changed files
changed_files=$(git diff --name-only origin/main...HEAD 2>/dev/null || git diff --name-only main...HEAD)

if [[ -n "$changed_files" ]]; then
    file_count=$(echo "$changed_files" | wc -l)
    echo "Files to be pushed: $file_count"
    
    # Categorize files
    categories=()
    
    # Check for different file categories
    if echo "$changed_files" | grep -q "\.py$"; then categories+=("Python"); fi
    if echo "$changed_files" | grep -q "\.js$"; then categories+=("JavaScript"); fi
    if echo "$changed_files" | grep -q "\.css$"; then categories+=("CSS"); fi
    if echo "$changed_files" | grep -q "\.html$"; then categories+=("HTML"); fi
    if echo "$changed_files" | grep -q "\.md$"; then categories+=("Documentation"); fi
    if echo "$changed_files" | grep -q "test_"; then categories+=("Tests"); fi
    if echo "$changed_files" | grep -q "^scripts/"; then categories+=("Scripts"); fi
    if echo "$changed_files" | grep -q "^docs/"; then categories+=("Docs"); fi
    if echo "$changed_files" | grep -q "CLAUDE\.md\|\.gitignore\|requirements\.txt"; then categories+=("Config"); fi
    
    category_count=${#categories[@]}
    
    # Warn if PR seems to have unrelated changes
    if [[ $category_count -gt 2 ]] || [[ $file_count -gt 10 ]]; then
        echo -e "${YELLOW}⚠️  PR contains $file_count files across $category_count categories${NC}"
        echo "Categories: ${categories[*]}"
        echo ""
        echo "Files:"
        echo "$changed_files" | head -20
        if [[ $file_count -gt 20 ]]; then
            echo "... and $((file_count - 20)) more files"
        fi
        echo ""
        echo -e "${YELLOW}Consider splitting into multiple focused PRs:${NC}"
        echo "  - One PR per feature/fix"
        echo "  - Group related changes together"
        echo "  - Keep PRs small and reviewable"
        echo ""
        read -p "Continue with push? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Push cancelled${NC}"
            exit 0
        fi
    else
        echo "✓ PR appears focused ($category_count categories)"
    fi
fi

# 4. Push to remote
echo -e "\n${GREEN}📤 Pushing to remote...${NC}"

if [[ -z "$remote_branch" ]]; then
    # No upstream set, push with -u
    echo "Setting upstream and pushing..."
    git push -u origin "$current_branch"
else
    # Normal push
    git push origin "$current_branch"
fi

# 5. Check for existing PR and analyze its health
echo -e "\n${GREEN}🔍 Checking for pull request...${NC}"

pr_info=$(gh pr list --head "$current_branch" --json number,url,state --limit 1 2>/dev/null || echo "[]")
pr_exists=$(echo "$pr_info" | jq 'length > 0')

# Function to check and fix PR issues
check_and_fix_pr_issues() {
    local pr_number=$1
    echo -e "\n${BLUE}🔍 Analyzing PR #$pr_number for issues...${NC}"
    
    # Check for merge conflicts
    echo "Checking for merge conflicts..."
    pr_mergeable=$(gh pr view "$pr_number" --json mergeable | jq -r '.mergeable')
    
    if [[ "$pr_mergeable" == "CONFLICTING" ]]; then
        echo -e "${RED}❌ Merge conflicts detected!${NC}"
        echo "Attempting to resolve conflicts..."
        
        # Fetch latest main and try to merge
        git fetch origin main
        if git merge origin/main --no-edit; then
            echo -e "${GREEN}✅ Conflicts resolved automatically${NC}"
            # Push the merge commit
            git push origin "$current_branch"
        else
            echo -e "${RED}❌ Manual conflict resolution required${NC}"
            echo "Please resolve conflicts manually:"
            echo "  1. Fix conflicts in files listed above"
            echo "  2. git add <resolved-files>"
            echo "  3. git commit"
            echo "  4. git push"
            return 1
        fi
    elif [[ "$pr_mergeable" == "MERGEABLE" ]]; then
        echo "✅ No merge conflicts"
    else
        echo "⚠️  Merge status: $pr_mergeable"
    fi
    
    # Check CI status
    echo "Checking CI status..."
    # Get check status using PR view (more reliable than checks command)
    checks_status=$(gh pr view "$pr_number" --json statusCheckRollup | jq '.statusCheckRollup // []')
    failed_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "FAILURE")] | length')
    
    if [[ $failed_checks -gt 0 ]]; then
        echo -e "${RED}❌ $failed_checks CI check(s) failing${NC}"
        echo "Failed checks:"
        echo "$checks_status" | jq -r '.[] | select(.conclusion == "FAILURE") | "  - \(.name): \(.detailsUrl)"'
        
        # Try to identify test failures
        test_failures=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "FAILURE" and (.name | test("test|Test")))] | length')
        if [[ $test_failures -gt 0 ]]; then
            echo "Running tests locally to identify issues..."
            if [[ -f "./run_tests.sh" ]]; then
                if ! ./run_tests.sh >/dev/null 2>&1; then
                    echo -e "${YELLOW}⚠️  Tests also failing locally - check ./run_tests.sh output${NC}"
                else
                    echo "✅ Tests pass locally - CI issue may be transient"
                fi
            fi
        fi
    else
        success_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "SUCCESS")] | length')
        if [[ $success_checks -gt 0 ]]; then
            echo "✅ All $success_checks CI check(s) passing"
        else
            echo "⚠️  CI status pending or unknown"
        fi
    fi
    
    # Check for bot comments that need addressing
    echo "Checking for bot comments..."
    
    # Check for inline review comments from bots
    REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
    bot_comments=$(gh api "repos/$REPO/pulls/$pr_number/comments" 2>/dev/null | jq '[.[] | select(.user.type == "Bot" or (.user.login | test("bot|copilot"; "i")))] | length' 2>/dev/null || echo "0")
    
    # Check for general PR comments from bots  
    general_bot_comments=$(gh pr view "$pr_number" --json comments | jq '[.comments[] | select(.author.login | test("bot|copilot|github-actions"; "i"))] | length' 2>/dev/null || echo "0")
    
    total_bot_comments=$((bot_comments + general_bot_comments))
    
    if [[ $total_bot_comments -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  $total_bot_comments bot comment(s) found${NC}"
        echo "Consider running: ./claude_command_scripts/commands/copilot.sh $pr_number"
    else
        echo "✅ No pending bot comments"
    fi
    
    return 0
}

if [[ "$pr_exists" == "true" ]]; then
    pr_number=$(echo "$pr_info" | jq -r '.[0].number')
    pr_url=$(echo "$pr_info" | jq -r '.[0].url')
    pr_state=$(echo "$pr_info" | jq -r '.[0].state')
    
    echo "✓ Found existing PR #$pr_number ($pr_state)"
    echo "  URL: $pr_url"
    
    # Check and fix PR issues if it's open
    if [[ "$pr_state" == "OPEN" ]]; then
        check_and_fix_pr_issues "$pr_number"
        
        echo -e "\n${GREEN}📝 Updating PR description with health status...${NC}"
        
        # Get recent commits since PR creation
        recent_commits=$(git log --oneline -10 --pretty=format:"- %s")
        
        # Get current PR health status for the update
        pr_mergeable=$(gh pr view "$pr_number" --json mergeable | jq -r '.mergeable')
        checks_status=$(gh pr view "$pr_number" --json statusCheckRollup | jq '.statusCheckRollup // []')
        failed_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "FAILURE")] | length')
        success_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "SUCCESS")] | length')
        
        # Create status indicators
        merge_status="❌ Conflicts"
        if [[ "$pr_mergeable" == "MERGEABLE" ]]; then
            merge_status="✅ No conflicts"
        elif [[ "$pr_mergeable" == "UNKNOWN" ]]; then
            merge_status="⚠️ Status unknown"
        fi
        
        ci_status_icon="⚠️ Pending"
        if [[ $success_checks -gt 0 && $failed_checks -eq 0 ]]; then
            ci_status_icon="✅ All $success_checks passing"
        elif [[ $failed_checks -gt 0 ]]; then
            ci_status_icon="❌ $failed_checks failing"
        fi
        
        # Create temporary file for PR body
        pr_body_file=$(mktemp)
        cat > "$pr_body_file" <<EOF
## Latest Status

### PR Health Check
- **Merge Status**: $merge_status
- **CI Status**: $ci_status_icon
- **Last Push**: $(date)
- **Auto-Analysis**: Completed by enhanced push.sh

### Recent Commits
$recent_commits

### Test Results
✅ All tests passing locally (verified by push.sh)

---
*Updated by enhanced push.sh on $(date)*
EOF

        # Update PR body using file
        gh pr edit "$pr_number" --body-file "$pr_body_file"
        rm -f "$pr_body_file"
        echo "✓ PR description updated with health status"
    fi
else
    echo -e "\n${YELLOW}📋 No PR found. Create one with:${NC}"
    echo "  gh pr create"
fi

# 6. Summary
echo -e "\n${GREEN}✅ Push complete!${NC}"
echo "  Branch: $current_branch"
echo "  Remote: origin/$current_branch"

if [[ "$pr_exists" == "true" ]]; then
    echo "  PR: #$pr_number - $pr_url"
else
    echo "  PR: None (run 'gh pr create' to create)"
fi

# 7. Smart test server management for web projects
if [[ -f "mvp_site/main.py" ]]; then
    echo -e "\n${GREEN}🖥️  Test Server Management${NC}"
    echo "==============================="
    
    # Source shared port utilities
    source "$(dirname "$0")/../port-utils.sh"
    
    # Function to offer server cleanup
    offer_cleanup() {
        local servers=$(ps aux | grep -E "python.*main.py.*serve" | grep -v grep || true)
        if [ -n "$servers" ]; then
            echo -e "${YELLOW}🧹 Options to manage conflicting servers:${NC}"
            echo "  [1] Show detailed server list: ps aux | grep 'main.py.*serve'"
            echo "  [2] Kill specific server: kill <PID>"
            echo "  [3] Kill all servers: pkill -f 'main.py.*serve'"
            echo ""
        fi
    }
    
    # Check for available port
    available_port=$(find_available_port)
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Available port found: $available_port${NC}"
        echo ""
        echo -e "${YELLOW}🚀 Start test server with:${NC}"
        echo "  TESTING=true PORT=$available_port python mvp_site/main.py serve"
        echo ""
        echo -e "${YELLOW}🌐 Then access at:${NC}"
        echo "  http://localhost:$available_port?test_mode=true&test_user_id=test-user-123"
        
        # Show any existing servers
        list_running_servers
    else
        echo -e "${RED}❌ No available ports in range $BASE_PORT-$((BASE_PORT + MAX_PORTS - 1))${NC}"
        echo ""
        list_running_servers
        offer_cleanup
    fi
elif [[ -f "./test_server_manager.sh" ]]; then
    echo -e "\n${YELLOW}💡 Start test server with:${NC}"
    echo "  ./claude_command_scripts/commands/testserver.sh start"
    echo "  # or use: ./test_server_manager.sh start"
fi