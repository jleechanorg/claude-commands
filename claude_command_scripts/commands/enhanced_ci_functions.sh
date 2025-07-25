#!/bin/bash
# enhanced_ci_functions.sh - Enhanced CI status checking with detailed error parsing
# Integration functions for Python copilot implementation

# Source the enhanced CI log fetcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/enhanced_ci_log_fetcher.sh"

# Enhanced function to check CI status with detailed error parsing
check_ci_status_enhanced() {
    local pr_number=$1
    local include_detailed_logs="${2:-false}"
    
    echo -e "${BLUE}🔍 Checking CI status with enhanced analysis...${NC}" >&2
    
    # Get basic check status (existing functionality)
    local checks
    checks=$(gh pr view "$pr_number" --json statusCheckRollup | jq '.statusCheckRollup // []')
    
    # Filter failed and cancelled checks
    local failed_checks
    failed_checks=$(echo "$checks" | jq '[.[] | select(.conclusion == "FAILURE" or .conclusion == "CANCELLED")]')
    
    local failed_count
    failed_count=$(echo "$failed_checks" | jq 'length')
    
    # If we have failures and detailed logs are requested, fetch them
    if [[ $failed_count -gt 0 && "$include_detailed_logs" == "true" ]]; then
        echo -e "${YELLOW}📋 Fetching detailed CI logs for $failed_count failed checks...${NC}" >&2
        
        # Get detailed CI errors using our enhanced fetcher
        local detailed_errors
        detailed_errors=$(get_detailed_ci_errors "$pr_number")
        
        # Combine basic checks with detailed analysis
        local enhanced_result
        enhanced_result=$(jq -n "
            {
                basic_checks: $failed_checks,
                detailed_errors: $detailed_errors,
                summary: {
                    failed_checks_count: ($failed_checks | length),
                    has_detailed_analysis: true,
                    total_test_failures: ($detailed_errors.summary.total_test_failures // 0),
                    total_critical_errors: ($detailed_errors.summary.total_critical_errors // 0)
                }
            }")
        
        echo "$enhanced_result"
    else
        # Return basic checks only
        echo "$failed_checks"
    fi
}

# Function to present enhanced CI data for Claude analysis
present_enhanced_ci_data() {
    local pr_number=$1
    local enhanced_ci_data=$2
    
    echo -e "${BLUE}📋 Preparing enhanced CI data for Claude analysis...${NC}" >&2
    
    # Determine if we have detailed analysis
    local has_detailed
    has_detailed=$(echo "$enhanced_ci_data" | jq -r '.summary.has_detailed_analysis // false')
    
    # Get branch name once for performance (addressing Copilot feedback) with sanitization
    local branch_name
    branch_name=$(git branch --show-current 2>/dev/null || echo "detached")
    branch_name=${branch_name//\//_}
    local data_dir="/tmp/copilot_pr_${branch_name}_${pr_number}"
    mkdir -p "$data_dir"
    
    if [[ "$has_detailed" == "true" ]]; then
        # Save enhanced data
        echo "$enhanced_ci_data" > "$data_dir/enhanced_ci_analysis.json"
        
        # Extract key failure information for summary
        local test_failures
        local critical_errors
        test_failures=$(echo "$enhanced_ci_data" | jq -r '.summary.total_test_failures // 0')
        critical_errors=$(echo "$enhanced_ci_data" | jq -r '.summary.total_critical_errors // 0')
        
        # Create enhanced summary
        cat > "$data_dir/ci_summary.md" << EOF
# Enhanced CI Analysis for PR #${pr_number}

## Summary
- **Test Failures**: $test_failures
- **Critical Errors**: $critical_errors (import/syntax errors)
- **Failed Workflow Runs**: $(echo "$enhanced_ci_data" | jq -r '.detailed_errors.summary.failed_runs_count // 0')

## Detailed Analysis Available
✅ **Enhanced CI log analysis completed**
- Stack traces extracted and categorized
- Error messages parsed with context
- Test failures identified with file/line information
- Import and syntax errors highlighted

## Data Files
- \`enhanced_ci_analysis.json\`: Complete detailed analysis
- \`failed_checks.json\`: Basic GitHub check status
- \`detailed_ci_errors.json\`: Detailed error extraction

## Error Categories Found
EOF
        
        # Add error category details
        echo "$enhanced_ci_data" | jq -r '
        .detailed_errors.detailed_analyses[]? | 
        "### " + (.run_id | tostring) + " Analysis
        - Test Failures: " + (.summary.test_errors | tostring) + "
        - Critical Errors: " + (.summary.critical_errors | tostring) + "
        - Stack Traces: " + (.summary.total_tracebacks | tostring) + "
        "' >> "$data_dir/ci_summary.md"
        
        echo "Enhanced CI analysis saved to: $data_dir/"
        echo "  📊 Summary: $data_dir/ci_summary.md"
        echo "  📋 Detailed: $data_dir/enhanced_ci_analysis.json"
        echo "  🔍 Test failures: $test_failures, Critical errors: $critical_errors"
    else
        # Basic analysis only
        echo "$enhanced_ci_data" > "$data_dir/failed_checks.json"
        
        local failed_count
        failed_count=$(echo "$enhanced_ci_data" | jq 'length')
        
        cat > "$data_dir/ci_summary.md" << EOF
# Basic CI Analysis for PR #${pr_number}

## Summary
- **Failed Checks**: $failed_count
- **Analysis Type**: Basic status only

## Available Data
- \`failed_checks.json\`: GitHub check status

## Note
Run with detailed analysis enabled to get comprehensive error parsing.
EOF
        
        echo "Basic CI analysis saved to: $data_dir/"
        echo "  📊 Failed checks: $failed_count"
        echo "  💡 Tip: Use enhanced mode for detailed error analysis"
    fi
}

# Function to extract actionable error messages for Claude
extract_actionable_errors() {
    local enhanced_ci_data=$1
    
    # Extract specific error types that are actionable
    echo "$enhanced_ci_data" | jq '
    {
        import_errors: [
            .detailed_errors.detailed_analyses[]?.import_errors[]? |
            {
                type: .error_type,
                message: .message,
                severity: .severity,
                action_needed: "Install missing dependency or fix import path"
            }
        ],
        syntax_errors: [
            .detailed_errors.detailed_analyses[]?.syntax_errors[]? |
            {
                file: .file_path,
                line: .line_number,
                message: .message,
                action_needed: "Fix syntax error at specified location"
            }
        ],
        test_failures: [
            .detailed_errors.detailed_analyses[]?.test_failures.unittest[]?, 
            .detailed_errors.detailed_analyses[]?.test_failures.pytest[]? |
            {
                test: (.test_name // .test_file),
                error: .error_type,
                message: .message,
                framework: .framework,
                action_needed: "Review test logic and fix assertion"
            }
        ],
        stack_traces: [
            .detailed_errors.detailed_analyses[]?.stack_traces[]? |
            {
                error: .error_type,
                message: .error_message,
                main_file: (.stack_frames[0].file_path // "unknown"),
                main_line: (.stack_frames[0].line_number // 0),
                action_needed: "Debug runtime error at specified location"
            }
        ]
    }'
}

# Function to generate priority recommendations
generate_error_priorities() {
    local actionable_errors=$1
    
    echo "$actionable_errors" | jq '
    {
        critical_first: [
            (.import_errors[] | . + {priority: 1, reason: "Prevents code execution"}),
            (.syntax_errors[] | . + {priority: 1, reason: "Prevents code parsing"})
        ],
        high_priority: [
            (.stack_traces[] | . + {priority: 2, reason: "Runtime failures"})
        ],
        medium_priority: [
            (.test_failures[] | . + {priority: 3, reason: "Test logic issues"})
        ]
    } |
    {
        recommended_order: (.critical_first + .high_priority + .medium_priority),
        summary: {
            critical_count: (.critical_first | length),
            high_count: (.high_priority | length),
            medium_count: (.medium_priority | length),
            total_actionable: ((.critical_first + .high_priority + .medium_priority) | length)
        }
    }'
}

# Integration function for existing copilot.sh workflow
integrate_enhanced_ci_analysis() {
    local pr_number=$1
    local request_detailed="${2:-true}"
    
    echo -e "${BLUE}🚀 Running enhanced CI analysis integration...${NC}" >&2
    
    # Get enhanced CI status
    local enhanced_data
    enhanced_data=$(check_ci_status_enhanced "$pr_number" "$request_detailed")
    
    # Present data for Claude analysis
    present_enhanced_ci_data "$pr_number" "$enhanced_data"
    
    # Extract actionable errors if detailed analysis available
    local has_detailed
    has_detailed=$(echo "$enhanced_data" | jq -r '.summary.has_detailed_analysis // false')
    
    if [[ "$has_detailed" == "true" ]]; then
        echo -e "${BLUE}🎯 Extracting actionable errors...${NC}" >&2
        
        local actionable_errors
        actionable_errors=$(extract_actionable_errors "$enhanced_data")
        
        local priorities
        priorities=$(generate_error_priorities "$actionable_errors")
        
        # Save actionable analysis (branch name logic duplicated from present_enhanced_ci_data for function independence)
        local branch_name
        branch_name=$(git branch --show-current 2>/dev/null || echo "detached")
        branch_name=${branch_name//\//_}
        local data_dir="/tmp/copilot_pr_${branch_name}_${pr_number}"
        echo "$actionable_errors" > "$data_dir/actionable_errors.json"
        echo "$priorities" > "$data_dir/error_priorities.json"
        
        # Generate Claude-friendly summary
        cat > "$data_dir/claude_analysis_input.md" << EOF
# PR #${pr_number} CI Failure Analysis - Ready for Claude

## Quick Summary
$(echo "$priorities" | jq -r '
"- Critical Issues: " + (.summary.critical_count | tostring) + " (import/syntax errors)
- High Priority: " + (.summary.high_count | tostring) + " (runtime failures)  
- Medium Priority: " + (.summary.medium_count | tostring) + " (test failures)
- Total Actionable: " + (.summary.total_actionable | tostring)')

## Recommended Fix Order
$(echo "$priorities" | jq -r '.recommended_order[] | "1. **" + (.action_needed // "Fix issue") + "** - " + (.message // .error // "No details") + " (Priority: " + (.priority | tostring) + ")"')

## Available Data Files
- \`actionable_errors.json\`: Structured error data for programmatic processing
- \`error_priorities.json\`: Prioritized fix recommendations  
- \`enhanced_ci_analysis.json\`: Complete detailed analysis
- \`ci_summary.md\`: Human-readable summary

## Claude Instructions
Review the actionable errors and provide specific fix recommendations. Focus on critical issues first (import/syntax), then runtime failures, then test logic.
EOF
        
        echo -e "${GREEN}✅ Enhanced CI analysis complete!${NC}" >&2
        echo "  📊 Total actionable errors: $(echo "$priorities" | jq -r '.summary.total_actionable')"
        echo "  🔥 Critical issues: $(echo "$priorities" | jq -r '.summary.critical_count')"
        echo "  📁 Analysis saved to: $data_dir/"
    fi
    
    # Return enhanced data for further processing
    echo "$enhanced_data"
}