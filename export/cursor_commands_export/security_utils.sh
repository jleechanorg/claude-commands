#!/bin/bash
# Security Utilities for Shell Scripts
# Centralized security functions for input validation and safe command execution

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Safe path for temporary files
readonly SAFE_TMP_DIR="/tmp/worldarchitectai_secure"
readonly MAX_BRANCH_NAME_LENGTH=50
readonly MAX_PR_TITLE_LENGTH=100
readonly MAX_PR_DESCRIPTION_LENGTH=2000

# Ensure safe temp directory exists with proper permissions
create_safe_temp_dir() {
    if [ ! -d "$SAFE_TMP_DIR" ]; then
        mkdir -p "$SAFE_TMP_DIR"
        chmod 700 "$SAFE_TMP_DIR"
    fi
}

# =============================================================================
# INPUT VALIDATION FUNCTIONS
# =============================================================================

# Validate branch name - only allow alphanumeric, hyphens, underscores, forward slashes
validate_branch_name() {
    local branch_name="$1"
    
    if [ -z "$branch_name" ]; then
        return 1
    fi
    
    if [ ${#branch_name} -gt $MAX_BRANCH_NAME_LENGTH ]; then
        echo "❌ Branch name too long (max $MAX_BRANCH_NAME_LENGTH characters)" >&2
        return 1
    fi
    
    if [[ ! "$branch_name" =~ ^[a-zA-Z0-9/_-]+$ ]]; then
        echo "❌ Invalid branch name. Only alphanumeric, hyphens, underscores, and forward slashes allowed." >&2
        return 1
    fi
    
    # Prevent path traversal
    if [[ "$branch_name" =~ \.\. ]]; then
        echo "❌ Branch name cannot contain '..' sequences" >&2
        return 1
    fi
    
    return 0
}

# Validate PR title
validate_pr_title() {
    local title="$1"
    
    if [ -z "$title" ]; then
        echo "❌ PR title cannot be empty" >&2
        return 1
    fi
    
    if [ ${#title} -gt $MAX_PR_TITLE_LENGTH ]; then
        echo "❌ PR title too long (max $MAX_PR_TITLE_LENGTH characters)" >&2
        return 1
    fi
    
    # Remove potentially dangerous characters
    if [[ "$title" =~ [\$\`\!] ]]; then
        echo "❌ PR title contains dangerous characters (\$, \`, !)" >&2
        return 1
    fi
    
    return 0
}

# Validate PR description
validate_pr_description() {
    local description="$1"
    
    if [ ${#description} -gt $MAX_PR_DESCRIPTION_LENGTH ]; then
        echo "❌ PR description too long (max $MAX_PR_DESCRIPTION_LENGTH characters)" >&2
        return 1
    fi
    
    # Remove potentially dangerous characters
    if [[ "$description" =~ [\$\`\!] ]]; then
        echo "❌ PR description contains dangerous characters (\$, \`, !)" >&2
        return 1
    fi
    
    return 0
}

# Validate file path - prevent path traversal
validate_file_path() {
    local file_path="$1"
    
    if [ -z "$file_path" ]; then
        return 1
    fi
    
    # Convert to absolute path
    local abs_path
    abs_path=$(realpath "$file_path" 2>/dev/null) || return 1
    
    # Ensure it's within the project directory
    local project_root
    project_root=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
    
    if [[ ! "$abs_path" == "$project_root"* ]]; then
        echo "❌ File path outside project directory: $file_path" >&2
        return 1
    fi
    
    return 0
}

# Validate PID for process operations
validate_pid() {
    local pid="$1"
    
    if [[ ! "$pid" =~ ^[0-9]+$ ]]; then
        echo "❌ Invalid PID format: $pid" >&2
        return 1
    fi
    
    if [ "$pid" -le 0 ] || [ "$pid" -gt 65535 ]; then
        echo "❌ PID out of valid range: $pid" >&2
        return 1
    fi
    
    return 0
}

# =============================================================================
# SECURE COMMAND EXECUTION
# =============================================================================

# Execute git command with proper escaping
secure_git_command() {
    local -a cmd_args=("$@")
    
    # Ensure we're in a git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "❌ Not in a git repository" >&2
        return 1
    fi
    
    # Execute git command with proper argument handling
    git "${cmd_args[@]}"
}

# Execute gh command with proper escaping
secure_gh_command() {
    local -a cmd_args=("$@")
    
    # Check if gh is available
    if ! command -v gh >/dev/null 2>&1; then
        echo "❌ GitHub CLI (gh) not found" >&2
        return 1
    fi
    
    # Execute gh command with proper argument handling
    gh "${cmd_args[@]}"
}

# Safe file operations with path validation
safe_file_operation() {
    local operation="$1"
    local file_path="$2"
    
    validate_file_path "$file_path" || return 1
    
    case "$operation" in
        "read")
            if [ -f "$file_path" ]; then
                cat "$file_path"
            else
                echo "❌ File not found: $file_path" >&2
                return 1
            fi
            ;;
        "write")
            local content="$3"
            echo "$content" > "$file_path"
            ;;
        "delete")
            if [ -f "$file_path" ]; then
                rm -f "$file_path"
            fi
            ;;
        *)
            echo "❌ Unknown file operation: $operation" >&2
            return 1
            ;;
    esac
}

# =============================================================================
# DEPENDENCY CHECKING
# =============================================================================

# Check for required commands
check_dependencies() {
    local -a required_commands=("git" "gh")
    local -a missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        echo "❌ Missing required commands: ${missing_commands[*]}" >&2
        echo "Please install the missing dependencies before continuing." >&2
        return 1
    fi
    
    return 0
}

# Check if we're in a valid git repository
check_git_repo() {
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "❌ Not in a git repository" >&2
        echo "Please run this script from within a git repository." >&2
        return 1
    fi
    
    return 0
}

# =============================================================================
# LOGGING AND ERROR HANDLING
# =============================================================================

# Centralized logging function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local script_name=$(basename "$0")
    
    case "$level" in
        "INFO")
            echo "[$timestamp] [$script_name] INFO: $message"
            ;;
        "WARN")
            echo "[$timestamp] [$script_name] WARN: $message" >&2
            ;;
        "ERROR")
            echo "[$timestamp] [$script_name] ERROR: $message" >&2
            ;;
        *)
            echo "[$timestamp] [$script_name] $level: $message"
            ;;
    esac
}

# Error handling with cleanup
handle_error() {
    local error_message="$1"
    local exit_code="${2:-1}"
    
    log_message "ERROR" "$error_message"
    
    # Cleanup any temporary files
    cleanup_temp_files
    
    exit "$exit_code"
}

# Cleanup temporary files
cleanup_temp_files() {
    if [ -d "$SAFE_TMP_DIR" ]; then
        find "$SAFE_TMP_DIR" -name "*.tmp" -type f -delete 2>/dev/null
    fi
}

# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize security utilities
init_security_utils() {
    create_safe_temp_dir
    check_dependencies || return 1
    check_git_repo || return 1
    
    # Set up cleanup trap
    trap cleanup_temp_files EXIT
    
    log_message "INFO" "Security utilities initialized"
}

# =============================================================================
# SAFE PATH UTILITIES
# =============================================================================

# Get safe log file path
get_safe_log_path() {
    local branch_name="$1"
    
    validate_branch_name "$branch_name" || return 1
    
    # Create safe log directory
    local log_dir="$SAFE_TMP_DIR/logs"
    mkdir -p "$log_dir"
    chmod 700 "$log_dir"
    
    # Create safe log file name by replacing special characters
    local safe_branch_name=$(echo "$branch_name" | tr '/' '_' | tr -cd 'a-zA-Z0-9_-')
    
    echo "$log_dir/${safe_branch_name}.log"
}

# Get safe PID file path
get_safe_pid_path() {
    local branch_name="$1"
    
    validate_branch_name "$branch_name" || return 1
    
    # Create safe PID directory
    local pid_dir="$SAFE_TMP_DIR/pids"
    mkdir -p "$pid_dir"
    chmod 700 "$pid_dir"
    
    # Create safe PID file name by replacing special characters
    local safe_branch_name=$(echo "$branch_name" | tr '/' '_' | tr -cd 'a-zA-Z0-9_-')
    
    echo "$pid_dir/${safe_branch_name}.pid"
}

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

# Export all functions for use in other scripts
export -f validate_branch_name validate_pr_title validate_pr_description validate_file_path validate_pid
export -f secure_git_command secure_gh_command safe_file_operation
export -f check_dependencies check_git_repo
export -f log_message handle_error cleanup_temp_files
export -f init_security_utils get_safe_log_path get_safe_pid_path