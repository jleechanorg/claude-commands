#!/bin/bash
# pushlite.sh - Enhanced reliable push command with selective staging and error handling
# Enhanced version addressing reliability issues from PR #1057
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
    echo "  3. Verbose mode for debugging complex scenarios"
    echo "  4. Dry-run mode to preview operations"
    echo "  5. Progress indicators and status messages"
    echo "  6. Always creates result JSON for automation"
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

    # Apply include patterns
    if [[ ${#INCLUDE_PATTERNS[@]} -gt 0 ]]; then
        local included=""
        for pattern in "${INCLUDE_PATTERNS[@]}"; do
            log_verbose "Applying include pattern: $pattern"
            local matches=$(echo "$status" | grep "$pattern" || true)
            if [[ -n "$matches" ]]; then
                included="$included$matches"$'\n'
            fi
        done
        filtered_status="$included"
    fi

    # Apply exclude patterns
    if [[ ${#EXCLUDE_PATTERNS[@]} -gt 0 ]]; then
        for pattern in "${EXCLUDE_PATTERNS[@]}"; do
            log_verbose "Applying exclude pattern: $pattern"
            filtered_status=$(echo "$filtered_status" | grep -v "$pattern" || true)
        done
    fi

    echo "$filtered_status"
}

# Safe execution wrapper for dry runs
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
untracked_files=$(echo "$filtered_status" | grep "^??" | cut -c4- || true)
staged_files=$(echo "$filtered_status" | grep "^[MARCDT]" | cut -c4- || true)
modified_files=$(echo "$filtered_status" | grep "^.[MARCDT]" | cut -c4- || true)
conflicted_files=$(echo "$git_status" | grep "^UU\|^AA\|^DD" | cut -c4- || true)

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
                    [[ -n "$file" ]] && safe_execute "git add '$file'" "Stage filtered file: $file"
                done <<< "$files"
            else
                safe_execute "git add ." "Stage all untracked files"
            fi
        else
            safe_execute "git add ." "Stage all modified files"
        fi

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
                safe_execute "git add ." "Stage all $file_type files"
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
                        safe_execute "git add '$file'" "Stage selected file: $file"
                    done

                    local commit_msg="${COMMIT_MESSAGE:-Add selected $file_type files}"
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
            local pr_body="Enhanced PR creation via pushl

## Changes
$(git log --oneline --no-merges origin/main..HEAD | head -5 | sed 's/^/- /')

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

# Enhanced post-push operations
run_post_push_checks() {
    log_info "Running post-push checks..."

    # Run linting checks (non-blocking)
    if [[ "${SKIP_LINT:-false}" != "true" && -f "./run_lint.sh" ]]; then
        log_info "Running post-push linting checks..."
        if [[ -x "./run_lint.sh" ]]; then
            if safe_execute "./run_lint.sh mvp_site" "Run linting checks"; then
                log_success "All linting checks passed"
            else
                log_warning "Some linting issues found"
                echo -e "${CYAN}💡 Run './run_lint.sh mvp_site fix' to auto-fix issues${NC}"
                echo -e "${CYAN}💡 Consider fixing before next push${NC}"
            fi
        else
            log_warning "Lint script found but not executable"
        fi
    else
        if [[ "${SKIP_LINT:-false}" == "true" ]]; then
            log_verbose "Skipping post-push linting (SKIP_LINT=true)"
        else
            log_verbose "Linting script not found, skipping"
        fi
    fi

    # Run CI replica test
    if [[ -f "./run_ci_replica.sh" ]]; then
        log_info "Running CI replica test..."
        if safe_execute "./run_ci_replica.sh" "Run CI replica test"; then
            log_success "CI replica tests passed"
        else
            log_warning "CI replica tests failed - review before merging"
        fi
    else
        log_verbose "CI replica script not found"
    fi
}

# Execute post-push checks
run_post_push_checks

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
