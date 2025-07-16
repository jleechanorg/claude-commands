#!/bin/bash
# Configuration Management for Shell Scripts
# Centralized configuration and settings

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================

# Project-specific settings
readonly PROJECT_NAME="worldarchitect.ai"
readonly DEFAULT_BRANCH="main"
readonly TEST_SCRIPT="./run_tests.sh"
readonly UI_TEST_SCRIPT="./run_ui_tests.sh"

# Repository settings
readonly REPO_OWNER="jleechan2015"
readonly REPO_NAME="worldarchitect.ai"
readonly REPO_URL="https://github.com/$REPO_OWNER/$REPO_NAME"

# Directory paths
readonly EXPORT_DIR="export/cursor_commands_export"
readonly ROADMAP_DIR="roadmap"
readonly MVP_SITE_DIR="mvp_site"
readonly TESTING_DIR="testing_ui"

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Safe temporary directory
readonly SECURE_TMP_DIR="/tmp/worldarchitectai_secure"
readonly LOG_DIR="$SECURE_TMP_DIR/logs"
readonly PID_DIR="$SECURE_TMP_DIR/pids"

# Input validation limits
readonly MAX_BRANCH_NAME_LENGTH=50
readonly MAX_PR_TITLE_LENGTH=100
readonly MAX_PR_DESCRIPTION_LENGTH=2000
readonly MAX_FILE_PATH_LENGTH=500

# =============================================================================
# TESTING CONFIGURATION
# =============================================================================

# Test server settings
readonly BASE_PORT=6006
readonly TEST_MODE_URL="http://localhost:PORT?test_mode=true&test_user_id=test-user-123"

# Test types
readonly TEST_TYPES=("unit" "integration" "ui" "http")

# Test commands
readonly TEST_COMMANDS=(
    "unit:$TEST_SCRIPT"
    "integration:$TEST_SCRIPT --integration"
    "ui:$UI_TEST_SCRIPT mock"
    "http:$TEST_SCRIPT --http"
)

# =============================================================================
# GIT WORKFLOW CONFIGURATION
# =============================================================================

# Branch naming conventions
readonly BRANCH_PREFIXES=("feature/" "fix/" "update/" "hotfix/" "chore/")
readonly PROTECTED_BRANCHES=("main" "develop" "master")

# Commit message prefixes
readonly COMMIT_PREFIXES=("feat:" "fix:" "chore:" "docs:" "style:" "refactor:" "test:")

# PR template
readonly PR_TEMPLATE="## Summary
- Implementation of: TASK_DESCRIPTION
- Branch: BRANCH_NAME

## Changes
COMMIT_LIST

## Testing
- ✅ All tests passing (TIMESTAMP)
- Test command: \`$TEST_SCRIPT\`

## Files Changed
FILE_CHANGES

---
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# =============================================================================
# TOOL CONFIGURATION
# =============================================================================

# Required tools with minimum versions
readonly REQUIRED_TOOLS=(
    "git:2.20.0"
    "gh:2.0.0"
    "curl:7.0.0"
)

# Optional tools
readonly OPTIONAL_TOOLS=(
    "jq:1.6"
    "python3:3.8"
    "docker:20.0"
)

# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================

# Detect environment
detect_environment() {
    local env="unknown"
    
    # Check for common CI environments
    if [ -n "$CI" ]; then
        env="ci"
    elif [ -n "$GITHUB_ACTIONS" ]; then
        env="github_actions"
    elif [ -n "$CODESPACES" ]; then
        env="codespaces"
    elif [ -n "$CURSOR" ]; then
        env="cursor"
    elif [ -n "$CLAUDE_CODE" ]; then
        env="claude_code"
    else
        env="local"
    fi
    
    echo "$env"
}

# Get environment-specific settings
get_env_setting() {
    local setting="$1"
    local environment=$(detect_environment)
    
    case "$environment" in
        "ci"|"github_actions")
            case "$setting" in
                "interactive") echo "false" ;;
                "timeout") echo "300" ;;
                "verbose") echo "true" ;;
                *) echo "" ;;
            esac
            ;;
        "cursor"|"claude_code")
            case "$setting" in
                "interactive") echo "true" ;;
                "timeout") echo "60" ;;
                "verbose") echo "true" ;;
                *) echo "" ;;
            esac
            ;;
        "local")
            case "$setting" in
                "interactive") echo "true" ;;
                "timeout") echo "30" ;;
                "verbose") echo "false" ;;
                *) echo "" ;;
            esac
            ;;
        *)
            echo ""
            ;;
    esac
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Get project root directory
get_project_root() {
    git rev-parse --show-toplevel 2>/dev/null || echo "."
}

# Get current branch
get_current_branch() {
    git branch --show-current 2>/dev/null || echo "unknown"
}

# Get upstream branch
get_upstream_branch() {
    git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream"
}

# Get PR information
get_pr_info() {
    local branch="${1:-$(get_current_branch)}"
    gh pr list --head "$branch" --json number,url --jq '.[0] | "#\(.number) \(.url)"' 2>/dev/null || echo "none"
}

# Generate header information
generate_header() {
    local local_branch=$(get_current_branch)
    local remote_branch=$(get_upstream_branch)
    local pr_info=$(get_pr_info "$local_branch")
    
    echo "[Local: $local_branch | Remote: $remote_branch | PR: $pr_info]"
}

# =============================================================================
# PORT MANAGEMENT
# =============================================================================

# Calculate port for branch
calculate_port() {
    local branch_name="$1"
    local hash_value=$(echo "$branch_name" | cksum | cut -d' ' -f1)
    local port=$((BASE_PORT + hash_value % 100))
    echo "$port"
}

# Get available port
get_available_port() {
    local preferred_port="$1"
    local port="$preferred_port"
    
    # Check if port is available
    while netstat -tuln 2>/dev/null | grep -q ":$port "; do
        port=$((port + 1))
        if [ "$port" -gt 65535 ]; then
            echo "❌ No available ports found" >&2
            return 1
        fi
    done
    
    echo "$port"
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Validate configuration
validate_config() {
    local errors=()
    
    # Check required directories exist
    if [ ! -d "$(get_project_root)" ]; then
        errors+=("Project root directory not found")
    fi
    
    # Check test scripts exist
    if [ ! -f "$TEST_SCRIPT" ]; then
        errors+=("Test script not found: $TEST_SCRIPT")
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        errors+=("Not in a git repository")
    fi
    
    # Report errors
    if [ ${#errors[@]} -gt 0 ]; then
        echo "❌ Configuration validation failed:" >&2
        for error in "${errors[@]}"; do
            echo "  - $error" >&2
        done
        return 1
    fi
    
    return 0
}

# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize configuration
init_config() {
    local environment=$(detect_environment)
    
    # Create required directories
    mkdir -p "$SECURE_TMP_DIR" "$LOG_DIR" "$PID_DIR"
    chmod 700 "$SECURE_TMP_DIR" "$LOG_DIR" "$PID_DIR"
    
    # Validate configuration
    if ! validate_config; then
        echo "❌ Configuration initialization failed" >&2
        return 1
    fi
    
    # Set environment variables
    export WORLDARCHITECT_ENV="$environment"
    export WORLDARCHITECT_PROJECT_ROOT="$(get_project_root)"
    export WORLDARCHITECT_SECURE_TMP="$SECURE_TMP_DIR"
    
    echo "✅ Configuration initialized for environment: $environment"
    return 0
}

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

# Export configuration functions
export -f detect_environment get_env_setting get_project_root get_current_branch
export -f get_upstream_branch get_pr_info generate_header
export -f calculate_port get_available_port validate_config init_config