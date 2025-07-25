#!/bin/bash

# /copilotsuper - Batch Copilot analysis on multiple PRs with isolation
# Usage: ./claude_command_scripts/commands/copilotsuper.sh PR1 [PR2 PR3...]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEMP_BRANCH_PREFIX="dev_copilotsuper"
TIMESTAMP=$(date +%s)
TEMP_BRANCH="${TEMP_BRANCH_PREFIX}_${TIMESTAMP}"
ORIGINAL_BRANCH=""
# Resolve branch; fall back for detached-HEAD; make it filename-safe (PR #941 standard)
RAW_BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "detached")
SANITIZED_BRANCH=$(echo "$RAW_BRANCH_NAME" | sed 's/[^a-zA-Z0-9._-]/_/g' | sed 's/^[.-]*//g')
OUTPUT_DIR="/tmp/copilot_${SANITIZED_BRANCH}"
mkdir -p "$OUTPUT_DIR"
RESULTS_FILE="$OUTPUT_DIR/copilotsuper_results_${TIMESTAMP}.txt"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    echo "GitHub Copilot Super - Batch PR Analysis"
    echo ""
    echo "Usage: $0 PR1 [PR2 PR3...]"
    echo ""
    echo "Options:"
    echo "  --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 718 719 720    # Process PRs 718, 719, and 720"
    echo "  $0 715            # Process single PR 715"
    echo ""
    echo "Features:"
    echo "  - Isolated processing (preserves current branch)"
    echo "  - Batch analysis of multiple PRs"
    echo "  - Comprehensive Copilot fixes"
    echo "  - Automatic commit and push"
    echo "  - Aggregate reporting"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary resources..."
    
    # Return to original branch if we know it
    if [[ -n "$ORIGINAL_BRANCH" ]]; then
        log_info "Returning to original branch: $ORIGINAL_BRANCH"
        git checkout "$ORIGINAL_BRANCH" 2>/dev/null || log_warning "Could not return to original branch"
    fi
    
    # Remove temp branch if it exists
    if git branch | grep -q "$TEMP_BRANCH"; then
        log_info "Removing temporary branch: $TEMP_BRANCH"
        git branch -D "$TEMP_BRANCH" 2>/dev/null || log_warning "Could not remove temp branch"
    fi
    
    # Clean up results file
    if [[ -f "$RESULTS_FILE" ]]; then
        rm -f "$RESULTS_FILE"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Validate PR number
validate_pr() {
    local pr_num="$1"
    if ! [[ "$pr_num" =~ ^[0-9]+$ ]]; then
        log_error "Invalid PR number: $pr_num"
        return 1
    fi
    
    # Check if PR exists
    if ! gh pr view "$pr_num" >/dev/null 2>&1; then
        log_error "PR #$pr_num does not exist or is not accessible"
        return 1
    fi
    
    return 0
}

