#!/bin/bash
# enhanced_ci_log_fetcher.sh - Comprehensive CI log fetching with detailed error parsing
# Integrates with Python copilot implementation to provide detailed CI failure analysis

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default working directory for log processing
WORK_DIR="/tmp"

# Function to get workflow runs for a PR
get_workflow_runs_for_pr() {
    local pr_number=$1
    local repo=$2
    
    echo -e "${BLUE}🔍 Finding workflow runs for PR #${pr_number}...${NC}" >&2
    
    # Get PR details to find head SHA
    local pr_data
    pr_data=$(gh api "repos/$repo/pulls/$pr_number" --jq '{head_sha: .head.sha, title: .title}')
    local head_sha
    head_sha=$(echo "$pr_data" | jq -r '.head_sha')
    
    echo "  PR head SHA: $head_sha" >&2
    
    # Get workflow runs for this commit
    local workflow_runs
    workflow_runs=$(gh api "repos/$repo/actions/runs" --jq "
        .workflow_runs 
        | map(select(.head_sha == \"$head_sha\")) 
        | map({
            id, 
            name, 
            status, 
            conclusion, 
            html_url, 
            created_at,
            head_sha: .head_sha
        })")
    
    echo "$workflow_runs"
}

# Function to download and extract logs for a workflow run
download_workflow_logs() {
    local run_id=$1
    local repo=$2
    local work_dir="${3:-$WORK_DIR}"
    
    echo -e "${BLUE}📥 Downloading logs for workflow run ${run_id}...${NC}" >&2
    
    # Create working directory
    local log_dir="$work_dir/workflow_logs_$run_id"
    mkdir -p "$log_dir"
    
    # Download logs
    local log_archive="$log_dir/logs.zip"
    if gh api "repos/$repo/actions/runs/$run_id/logs" > "$log_archive"; then
        echo "  Downloaded to: $log_archive" >&2
        
        # Extract logs using Python (unzip not available)
        python3 -c "
import zipfile
import os
import sys

try:
    with zipfile.ZipFile('$log_archive', 'r') as zip_ref:
        zip_ref.extractall('$log_dir')
    print('  Extracted logs to: $log_dir', file=sys.stderr)
    
    # List extracted files
    for root, dirs, files in os.walk('$log_dir'):
        for file in files:
            if file.endswith('.txt'):
                print(os.path.join(root, file))
except Exception as e:
    print(f'Error extracting logs: {e}', file=sys.stderr)
    sys.exit(1)
"
    else
        echo -e "${RED}❌ Failed to download logs for run $run_id${NC}" >&2
        return 1
    fi
}

# Function to parse test failures from log content
parse_test_failures() {
    local log_content="$1"
    
    # Parse Python unittest failures
    python3 -c "
import re
import json
import sys

log_content = '''$log_content'''
failures = []

# Pattern 1: Python unittest failures
# FAIL: test_name (module.TestClass)
# AssertionError: message
unittest_pattern = r'FAIL: ([^\(]+)\(([^)]+)\)\s*\n.*?AssertionError: ([^\n]+)'
for match in re.finditer(unittest_pattern, log_content, re.MULTILINE | re.DOTALL):
    test_name, test_class, message = match.groups()
    failures.append({
        'type': 'unittest_failure',
        'test_name': test_name.strip(),
        'test_class': test_class.strip(),
        'error_type': 'AssertionError',
        'message': message.strip(),
        'framework': 'unittest'
    })

# Pattern 2: pytest failures  
# FAILED test_file.py::test_name - AssertionError: message
pytest_pattern = r'FAILED ([^:]+)::([^-]+) - ([^:]+): ([^\n]+)'
for match in re.finditer(pytest_pattern, log_content, re.MULTILINE):
    test_file, test_name, error_type, message = match.groups()
    failures.append({
        'type': 'pytest_failure',
        'test_file': test_file.strip(),
        'test_name': test_name.strip(),
        'error_type': error_type.strip(),
        'message': message.strip(),
        'framework': 'pytest'
    })

# Pattern 3: Import errors
# ModuleNotFoundError: No module named 'module'
import_pattern = r'(ModuleNotFoundError|ImportError): ([^\n]+)'
for match in re.finditer(import_pattern, log_content, re.MULTILINE):
    error_type, message = match.groups()
    failures.append({
        'type': 'import_error',
        'error_type': error_type.strip(),
        'message': message.strip(),
        'severity': 'critical'
    })

# Pattern 4: Syntax errors
# SyntaxError: invalid syntax
syntax_pattern = r'SyntaxError: ([^\n]+).*?File \"([^\"]+)\", line (\d+)'
for match in re.finditer(syntax_pattern, log_content, re.MULTILINE | re.DOTALL):
    message, file_path, line_number = match.groups()
    failures.append({
        'type': 'syntax_error',
        'error_type': 'SyntaxError',
        'message': message.strip(),
        'file_path': file_path.strip(),
        'line_number': int(line_number),
        'severity': 'critical'
    })

print(json.dumps(failures, indent=2))
"
}

# Function to extract stack traces from log content
extract_stack_traces() {
    local log_content="$1"
    
    # Extract Python tracebacks
    python3 -c "
import re
import json

log_content = '''$log_content'''
tracebacks = []

# Pattern for Python tracebacks
# Traceback (most recent call last):
#   File \"path\", line N, in function
#     code line
# ErrorType: message
traceback_pattern = r'Traceback \(most recent call last\):(.*?)^(\w+Error): ([^\n]+)'
for match in re.finditer(traceback_pattern, log_content, re.MULTILINE | re.DOTALL):
    trace_content, error_type, error_message = match.groups()
    
    # Extract file/line information from traceback
    file_pattern = r'File \"([^\"]+)\", line (\d+), in ([^\n]+)'
    files = []
    for file_match in re.finditer(file_pattern, trace_content):
        file_path, line_number, function_name = file_match.groups()
        files.append({
            'file_path': file_path.strip(),
            'line_number': int(line_number),
            'function_name': function_name.strip()
        })
    
    tracebacks.append({
        'error_type': error_type.strip(),
        'error_message': error_message.strip(),
        'stack_frames': files,
        'full_traceback': match.group(0).strip()
    })

print(json.dumps(tracebacks, indent=2))
"
}

# Function to categorize and analyze errors
categorize_errors() {
    local failures_json="$1"
    local tracebacks_json="$2"
    
    python3 -c "
import json
import sys
from collections import defaultdict

failures = json.loads('''$failures_json''')
tracebacks = json.loads('''$tracebacks_json''')

# Categorize errors by type and severity
categorized = {
    'test_failures': {
        'unittest': [],
        'pytest': [],
        'other': []
    },
    'import_errors': [],
    'syntax_errors': [],
    'runtime_errors': [],
    'stack_traces': tracebacks,
    'summary': {
        'total_failures': len(failures),
        'total_tracebacks': len(tracebacks),
        'critical_errors': 0,
        'test_errors': 0
    }
}

for failure in failures:
    failure_type = failure.get('type', 'unknown')
    
    if failure_type in ['unittest_failure', 'pytest_failure']:
        framework = failure.get('framework', 'other')
        categorized['test_failures'][framework].append(failure)
        categorized['summary']['test_errors'] += 1
    elif failure_type == 'import_error':
        categorized['import_errors'].append(failure)
        categorized['summary']['critical_errors'] += 1
    elif failure_type == 'syntax_error':
        categorized['syntax_errors'].append(failure)
        categorized['summary']['critical_errors'] += 1
    else:
        categorized['runtime_errors'].append(failure)

print(json.dumps(categorized, indent=2))
"
}

# Function to analyze logs from a specific workflow run
analyze_workflow_logs() {
    local run_id=$1
    local repo=$2
    local work_dir="${3:-$WORK_DIR}"
    
    echo -e "${BLUE}🔍 Analyzing logs for workflow run ${run_id}...${NC}" >&2
    
    local log_dir="$work_dir/workflow_logs_$run_id"
    local analysis_file="$work_dir/analysis_${run_id}.json"
    
    if [[ ! -d "$log_dir" ]]; then
        echo -e "${RED}❌ Log directory not found: $log_dir${NC}" >&2
        return 1
    fi
    
    # Find all log files and analyze them
    local all_failures="[]"
    local all_tracebacks="[]"
    
    find "$log_dir" -name "*.txt" -type f | while read -r log_file; do
        echo "  Analyzing: $(basename "$log_file")" >&2
        
        # Read log content
        local log_content
        log_content=$(cat "$log_file")
        
        # Parse failures and tracebacks
        local failures
        local tracebacks
        failures=$(parse_test_failures "$log_content")
        tracebacks=$(extract_stack_traces "$log_content")
        
        # Combine with previous results
        all_failures=$(echo "$all_failures $failures" | jq -s 'add')
        all_tracebacks=$(echo "$all_tracebacks $tracebacks" | jq -s 'add')
    done
    
    # Categorize all errors
    local categorized_errors
    categorized_errors=$(categorize_errors "$all_failures" "$all_tracebacks")
    
    # Add metadata
    local final_analysis
    final_analysis=$(echo "$categorized_errors" | jq ". + {
        run_id: $run_id,
        analysis_timestamp: \"$(date -Iseconds)\",
        log_directory: \"$log_dir\"
    }")
    
    # Save analysis
    echo "$final_analysis" > "$analysis_file"
    echo "$final_analysis"
}

# Function to get detailed CI errors for a PR (main interface)
get_detailed_ci_errors() {
    local pr_number=$1
    local repo="${2:-$(gh repo view --json owner,name | jq -r '"\(.owner.login)/\(.name)"')}"
    local work_dir="${3:-$WORK_DIR}"
    
    echo -e "${BLUE}🔬 Fetching detailed CI errors for PR #${pr_number}...${NC}" >&2
    
    # Create output directory
    local output_dir="$work_dir/copilot_pr_${pr_number}"
    mkdir -p "$output_dir"
    
    # Get workflow runs for PR
    local workflow_runs
    workflow_runs=$(get_workflow_runs_for_pr "$pr_number" "$repo")
    
    # Filter to failed/cancelled runs
    local failed_runs
    failed_runs=$(echo "$workflow_runs" | jq '[.[] | select(.conclusion == "failure" or .conclusion == "cancelled")]')
    
    local failed_count
    failed_count=$(echo "$failed_runs" | jq 'length')
    
    echo "  Found $failed_count failed workflow runs" >&2
    
    if [[ $failed_count -eq 0 ]]; then
        echo '{"error": "No failed workflow runs found", "failed_runs": []}' > "$output_dir/detailed_ci_errors.json"
        echo '{"error": "No failed workflow runs found", "failed_runs": []}'
        return 0
    fi
    
    # Analyze each failed run
    local all_analyses="[]"
    echo "$failed_runs" | jq -r '.[].id' | while read -r run_id; do
        echo -e "${YELLOW}📋 Processing workflow run ${run_id}...${NC}" >&2
        
        # Download and extract logs
        if download_workflow_logs "$run_id" "$repo" "$work_dir"; then
            # Analyze logs
            local analysis
            analysis=$(analyze_workflow_logs "$run_id" "$repo" "$work_dir")
            
            # Add to combined results
            all_analyses=$(echo "$all_analyses" | jq ". + [$analysis]")
        else
            echo -e "${RED}❌ Failed to process workflow run ${run_id}${NC}" >&2
        fi
    done
    
    # Create final combined analysis
    local final_result
    final_result=$(jq -n "
        {
            pr_number: $pr_number,
            repo: \"$repo\",
            failed_runs: $failed_runs,
            detailed_analyses: $all_analyses,
            summary: {
                failed_runs_count: ($failed_runs | length),
                total_test_failures: ($all_analyses | map(.summary.test_errors) | add // 0),
                total_critical_errors: ($all_analyses | map(.summary.critical_errors) | add // 0),
                analysis_timestamp: \"$(date -Iseconds)\"
            }
        }")
    
    # Save detailed results
    echo "$final_result" > "$output_dir/detailed_ci_errors.json"
    
    # Return result
    echo "$final_result"
}

# Main function when script is called directly
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <PR_NUMBER> [REPO] [WORK_DIR]"
        echo "  PR_NUMBER: GitHub PR number"
        echo "  REPO: Repository in format owner/name (optional, auto-detected)"
        echo "  WORK_DIR: Working directory for logs (optional, default: /tmp)"
        exit 1
    fi
    
    local pr_number=$1
    local repo="${2:-}"
    local work_dir="${3:-$WORK_DIR}"
    
    get_detailed_ci_errors "$pr_number" "$repo" "$work_dir"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi