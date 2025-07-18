#!/bin/bash
# push.sh - Reliable push workflow with PR management
# Replaces unreliable /push command behavior
# Enhanced with modular architecture and configuration support

set -euo pipefail

# Configuration defaults
DEFAULT_CONFIG='{"checks":{"merge_conflicts":true,"ci_status":true,"bot_comments":true},"auto_fix":{"merge_conflicts":true,"run_local_tests":true},"github":{"api_timeout":30,"retry_attempts":3}}'
CONFIG_FILE="$HOME/.push-config.json"

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

# Logging functions
log() {
    local level=$1
    local message=$2
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >&2
}

log_info() { log "INFO" "$1"; }
log_warn() { log "WARN" "$1"; }
log_error() { log "ERROR" "$1"; }

# Configuration loader
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log_info "Loading configuration from $CONFIG_FILE"
        cat "$CONFIG_FILE"
    else
        log_info "Using default configuration"
        echo "$DEFAULT_CONFIG"
    fi
}

# Resilient GitHub API call with retry logic
call_github_api() {
    local endpoint=$1
    local config=$2
    local timeout
    local max_attempts
    timeout=$(echo "$config" | jq -r '.github.api_timeout // 30') || timeout=30
    max_attempts=$(echo "$config" | jq -r '.github.retry_attempts // 3') || max_attempts=3
    
    for ((i=1; i<=max_attempts; i++)); do
        if result=$(timeout "$timeout" gh api "$endpoint" 2>/dev/null); then
            echo "$result"
            return 0
        fi
        log_warn "GitHub API call failed (attempt $i/$max_attempts): $endpoint"
        if [[ $i -lt $max_attempts ]]; then
            sleep $((i * 2))  # Exponential backoff
        fi
    done
    log_error "GitHub API call failed after $max_attempts attempts: $endpoint"
    return 1
}

# Resilient GitHub CLI call with retry logic
call_github_cli() {
    local cmd=$1
    local config=$2
    local timeout
    local max_attempts
    timeout=$(echo "$config" | jq -r '.github.api_timeout // 30') || timeout=30
    max_attempts=$(echo "$config" | jq -r '.github.retry_attempts // 3') || max_attempts=3
    
    for ((i=1; i<=max_attempts; i++)); do
        if result=$(timeout "$timeout" gh $cmd 2>/dev/null); then
            echo "$result"
            return 0
        fi
        log_warn "GitHub CLI call failed (attempt $i/$max_attempts): gh $cmd"
        if [[ $i -lt $max_attempts ]]; then
            sleep $((i * 2))
        fi
    done
    log_error "GitHub CLI call failed after $max_attempts attempts: gh $cmd"
    return 1
}

# Configuration initialization
init_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo -e "${YELLOW}No configuration file found at $CONFIG_FILE${NC}"
        read -p "Create default configuration file? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "$DEFAULT_CONFIG" | jq '.' > "$CONFIG_FILE"
            echo -e "${GREEN}✅ Default configuration created at $CONFIG_FILE${NC}"
            echo "You can edit this file to customize push command behavior."
        fi
    fi
}

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
    echo "  --init-config   Create default configuration file"
    echo "  --show-config   Display current configuration"
    echo ""
    echo "Description:"
    echo "  This script provides a comprehensive push workflow that:"
    echo "  1. Runs pushlite for initial commit and push"
    echo "  2. Runs core HTTP tests (async) + backend tests if available"
    echo "  3. Validates CI environment compatibility with run_ci_replica"
    echo "  4. Pushes additional changes if any were made during testing"
    echo "  5. Updates or creates PR with comprehensive health analysis"
    echo "  6. Provides test server instructions"
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
        --init-config)
            init_config
            exit 0
            ;;
        --show-config)
            echo "Current configuration:"
            load_config | jq '.'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Load configuration
CONFIG=$(load_config)
log_info "Push workflow starting with configuration loaded"

echo -e "${BLUE}🚀 Push Workflow${NC}"
echo "=================="

# Run CI replica test first
echo -e "\n${BLUE}🔄 Running CI replica test to validate environment...${NC}"
if [ -f "./run_ci_replica.sh" ]; then
    if ./run_ci_replica.sh; then
        echo -e "${GREEN}✅ CI replica tests passed - environment is CI-compatible${NC}"
    else
        echo -e "${RED}❌ CI replica tests failed!${NC}"
        echo -e "${YELLOW}Fix CI issues before pushing to avoid breaking the build.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ CI replica script not found - skipping CI validation${NC}"
fi

# 1. Pre-push checks with pushlite integration
echo -e "\n${GREEN}🔍 Running enhanced pre-push workflow...${NC}"

# Skip pushlite in test-only mode
if [[ "$TEST_ONLY" != "true" ]]; then
    # Step 1: Run pushlite first to handle uncommitted changes and initial push
    echo -e "\n${BLUE}📤 Step 1: Running pushlite for initial commit and push...${NC}"
    if [[ -f "./claude_command_scripts/commands/pushlite.sh" ]]; then
        if ./claude_command_scripts/commands/pushlite.sh; then
            echo "✓ Pushlite completed successfully"
        else
            echo -e "${RED}❌ Pushlite failed! Aborting enhanced push workflow.${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️ Pushlite not found, falling back to manual change check${NC}"
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
    fi
