#!/bin/bash
# pushlite.sh - Enhanced reliable push command with selective staging and uncommitted change verification
# Enhanced version focusing on push reliability and clean state verification
# Primary implementation - pushl.sh is an alias that calls this script

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Global variables for enhanced functionality
VERBOSE=false
DRY_RUN=false
INCLUDE_PATTERNS=()
EXCLUDE_PATTERNS=()
ERROR_LOG="/tmp/pushl_error_$(date +%s).log"
RESULT_JSON="/tmp/pushl_result_$(date +%s).json"

# Enhanced help function
show_help() {
    echo "pushlite - Enhanced reliable push command with selective staging"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Basic Options:"
    echo "  pr                    Push and create PR to main"
    echo "  force                 Force push to origin (use with caution)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Enhanced Options:"
    echo "  -v, --verbose         Enable verbose output for debugging"
    echo "  --dry-run             Preview operations without executing"
    echo "  --include PATTERN     Include files matching pattern"
    echo "  --exclude PATTERN     Exclude files matching pattern"
    echo "  -m, --message MSG     Commit message"
    echo ""
    echo "Description:"
    echo "  Enhanced push command with reliability improvements:"
    echo "  1. Comprehensive error handling and reporting"
    echo "  2. Selective staging with include/exclude patterns"
    echo "  3. Automatic lint fixes for staged files only"
    echo "  4. Post-push verification of uncommitted changes"
    echo "  5. Interactive handling of unclean repository state"
    echo "  6. Verbose mode for debugging complex scenarios"
    echo "  7. Dry-run mode to preview operations"
    echo "  8. Always creates result JSON for automation"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Simple push"
    echo "  $0 pr                                 # Push and create PR"
    echo "  $0 --verbose --dry-run                # Debug mode preview"
    echo "  $0 --include '*.py' --exclude test_*  # Selective staging"
    echo "  $0 -m 'fix: resolve conflicts' force # Force push with message"
    echo ""
    echo "Aliases: /pushlite, /pushl"
    exit 0
}

# Enhanced argument parsing
CREATE_PR=false
FORCE_PUSH=false
AUTOMATION_MODE=false
COMMIT_MESSAGE=""

# Check for environment automation mode
if [[ -n "${COPILOT_WORKFLOW:-}" ]] || [[ -n "${CI:-}" ]] || [[ ! -t 0 ]]; then
    AUTOMATION_MODE=true
fi

# Parse arguments with enhanced options
while [[ $# -gt 0 ]]; do
    case "$1" in
        pr)
            CREATE_PR=true
            shift
            ;;
        force)
            FORCE_PUSH=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            VERBOSE=true  # Enable verbose for dry runs
            shift
            ;;
        --include)
            if [[ -n "${2:-}" ]]; then
                INCLUDE_PATTERNS+=("$2")
                shift 2
            else
                echo "Error: --include requires a pattern"
                exit 1
            fi
            ;;
        --exclude)
            if [[ -n "${2:-}" ]]; then
                EXCLUDE_PATTERNS+=("$2")
                shift 2
            else
                echo "Error: --exclude requires a pattern"
                exit 1
            fi
            ;;
        -m|--message)
            if [[ -n "${2:-}" ]]; then
                COMMIT_MESSAGE="$2"
                shift 2
            else
                echo "Error: --message requires a commit message"
                exit 1
            fi
            ;;
        --automation)
            AUTOMATION_MODE=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Enhanced status output
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${CYAN}🔍 pushlite (DRY RUN)${NC}"
    echo "==================="
else
    echo -e "${CYAN}🚀 pushlite Enhanced${NC}"
    echo "==================="
fi

if [[ "$VERBOSE" == "true" ]]; then
    echo -e "${BLUE}Mode:${NC} Verbose enabled"
    echo -e "${BLUE}Dry run:${NC} $DRY_RUN"
    echo -e "${BLUE}Include patterns:${NC} ${INCLUDE_PATTERNS[*]:-none}"
    echo -e "${BLUE}Exclude patterns:${NC} ${EXCLUDE_PATTERNS[*]:-none}"
    echo -e "${BLUE}Error log:${NC} $ERROR_LOG"
fi