# Process single PR
process_pr() {
    local pr_num="$1"
    local start_time=$(date)
    
    log_info "Processing PR #$pr_num..."
    
    # Checkout the PR
    log_info "Checking out PR #$pr_num"
    if ! gh pr checkout "$pr_num" 2>/dev/null; then
        log_error "Failed to checkout PR #$pr_num"
        echo "❌ PR #$pr_num: Failed to checkout" >> "$RESULTS_FILE"
        return 1
    fi
    
    # Run copilot analysis
    log_info "Running Copilot analysis on PR #$pr_num"
    local copilot_output=""
    local copilot_exit_code=0
    
    # Use Python implementation (Option 3 architecture)
    if [[ -f ".claude/commands/copilot.py" ]]; then
        log_info "Using Python implementation: .claude/commands/copilot.py"
        copilot_output=$(python3 .claude/commands/copilot.py --shell-mode "$pr_num" 2>&1)
        copilot_exit_code=$?
    else
        log_error "No copilot implementation found"
        log_error "Looked for: .claude/commands/copilot.py"
        echo "❌ PR #$pr_num: Python copilot implementation not available" >> "$RESULTS_FILE"
        return 1
    fi
    
    # Parse results with hybrid JSON/grep approach
    local fixes_count=0
    local tests_fixed=0
    local commits_made=0
    local json_summary="$OUTPUT_DIR/pr_${pr_num}_summary.json"
    
    # Try JSON parsing first (reliable), fallback to grep parsing
    if [[ -f "$json_summary" ]]; then
        log_info "Using structured JSON parsing for reliable results"
        fixes_count=$(jq '.fixes_applied // 0' "$json_summary" 2>/dev/null || echo "0")
        local ci_failures=$(jq '.ci_failures // 0' "$json_summary" 2>/dev/null || echo "0")
        tests_fixed=$((ci_failures > 0 ? fixes_count : 0))  # Estimate tests fixed
    else
        log_info "JSON summary not found, falling back to grep parsing"
        # Fallback to original grep-based parsing
        fixes_count=$(echo "$copilot_output" | grep -c "FIXED" || echo "0")
        tests_fixed=$(echo "$copilot_output" | grep -c "test.*pass" || echo "0")
    fi
    
    commits_made=$(git log --oneline HEAD~5..HEAD 2>/dev/null | wc -l || echo "0")
    
    # Determine status
    local status="✅ Ready to merge"
    if [[ $copilot_exit_code -ne 0 ]]; then
        status="⚠️ Needs attention"
    elif [[ $fixes_count -eq 0 && $tests_fixed -eq 0 ]]; then
        status="✅ No issues found"
    fi
    
    # Record results
    local end_time=$(date)
    local pr_title=$(gh pr view "$pr_num" --json title -q '.title' 2>/dev/null || echo "Unknown")
    
    echo "$status PR #$pr_num: $pr_title" >> "$RESULTS_FILE"
    echo "  - Fixed: $fixes_count issues" >> "$RESULTS_FILE"
    echo "  - Tests: $tests_fixed resolved" >> "$RESULTS_FILE"
    echo "  - Commits: $commits_made new commits" >> "$RESULTS_FILE"
    echo "  - Started: $start_time" >> "$RESULTS_FILE"
    echo "  - Completed: $end_time" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    log_success "Completed PR #$pr_num: $fixes_count fixes, $tests_fixed tests resolved"
    return 0
}

# Main execution
main() {
    # Parse arguments
    if [[ $# -eq 0 ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        show_help
        exit 0
    fi
    
    # Initialize results file
    echo "🤖 COPILOT SUPER ANALYSIS RESULTS" > "$RESULTS_FILE"
    echo "Generated: $(date)" >> "$RESULTS_FILE"
    echo "================================================" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    # Save current branch
    ORIGINAL_BRANCH=$(git branch --show-current)
    log_info "Current branch: $ORIGINAL_BRANCH"
    
    # Create temporary branch from main
    log_info "Creating temporary branch: $TEMP_BRANCH"
    git fetch origin main >/dev/null 2>&1 || log_warning "Could not fetch latest main"
    
    if ! git checkout -b "$TEMP_BRANCH" origin/main 2>/dev/null; then
        log_error "Failed to create temporary branch"
        exit 1
    fi
    
    # Validate all PR numbers first
    local valid_prs=()
    for pr_num in "$@"; do
        if validate_pr "$pr_num"; then
            valid_prs+=("$pr_num")
        else
            echo "❌ PR #$pr_num: Invalid or inaccessible" >> "$RESULTS_FILE"
        fi
    done
    
    if [[ ${#valid_prs[@]} -eq 0 ]]; then
        log_error "No valid PRs to process"
        exit 1
    fi
    
    log_info "Processing ${#valid_prs[@]} valid PRs: ${valid_prs[*]}"
    
    # Process each PR
    local processed=0
    local successful=0
    
    for pr_num in "${valid_prs[@]}"; do
        if process_pr "$pr_num"; then
            ((successful++))
        fi
        ((processed++))
        
        # Brief pause between PRs
        sleep 1
    done
    
    # Generate summary
    echo "📊 BATCH SUMMARY:" >> "$RESULTS_FILE"
    echo "- Processed: $processed PRs" >> "$RESULTS_FILE"
    echo "- Successful: $successful PRs" >> "$RESULTS_FILE"
    echo "- Failed: $((processed - successful)) PRs" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    
    # Display results
    echo ""
    log_success "Copilot Super analysis complete!"
    echo ""
    cat "$RESULTS_FILE"
    
    return 0
}

# Execute main function
main "$@"