else
    echo "⚠️  Skipping pushlite (test-only mode)"
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

# CI replica already run at the beginning, skip duplicate run

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

# 4. Check if additional push is needed (pushlite already pushed initially)
echo -e "\n${GREEN}📤 Step 3: Checking if additional push is needed...${NC}"

# Check if there are any commits that haven't been pushed since pushlite
if git log --oneline origin/"$current_branch"..HEAD | grep -q .; then
    echo "✓ New commits detected since initial pushlite push"
    echo -e "\n${BLUE}📤 Pushing additional changes to remote...${NC}"
    
    if [[ -z "$remote_branch" ]]; then
        # No upstream set, push with -u
        echo "Setting upstream and pushing..."
        git push -u origin "$current_branch"
    else
        # Normal push
        git push origin "$current_branch"
    fi
else
    echo "✓ No additional changes since pushlite - skipping redundant push"
fi

# 5. Check for existing PR and analyze its health
echo -e "\n${GREEN}🔍 Checking for pull request...${NC}"

pr_info=$(gh pr list --head "$current_branch" --json number,url,state --limit 1 2>/dev/null || echo "[]")
pr_exists=$(echo "$pr_info" | jq 'length > 0')

# Individual check functions (Phase 1: Extract functions)

# Check PR merge status
check_pr_merge_status() {
    local pr_number=$1
    local config=$2
    
    if [[ $(echo "$config" | jq -r '.checks.merge_conflicts') != "true" ]]; then
        log_info "Merge conflict checking disabled"
        return 0
    fi
    
    log_info "Checking merge conflicts for PR #$pr_number"
    
    local pr_data
    if ! pr_data=$(call_github_cli "pr view $pr_number --json mergeable" "$config"); then
        log_error "Failed to get PR merge status"
        return 1
    fi
    
    local pr_mergeable
    pr_mergeable=$(echo "$pr_data" | jq -r '.mergeable') || pr_mergeable="UNKNOWN"
    
    case "$pr_mergeable" in
        "CONFLICTING")
            echo -e "${RED}❌ Merge conflicts detected!${NC}"
            return 2  # Conflicts found
            ;;
        "MERGEABLE")
            echo "✅ No merge conflicts"
            return 0
            ;;
        *)
            echo "⚠️  Merge status: $pr_mergeable"
            return 0
            ;;
    esac
}

# Check PR CI status
check_pr_ci_status() {
    local pr_number=$1
    local config=$2
    
    if [[ $(echo "$config" | jq -r '.checks.ci_status') != "true" ]]; then
        log_info "CI status checking disabled"
        return 0
    fi
    
    log_info "Checking CI status for PR #$pr_number"
    
    local checks_data
    if ! checks_data=$(call_github_cli "pr view $pr_number --json statusCheckRollup" "$config"); then
        log_error "Failed to get CI status"
        return 1
    fi
    
    local checks_status
    local failed_checks
    local success_checks
    checks_status=$(echo "$checks_data" | jq '.statusCheckRollup') || checks_status="[]"
    failed_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "FAILURE")] | length') || failed_checks=0
    success_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "SUCCESS")] | length') || success_checks=0
    
    if [[ $failed_checks -gt 0 ]]; then
        echo -e "${RED}❌ $failed_checks CI check(s) failing${NC}"
        echo "Failed checks:"
        echo "$checks_status" | jq -r '.[] | select(.conclusion == "FAILURE") | "  - \(.name): \(.detailsUrl)"'
        return 3  # CI failures found
    elif [[ $success_checks -gt 0 ]]; then
        echo "✅ All $success_checks CI check(s) passing"
        return 0
    else
        echo "⚠️  CI status pending or unknown"
        return 0
    fi
}