# Enhanced pre-flight checks with verbose output
log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[VERBOSE]${NC} $1"
    fi
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$ERROR_LOG"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Result JSON creation functions
create_success_result() {
    local message="$1"
    local commit_sha="${2:-}"
    local branch="${3:-$current_branch}"

    cat > "$RESULT_JSON" << EOF
{
  "pushed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "branch": "$branch",
  "remote": "origin",
  "commit_sha": "$commit_sha",
  "message": "$message",
  "success": true,
  "verbose": $VERBOSE,
  "dry_run": $DRY_RUN
}
EOF
    log_verbose "Success result written to $RESULT_JSON"
}

create_error_result() {
    local error_message="$1"
    local branch="${2:-$current_branch}"

    cat > "$RESULT_JSON" << EOF
{
  "pushed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "branch": "$branch",
  "remote": "origin",
  "commit_sha": null,
  "message": "$error_message",
  "success": false,
  "verbose": $VERBOSE,
  "dry_run": $DRY_RUN,
  "error_log": "$ERROR_LOG"
}
EOF
    log_verbose "Error result written to $RESULT_JSON"
    echo "Result JSON available at: $RESULT_JSON"
}

# File filtering function for selective staging
apply_file_filters() {
    local status="$1"
    local filtered_status="$status"

    # Apply include patterns (using glob matching)
    if [[ ${#INCLUDE_PATTERNS[@]} -gt 0 ]]; then
        local included=""
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            # Git status --porcelain format: "XY filename" where X and Y are status codes
            # Extract filename starting from position 3 (after "XY ")
            local file_path="${line:3}"
            
            # Handle renamed files (format: "R  old -> new")
            if [[ "${line:0:1}" == "R" ]]; then
                # Extract the new filename after " -> "
                file_path="${file_path#* -> }"
            fi
            
            for pattern in "${INCLUDE_PATTERNS[@]}"; do
                # Use bash glob matching
                if [[ "$file_path" == $pattern ]] || [[ "$(basename "$file_path")" == $pattern ]]; then
                    log_verbose "File '$file_path' matches include pattern: $pattern"
                    included="$included$line"$'\n'
                    break
                fi
            done
        done <<< "$status"
        filtered_status="$included"
    fi

    # Apply exclude patterns (using glob matching)
    if [[ ${#EXCLUDE_PATTERNS[@]} -gt 0 ]]; then
        local excluded=""
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            # Git status --porcelain format: "XY filename" where X and Y are status codes
            # Extract filename starting from position 3 (after "XY ")
            local file_path="${line:3}"
            
            # Handle renamed files (format: "R  old -> new")
            if [[ "${line:0:1}" == "R" ]]; then
                # Extract the new filename after " -> "
                file_path="${file_path#* -> }"
            fi
            
            local should_exclude=false
            for pattern in "${EXCLUDE_PATTERNS[@]}"; do
                # Use bash glob matching
                if [[ "$file_path" == $pattern ]] || [[ "$(basename "$file_path")" == $pattern ]]; then
                    log_verbose "File '$file_path' matches exclude pattern: $pattern"
                    should_exclude=true
                    break
                fi
            done
            
            if [[ "$should_exclude" == false ]]; then
                excluded="$excluded$line"$'\n'
            fi
        done <<< "$filtered_status"
        filtered_status="$excluded"
    fi

    echo "$filtered_status"
}

# Safe execution wrapper for dry runs (eval-based for backward compatibility)
safe_execute() {
    local command="$1"
    local description="$2"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would execute: $command"
        log_verbose "Dry run - skipping: $description"
        return 0
    else
        log_verbose "Executing: $command"
        if eval "$command" 2>>"$ERROR_LOG"; then
            log_verbose "Success: $description"
            return 0
        else
            log_error "Failed: $description"
            log_error "Command: $command"
            return 1
        fi
    fi
}

# Safe execution wrapper without eval (preferred for security)
safe_exec() {
    local description="$1"
    shift  # Remove description from arguments
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would execute: $*"
        log_verbose "Dry run - skipping: $description"
        return 0
    else
        log_verbose "Executing: $description"
        if "$@" 2>>"$ERROR_LOG"; then
            log_verbose "Success: $description"
            return 0
        else
            log_error "Failed: $description"
            log_error "Command: $*"
            return 1
        fi
    fi
}

# Validate git availability
log_verbose "Checking git availability..."
if ! command -v git &> /dev/null; then
    log_error "Git is not installed"
    create_error_result "Git not found"
    exit 1
fi
log_verbose "Git found: $(git --version)"

# Enhanced dependency checks
if [[ "$CREATE_PR" == "true" ]]; then
    log_verbose "Checking GitHub CLI availability..."
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is required for PR creation"
        create_error_result "GitHub CLI not found"
        exit 1
    fi
    log_verbose "GitHub CLI found: $(gh --version | head -1)"

    log_verbose "Checking jq availability..."
    if ! command -v jq &> /dev/null; then
        log_error "jq is required for PR creation (JSON parsing)"
        echo "Install with: sudo apt-get install jq (Ubuntu/Debian) or brew install jq (macOS)"
        create_error_result "jq not found"
        exit 1
    fi
    log_verbose "jq found: $(jq --version)"
fi

# Enhanced git state validation
log_verbose "Validating git repository state..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "Not in a git repository"
    create_error_result "Not in git repository"
    exit 1
fi

# Check for problematic repository states
if [[ -f ".git/MERGE_HEAD" ]]; then
    log_error "Repository is in merge state - resolve conflicts first"
    create_error_result "Repository in merge state"
    exit 1
fi

if [[ -f ".git/rebase-merge" ]] || [[ -f ".git/rebase-apply" ]]; then
    log_error "Repository is in rebase state - complete rebase first"
    create_error_result "Repository in rebase state"
    exit 1
fi

# Get current branch with validation
current_branch=$(git branch --show-current)
if [[ -z "$current_branch" ]]; then
    log_error "Not on any branch (detached HEAD?)"
    create_error_result "Detached HEAD state"
    exit 1
fi

log_info "Branch: $current_branch"
log_verbose "Repository root: $(git rev-parse --show-toplevel)"

# Enhanced repository status analysis
log_info "Repository Status"
log_verbose "Running git status analysis..."

# Capture git status with error handling
if ! git_status=$(git status --porcelain 2>"$ERROR_LOG"); then
    log_error "Failed to get git status"
    create_error_result "Git status failed"
    exit 1
fi

# Apply selective filtering if patterns are specified
filtered_status="$git_status"
if [[ ${#INCLUDE_PATTERNS[@]} -gt 0 ]] || [[ ${#EXCLUDE_PATTERNS[@]} -gt 0 ]]; then
    log_verbose "Applying file filtering patterns..."
    filtered_status=$(apply_file_filters "$git_status")
fi

# Parse status with enhanced categorization
# Extract untracked files (status code "??")
untracked_files=""
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    if [[ "${line:0:2}" == "??" ]]; then
        # Extract filename starting from position 3
        untracked_files="${untracked_files}${line:3}"$'\n'
    fi
done <<< "$filtered_status"

# Extract staged files (first char is not space)
staged_files=""
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    if [[ "${line:0:1}" =~ [MARCDT] ]]; then
        file_path="${line:3}"
        # Handle renamed files
        if [[ "${line:0:1}" == "R" ]]; then
            file_path="${file_path#* -> }"
        fi
        staged_files="${staged_files}${file_path}"$'\n'
    fi
done <<< "$filtered_status"

# Extract modified files (second char is not space)
modified_files=""
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    if [[ "${line:1:1}" =~ [MARCDT] ]]; then
        file_path="${line:3}"
        # Handle renamed files
        if [[ "${line:0:1}" == "R" ]]; then
            file_path="${file_path#* -> }"
        fi
        modified_files="${modified_files}${file_path}"$'\n'
    fi
done <<< "$filtered_status"

# Extract conflicted files (all conflict states)
conflicted_files=""
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    # Include all conflict states: UU, AA, DD, UA, AU, UD, DU
    if [[ "${line:0:2}" =~ ^(UU|AA|DD|UA|AU|UD|DU)$ ]]; then
        conflicted_files="${conflicted_files}${line:3}"$'\n'
    fi
done <<< "$git_status"

# Enhanced file counting with conflict detection
untracked_count=$(echo "$untracked_files" | sed '/^$/d' | wc -l)
staged_count=$(echo "$staged_files" | sed '/^$/d' | wc -l)
modified_count=$(echo "$modified_files" | sed '/^$/d' | wc -l)
conflicted_count=$(echo "$conflicted_files" | sed '/^$/d' | wc -l)

# Check for merge conflicts
if [[ $conflicted_count -gt 0 ]]; then
    log_error "Repository has $conflicted_count conflicted files"
    echo "$conflicted_files" | head -10
    create_error_result "Merge conflicts detected"
    exit 1
fi

# Enhanced status display
echo "  Staged files: $staged_count"
echo "  Modified files: $modified_count"
echo "  Untracked files: $untracked_count"

if [[ "$VERBOSE" == "true" ]]; then
    if [[ $staged_count -gt 0 ]]; then
        echo -e "\n${CYAN}Staged files:${NC}"
        echo "$staged_files" | head -10 | sed 's/^/  - /'
        [[ $(echo "$staged_files" | wc -l) -gt 10 ]] && echo "  ... and $(($(echo "$staged_files" | wc -l) - 10)) more"
    fi

    if [[ $modified_count -gt 0 ]]; then
        echo -e "\n${CYAN}Modified files:${NC}"
        echo "$modified_files" | head -10 | sed 's/^/  - /'
        [[ $(echo "$modified_files" | wc -l) -gt 10 ]] && echo "  ... and $(($(echo "$modified_files" | wc -l) - 10)) more"
    fi

    if [[ $untracked_count -gt 0 ]]; then
        echo -e "\n${CYAN}Untracked files:${NC}"
        echo "$untracked_files" | head -10 | sed 's/^/  - /'
        [[ $(echo "$untracked_files" | wc -l) -gt 10 ]] && echo "  ... and $(($(echo "$untracked_files" | wc -l) - 10)) more"
    fi
fi

# Apply conditional lint fixes to staged files only
apply_conditional_lint_fixes() {
    # Skip if linting is disabled or script not found
    if [[ "${SKIP_LINT:-false}" == "true" ]] || [[ ! -f "./run_lint.sh" ]] || [[ ! -x "./run_lint.sh" ]]; then
        if [[ "${SKIP_LINT:-false}" == "true" ]]; then
            log_verbose "Skipping conditional lint fixes (SKIP_LINT=true)"
        else
            log_verbose "Lint script not found or not executable, skipping conditional fixes"
        fi
        return 0
    fi

    # Get list of staged files
    local staged_files
    if ! staged_files=$(git diff --cached --name-only 2>"$ERROR_LOG"); then
        log_verbose "Could not get staged files list, skipping lint fixes"
        return 0
    fi

    # Filter for Python files that are staged
    local python_files
    python_files=$(echo "$staged_files" | grep -E '\.(py)$' || true)

    if [[ -z "$python_files" ]]; then
        log_verbose "No Python files staged, skipping lint fixes"
        return 0
    fi

    local python_count=$(echo "$python_files" | sed '/^$/d' | wc -l)
    log_info "Applying lint fixes to $python_count staged Python files"

    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}Staged Python files for lint fixes:${NC}"
        echo "$python_files" | sed 's/^/  - /'
    fi

    # Apply lint fixes only to staged Python files
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would run: ./run_lint.sh fix (on staged files only)"
    else
        # Get list of staged Python files for targeted linting
        local staged_py_files
        staged_py_files=$(git diff --cached --name-only --diff-filter=d | grep '\.py$' || true)
        
        if [[ -n "$staged_py_files" ]]; then
            # Run lint fixes only on the staged files
            if echo "$staged_py_files" | xargs ./run_lint.sh fix 2>>"$ERROR_LOG"; then
                log_verbose "Lint fixes applied successfully"

                # Re-stage any files that were modified by lint fixes
                local modified_by_lint
                if modified_by_lint=$(git diff --name-only 2>/dev/null); then
                    local restage_files=""
                    # Check each Python file to see if it was modified by lint fixes
                    while IFS= read -r python_file; do
                        if echo "$modified_by_lint" | grep -Fxq "$python_file"; then
                            restage_files="${restage_files}${python_file}"$'\n'
                        fi
                    done <<< "$staged_py_files"

                    if [[ -n "$restage_files" ]]; then
                        log_info "Re-staging $(echo "$restage_files" | wc -l) files modified by lint fixes"
                        if [[ "$VERBOSE" == "true" ]]; then
                            echo -e "${CYAN}Re-staging files:${NC}"
                            echo "$restage_files" | sed 's/^/  - /'
                        fi

                        while IFS= read -r file; do
                            [[ -n "$file" ]] && safe_exec "Re-stage lint-fixed file: $file" git add -- "$file"
                        done <<< "$restage_files"
                    fi
                fi
            else
                log_warning "Lint fixes encountered issues (non-fatal)"
                log_verbose "Check $ERROR_LOG for lint fix details"
            fi
        fi
    fi
}

# Enhanced file handling with selective staging
handle_files() {
    local file_type="$1"
    local files="$2"
    local count="$3"

    if [[ $count -eq 0 ]]; then
        log_verbose "No $file_type files to handle"
        return 0
    fi

    log_info "Handling $count $file_type files"

    # In automation mode or with patterns, handle automatically
    if [[ "$AUTOMATION_MODE" == "true" ]] || [[ ${#INCLUDE_PATTERNS[@]} -gt 0 ]] || [[ ${#EXCLUDE_PATTERNS[@]} -gt 0 ]]; then
        local commit_msg="Add $file_type files"
        if [[ -n "$COMMIT_MESSAGE" ]]; then
            commit_msg="$COMMIT_MESSAGE"
        fi

        log_info "Auto-staging $file_type files (automation mode or patterns specified)"

        if [[ "$file_type" == "untracked" ]]; then
            # Stage specific untracked files if filtered, otherwise all
            if [[ ${#INCLUDE_PATTERNS[@]} -gt 0 ]] || [[ ${#EXCLUDE_PATTERNS[@]} -gt 0 ]]; then
                while IFS= read -r file; do
                    [[ -n "$file" ]] && safe_exec "Stage filtered file: $file" git add -- "$file"
                done <<< "$files"
            else
                safe_exec "Stage all untracked files" git add .
            fi
        else
            # Stage specific modified files if filtered, otherwise all
            if [[ ${#INCLUDE_PATTERNS[@]} -gt 0 ]] || [[ ${#EXCLUDE_PATTERNS[@]} -gt 0 ]]; then
                while IFS= read -r file; do
                    [[ -n "$file" ]] && safe_exec "Stage filtered modified file: $file" git add -- "$file"
                done <<< "$files"
            else
                safe_exec "Stage all modified files (including deletions)" git add -A
            fi
        fi

        # Apply lint fixes to staged files before committing
        apply_conditional_lint_fixes

        safe_execute "git commit -m '$commit_msg'" "Commit $file_type files"
        return $?
    fi

    # Interactive mode for complex scenarios
    echo -e "\n${YELLOW}📁 $count $file_type Files Found:${NC}"
    echo "$files" | head -20 | sed 's/^/  - /'
    if [[ $count -gt 20 ]]; then
        echo "  ... and $((count - 20)) more files"
    fi

    echo -e "\n${YELLOW}Options:${NC}"
    echo "  [1] Add all $file_type files and commit"
    echo "  [2] Select specific files to add"
    echo "  [3] Continue without adding (push existing commits only)"
    echo "  [4] Cancel push operation"
    echo ""

    while true; do
        read -p "Choose option [1-4]: " -n 1 -r choice
        echo

        case "$choice" in
            1)
                local commit_msg="Add $file_type files"
                if [[ -n "$COMMIT_MESSAGE" ]]; then
                    commit_msg="$COMMIT_MESSAGE"
                fi

                log_info "Adding all $file_type files..."
                safe_exec "Stage all $file_type files" git add -A

                # Apply lint fixes to staged files before committing
                apply_conditional_lint_fixes

                safe_execute "git commit -m '$commit_msg'" "Commit $file_type files"
                return $?
                ;;
            2)
                echo -e "${BLUE}📝 Select files to add:${NC}"
                echo "$files" | nl -w2 -s') '
                echo ""
                read -p "Enter file numbers (space-separated, e.g., 1 3 5): " file_numbers

                local selected_files=()
                for num in $file_numbers; do
                    if [[ "$num" =~ ^[0-9]+$ ]] && [[ $num -le $count ]]; then
                        file=$(echo "$files" | sed -n "${num}p")
                        selected_files+=("$file")
                    fi
                done

                if [[ ${#selected_files[@]} -gt 0 ]]; then
                    log_info "Adding selected files:"
                    for file in "${selected_files[@]}"; do
                        echo "  + $file"
                        safe_exec "Stage selected file: $file" git add -- "$file"
                    done

                    local commit_msg="${COMMIT_MESSAGE:-Add selected $file_type files}"
                    # Apply lint fixes to staged files before committing
                    apply_conditional_lint_fixes

                    safe_execute "git commit -m '$commit_msg'" "Commit selected files"
                    return $?
                else
                    log_warning "No valid files selected"
                fi
                return 0
                ;;
            3)
                log_info "Continuing without adding $file_type files"
                return 0
                ;;
            4)
                log_error "Push cancelled by user"
                create_error_result "User cancelled operation"
                exit 0
                ;;
            *)
                echo "Invalid choice. Please select 1-4."
                continue
                ;;
        esac
    done
}

# Handle untracked files if present
if [[ $untracked_count -gt 0 ]]; then
    handle_files "untracked" "$untracked_files" "$untracked_count"
fi

# Handle modified files if present
if [[ $modified_count -gt 0 ]]; then
    handle_files "modified" "$modified_files" "$modified_count"
fi

# Enhanced push logic with better error handling
perform_push() {
    log_info "Preparing to push changes..."

    # Check if there are any commits to push
    local commits_ahead
    if commits_ahead=$(git rev-list --count @{upstream}..HEAD 2>/dev/null); then
        log_verbose "Commits ahead of upstream: $commits_ahead"
        if [[ "$commits_ahead" == "0" ]]; then
            if [[ "$FORCE_PUSH" != "true" ]]; then
                log_warning "No new commits to push - branch is up to date"
                create_success_result "No changes to push" "" "$current_branch"
                echo "Result JSON available at: $RESULT_JSON"
                return 0
            fi
        fi
    else
        log_verbose "Unable to check upstream status (new branch or no upstream)"
    fi

    log_info "Executing push operation..."

    if [[ "$FORCE_PUSH" == "true" ]]; then
        log_warning "Force pushing (this will overwrite remote history)"
        if [[ "$AUTOMATION_MODE" != "true" ]]; then
            read -p "Are you sure? [y/N]: " -n 1 -r confirm
            echo
            if [[ ! $confirm =~ ^[Yy]$ ]]; then
                log_error "Force push cancelled by user"
                create_error_result "Force push cancelled"
                return 1
            fi
        fi

        local push_cmd="git push --force-with-lease origin '$current_branch'"
        if safe_execute "$push_cmd" "Force push to origin"; then
            local commit_sha=$(git rev-parse HEAD)
            create_success_result "Force push successful" "$commit_sha" "$current_branch"
            log_success "Force push completed successfully"
        else
            create_error_result "Force push failed"
            return 1
        fi
    else
        # Check if upstream is set
        if ! git rev-parse --abbrev-ref @{upstream} >/dev/null 2>&1; then
            log_info "Setting upstream and pushing..."
            local push_cmd="git push -u origin '$current_branch'"
            if safe_execute "$push_cmd" "Set upstream and push"; then
                local commit_sha=$(git rev-parse HEAD)
                create_success_result "Push with upstream set successful" "$commit_sha" "$current_branch"
                log_success "Push with upstream completed successfully"
            else
                create_error_result "Push with upstream failed"
                return 1
            fi
        else
            log_info "Pushing to existing upstream..."
            local push_cmd="git push origin '$current_branch'"
            if safe_execute "$push_cmd" "Push to origin"; then
                local commit_sha=$(git rev-parse HEAD)
                create_success_result "Push successful" "$commit_sha" "$current_branch"
                log_success "Push completed successfully"
            else
                create_error_result "Push failed"
                return 1
            fi
        fi
    fi

    echo "Result JSON available at: $RESULT_JSON"
    return 0
}

# Execute the push operation
if ! perform_push; then
    log_error "Push operation failed"
    exit 1
fi

# Enhanced PR creation with better error handling
if [[ "$CREATE_PR" == "true" ]]; then
    log_info "Creating Pull Request..."

    # Check if PR already exists
    if existing_pr=$(gh pr list --head "$current_branch" --json number,url --limit 1 2>>"$ERROR_LOG"); then
        pr_exists=$(echo "$existing_pr" | jq 'length > 0' 2>/dev/null || echo "false")

        if [[ "$pr_exists" == "true" ]]; then
            pr_number=$(echo "$existing_pr" | jq -r '.[0].number')
            pr_url=$(echo "$existing_pr" | jq -r '.[0].url')
            log_warning "PR already exists: #$pr_number"
            echo "  URL: $pr_url"
        else
            # Create new PR
            log_info "Creating new PR..."
            local pr_title="${COMMIT_MESSAGE:-$(git log -1 --pretty=format:'%s')}"
            local default_branch
            default_branch=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | cut -d'/' -f2 || echo "main")
            local pr_body="Enhanced PR creation via pushl

## Changes
$(git log --oneline --no-merges "origin/${default_branch}"..HEAD | head -5 | sed 's/^/- /')

🤖 Generated with enhanced pushl command"

            if [[ "$DRY_RUN" == "true" ]]; then
                echo -e "${YELLOW}[DRY RUN]${NC} Would create PR with title: $pr_title"
            else
                if pr_url=$(gh pr create --title "$pr_title" --body "$pr_body" 2>>"$ERROR_LOG"); then
                    log_success "PR created successfully"
                    echo "  URL: $pr_url"
                else
                    log_error "Failed to create PR"
                    echo "You can create it manually with: gh pr create"
                fi
            fi
        fi
    else
        log_error "Failed to check existing PRs"
    fi
fi

# Post-push verification - check for any remaining uncommitted changes
verify_clean_state() {
    log_info "Verifying clean repository state..."

    # Check for any uncommitted changes after push
    local post_push_status
    if ! post_push_status=$(git status --porcelain 2>"$ERROR_LOG"); then
        log_error "Failed to get post-push git status"
        return 1
    fi

    if [[ -n "$post_push_status" ]]; then
        log_warning "Uncommitted changes detected after push:"
        echo "$post_push_status" | head -20 | sed 's/^/  /'

        # In non-interactive mode, continue with uncommitted changes
        if [[ "${AUTOMATION_MODE:-false}" == "true" ]] || [[ ! -t 0 ]]; then
            log_warning "Non-interactive mode - continuing with uncommitted changes"
            return 0
        fi

        echo -e "\n${YELLOW}⚠️  Repository is not clean after push!${NC}"
        echo -e "${CYAN}Options:${NC}"
        echo "  [1] Stage and commit remaining changes"
        echo "  [2] Show what changed (git diff)"
        echo "  [3] Continue anyway (leave uncommitted)"
        echo "  [4] Stash uncommitted changes"
        echo ""

        while true; do
            read -p "Choose option [1-4]: " -n 1 -r choice
            echo

            case "$choice" in
                1)
                    log_info "Staging and committing remaining changes..."
                    if safe_exec "Stage remaining changes (including deletions)" git add -A; then
                        local commit_msg="Additional changes after push"
                        if safe_execute "git commit -m '$commit_msg'" "Commit remaining changes"; then
                            log_warning "Additional commit created - consider pushing again"
                            return 1  # Indicate more work needed
                        fi
                    fi
                    break
                    ;;
                2)
                    echo -e "\n${CYAN}Current changes:${NC}"
                    git diff --stat
                    echo ""
                    git diff | head -50
                    echo -e "\n${CYAN}Staged changes:${NC}"
                    git diff --cached --stat
                    continue
                    ;;
                3)
                    log_warning "Continuing with uncommitted changes"
                    return 0
                    ;;
                4)
                    if safe_execute "git stash push -m 'Auto-stash after push'" "Stash uncommitted changes"; then
                        log_success "Changes stashed successfully"
                        return 0
                    fi
                    break
                    ;;
                *)
                    echo "Invalid choice. Please select 1-4."
                    continue
                    ;;
            esac
        done
    else
        log_success "Repository is clean - all changes committed and pushed"
    fi

    return 0
}

# Execute post-push verification
if ! verify_clean_state; then
    log_warning "Repository state requires attention after push"
    echo -e "${YELLOW}💡 Consider running '/pushl' again if you committed additional changes${NC}"
fi

# Enhanced completion summary
echo -e "\n${GREEN}✅ pushlite Enhanced Complete${NC}"
echo "  Branch: $current_branch"
echo "  Remote: origin/$current_branch"

if [[ "$CREATE_PR" == "true" ]]; then
    echo "  PR: Processed"
fi

if [[ "$DRY_RUN" == "true" ]]; then
    echo "  Mode: DRY RUN (no changes made)"
fi

echo -e "\n${CYAN}💡 Enhanced Tips:${NC}"
echo "  • Use --verbose for detailed debugging output"
echo "  • Use --dry-run to preview operations"
echo "  • Use --include/--exclude for selective staging"
echo "  • Check $RESULT_JSON for operation details"
echo "  • Error log available at: $ERROR_LOG"
