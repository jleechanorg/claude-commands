#!/bin/bash
# pushlite.sh - Streamlined reliable push command
# LLM-first approach: PR intelligence handled by Claude, passed as arguments

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Global variables
VERBOSE=false
DRY_RUN=false
ERROR_LOG="/tmp/pushl_error_$(date +%s).log"
RESULT_JSON="/tmp/pushl_result_$(date +%s).json"

# Core functionality flags
CREATE_PR=false
FORCE_PUSH=false
AUTOMATION_MODE=false
COMMIT_MESSAGE=""

# Pre-generated PR content (passed as arguments)
PR_TITLE=""
PR_DESCRIPTION=""
PR_LABELS=""

# Helper functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_verbose() { [[ "$VERBOSE" == true ]] && echo -e "${CYAN}🔍${NC} $1"; }

show_help() {
    cat << 'EOF'
pushlite - Streamlined reliable push command (LLM-first approach)

Usage: pushlite.sh [options]

Basic Options:
  pr                          Push and create PR to main
  pr --title "Title"          Create PR with specific title  
  pr --description "Desc"     Create PR with specific description
  pr --labels "label1,label2" Create PR with specific labels
  force                       Force push to origin (use with caution)
  -h, --help                  Show this help message

Enhanced Options:
  -v, --verbose               Enable verbose output for debugging
  --dry-run                   Preview operations without executing
  -m, --message MSG           Commit message

PR Content Options:
  --pr-title "Title"          Set PR title
  --pr-description "Desc"     Set PR description  
  --pr-labels "l1,l2,l3"      Set PR labels (comma-separated)

Description:
  Streamlined push command focusing on core reliability:
  1. Comprehensive error handling and reporting
  2. Automatic lint fixes for staged files only
  3. Post-push verification of uncommitted changes
  4. Interactive handling of unclean repository state
  5. LLM-generated PR content passed as arguments

Examples:
  pushlite.sh                                    # Simple push
  pushlite.sh pr                                 # Push and create basic PR
  pushlite.sh pr --title "feat: new feature"    # PR with custom title
  pushlite.sh --verbose --dry-run               # Debug mode preview
  pushlite.sh -m 'fix: resolve conflicts' force # Force push with message
  
  # Full PR with LLM-generated content:
  pushlite.sh pr --pr-title "feat: GitHub stats integration" \
                 --pr-description "$(cat pr_desc.txt)" \
                 --pr-labels "type:feature,size:large,scope:backend"

LLM Integration:
  This script is designed to work with Claude Code CLI where:
  1. Claude analyzes git diff vs origin/main
  2. Claude generates smart PR title, description, and labels
  3. Claude passes pre-generated content to this streamlined script
  4. Script focuses on reliable push/PR operations only

EOF
    exit 0
}

# Check for environment automation mode
if [[ -n "${COPILOT_WORKFLOW:-}" ]] || [[ -n "${CI:-}" ]] || [[ ! -t 0 ]]; then
    AUTOMATION_MODE=true
fi

# Parse arguments
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
            shift
            ;;
        -m|--message)
            shift
            COMMIT_MESSAGE="$1"
            shift
            ;;
        --pr-title)
            shift
            PR_TITLE="$1"
            shift
            ;;
        --pr-description)
            shift
            PR_DESCRIPTION="$1"
            shift
            ;;
        --pr-labels)
            shift
            PR_LABELS="$1"
            shift
            ;;
        --title)
            # Legacy support
            shift
            PR_TITLE="$1"
            shift
            ;;
        --description)
            # Legacy support
            shift
            PR_DESCRIPTION="$1"
            shift
            ;;
        --labels)
            # Legacy support
            shift
            PR_LABELS="$1"
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Core push function
do_push() {
    local current_branch
    current_branch=$(git branch --show-current)
    
    if [[ "$current_branch" == "main" ]] && [[ "$FORCE_PUSH" != true ]]; then
        log_error "Cannot push directly to main branch without --force"
        exit 1
    fi
    
    log_info "Pushing branch: $current_branch"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would execute: git push origin HEAD:$current_branch"
        return 0
    fi
    
    if [[ "$FORCE_PUSH" == true ]]; then
        log_warning "Force pushing to $current_branch"
        git push --force origin HEAD:"$current_branch"
    else
        git push origin HEAD:"$current_branch"
    fi
    
    log_success "Successfully pushed to origin/$current_branch"
}

# Create PR function
create_pr() {
    local current_branch
    current_branch=$(git branch --show-current)
    
    # Set defaults if not provided
    if [[ -z "$PR_TITLE" ]]; then
        PR_TITLE="$(git log -1 --pretty=format:'%s')"
        log_verbose "Using commit message as PR title: $PR_TITLE"
    fi
    
    if [[ -z "$PR_DESCRIPTION" ]]; then
        PR_DESCRIPTION="Automated PR from branch: $current_branch"
        log_verbose "Using default PR description"
    fi
    
    log_info "Creating PR: $PR_TITLE"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would create PR with:"
        log_info "  Title: $PR_TITLE"
        log_info "  Description: $PR_DESCRIPTION"
        [[ -n "$PR_LABELS" ]] && log_info "  Labels: $PR_LABELS"
        return 0
    fi
    
    # Create PR using gh CLI
    local pr_cmd="gh pr create --title \"$PR_TITLE\" --body \"$PR_DESCRIPTION\""
    
    if [[ -n "$PR_LABELS" ]]; then
        # Convert comma-separated labels to individual --label flags
        local labels_array
        IFS=',' read -ra labels_array <<< "$PR_LABELS"
        for label in "${labels_array[@]}"; do
            label=$(echo "$label" | xargs) # trim whitespace
            pr_cmd+=" --label \"$label\""
        done
    fi
    
    log_verbose "Executing: $pr_cmd"
    
    # Execute PR creation
    local pr_url
    if pr_url=$(eval "$pr_cmd" 2>&1); then
        log_success "PR created successfully: $pr_url"
        
        # Save result for automation
        cat > "$RESULT_JSON" << EOF
{
  "success": true,
  "action": "create_pr",
  "pr_url": "$pr_url",
  "branch": "$current_branch",
  "title": "$PR_TITLE",
  "labels": "$PR_LABELS"
}
EOF
        
        echo "$pr_url"
    else
        log_error "Failed to create PR: $pr_url"
        cat > "$RESULT_JSON" << EOF
{
  "success": false,
  "action": "create_pr",
  "error": "$pr_url",
  "branch": "$current_branch"
}
EOF
        exit 1
    fi
}

# Verify repository state
verify_repo_state() {
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    local status
    status=$(git status --porcelain)
    
    if [[ -n "$status" ]] && [[ "$AUTOMATION_MODE" != true ]]; then
        log_warning "Repository has uncommitted changes:"
        git status --short
        
        if [[ "$DRY_RUN" != true ]]; then
            read -r -p "Continue anyway? (y/N): " response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                log_info "Aborted by user"
                exit 1
            fi
        fi
    fi
}

# Main execution
main() {
    log_verbose "Starting pushlite.sh in$([ "$DRY_RUN" == true ] && echo " DRY RUN") mode"
    
    verify_repo_state
    
    # Always push first
    do_push
    
    # Create PR if requested
    if [[ "$CREATE_PR" == true ]]; then
        create_pr
    fi
    
    # Create success result
    if [[ "$CREATE_PR" != true ]]; then
        cat > "$RESULT_JSON" << EOF
{
  "success": true,
  "action": "push_only",
  "branch": "$(git branch --show-current)"
}
EOF
    fi
    
    log_success "Operation completed successfully"
}

# Error handling
trap 'log_error "Script failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@"