# Check for bot comments
check_pr_bot_comments() {
    local pr_number=$1
    local config=$2
    
    if [[ $(echo "$config" | jq -r '.checks.bot_comments') != "true" ]]; then
        log_info "Bot comment checking disabled"
        return 0
    fi
    
    log_info "Checking bot comments for PR #$pr_number"
    
    # Check for inline review comments from bots
    local bot_comments=0
    if bot_result=$(call_github_api "repos/{owner}/{repo}/pulls/$pr_number/comments" "$config"); then
        bot_comments=$(echo "$bot_result" | jq '[.[] | select(.user.type == "Bot" or (.user.login | test("bot|copilot"; "i")))] | length' 2>/dev/null || echo "0")
    fi
    
    # Check for general PR comments from bots
    local general_bot_comments=0
    if general_result=$(call_github_cli "pr view $pr_number --json comments" "$config"); then
        general_bot_comments=$(echo "$general_result" | jq '[.comments[] | select(.author.login | test("bot|copilot|github-actions"; "i"))] | length' 2>/dev/null || echo "0")
    fi
    
    local total_bot_comments=$((bot_comments + general_bot_comments))
    
    if [[ $total_bot_comments -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  $total_bot_comments bot comment(s) found${NC}"
        echo "Consider running: ./claude_command_scripts/commands/copilot.sh $pr_number"
        return 4  # Bot comments found
    else
        echo "✅ No pending bot comments"
        return 0
    fi
}

# Attempt to fix PR issues with user confirmation
attempt_pr_fixes() {
    local pr_number=$1
    local issues_found=$2
    local config=$3
    local current_branch=$4
    
    log_info "Attempting to fix issues for PR #$pr_number (issues: $issues_found)"
    
    # Fix merge conflicts if found and auto-fix is enabled
    if [[ $issues_found -eq 2 && $(echo "$config" | jq -r '.auto_fix.merge_conflicts') == "true" ]]; then
        echo -e "${BLUE}🔧 Attempting to resolve merge conflicts...${NC}"
        
        # Phase 2: Add confirmation prompt for destructive operations
        echo -e "${YELLOW}⚠️  This will fetch and merge origin/main into your branch.${NC}"
        read -p "Continue with automatic conflict resolution? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "User declined automatic conflict resolution"
            return 0
        fi
        
        if git fetch origin main && git merge origin/main --no-edit; then
            echo -e "${GREEN}✅ Conflicts resolved automatically${NC}"
            
            # Confirm push
            echo -e "${YELLOW}⚠️  This will push the merge commit to your branch.${NC}"
            read -p "Push merge commit? [y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git push origin "$current_branch"
                log_info "Merge commit pushed successfully"
            else
                log_info "Merge commit not pushed (user choice)"
            fi
        else
            echo -e "${RED}❌ Manual conflict resolution required${NC}"
            echo "Please resolve conflicts manually:"
            echo "  1. Fix conflicts in files listed above"
            echo "  2. git add <resolved-files>"
            echo "  3. git commit"
            echo "  4. git push"
            return 1
        fi
    fi
    
    # Run local tests if CI failures and local testing is enabled
    if [[ $issues_found -eq 3 && $(echo "$config" | jq -r '.auto_fix.run_local_tests') == "true" ]]; then
        echo -e "${BLUE}🔧 Running local tests to diagnose CI failures...${NC}"
        if [[ -f "./run_tests.sh" ]]; then
            if ! ./run_tests.sh >/dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Tests also failing locally - check ./run_tests.sh output${NC}"
            else
                echo "✅ Tests pass locally - CI issue may be transient"
            fi
        else
            log_warn "No ./run_tests.sh found for local testing"
        fi
    fi
    
    return 0
}

# Main PR health check coordinator (refactored)
check_and_fix_pr_issues() {
    local pr_number=$1
    local config=$2
    local current_branch=$3
    
    echo -e "\n${BLUE}🔍 Analyzing PR #$pr_number for issues...${NC}"
    log_info "Starting comprehensive PR health check"
    
    local issues_found=0
    
    # Phase 2: Parallel execution of independent checks
    {
        check_pr_merge_status "$pr_number" "$config" &
        local merge_pid=$!
        
        check_pr_ci_status "$pr_number" "$config" &
        local ci_pid=$!
        
        check_pr_bot_comments "$pr_number" "$config" &
        local bot_pid=$!
        
        # Wait for all checks to complete
        wait $merge_pid; local merge_result=$?
        wait $ci_pid; local ci_result=$?
        wait $bot_pid; local bot_result=$?
        
        # Determine which issues were found
        if [[ $merge_result -eq 2 ]]; then issues_found=2; fi
        if [[ $ci_result -eq 3 ]]; then issues_found=3; fi
        if [[ $bot_result -eq 4 ]]; then issues_found=4; fi
    }
    
    # Attempt fixes if issues were found
    if [[ $issues_found -gt 0 ]]; then
        attempt_pr_fixes "$pr_number" "$issues_found" "$config" "$current_branch"
    else
        echo -e "${GREEN}✅ PR is healthy - no issues found${NC}"
        log_info "PR health check completed successfully"
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
        check_and_fix_pr_issues "$pr_number" "$CONFIG" "$current_branch"
        
        echo -e "\n${GREEN}📝 Updating PR description with health status...${NC}"
        
        # Get recent commits since PR creation
        recent_commits=$(git log --oneline -10 --pretty=format:"- %s")
        
        # Get current PR health status for the update using resilient API calls
        # Remove 'local' keyword - we're in the main script body
        if pr_data=$(call_github_cli "pr view $pr_number --json mergeable" "$CONFIG"); then
            pr_mergeable=$(echo "$pr_data" | jq -r '.mergeable')
        else
            pr_mergeable="UNKNOWN"
        fi
        
        if ci_data=$(call_github_cli "pr view $pr_number --json statusCheckRollup" "$CONFIG"); then
            checks_status=$(echo "$ci_data" | jq '.statusCheckRollup')
            failed_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "FAILURE")] | length')
            success_checks=$(echo "$checks_status" | jq '[.[] | select(.conclusion == "SUCCESS")] | length')
        else
            checks_status="[]"
            failed_checks=0
            success_checks=0
        fi
        
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