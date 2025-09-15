#!/bin/bash

# ==============================================================================
# Complete GitHub Statistics Script
#
# Description:
# This script provides comprehensive GitHub development analysis including:
# 1. Commit statistics and categorization
# 2. Pull request analysis and types
# 3. Code change metrics (excluding vendor files)
# 4. Lines of code breakdown by file type
# 5. Test vs non-test code ratios
# 6. Daily averages and productivity metrics
#
# Usage:
# ./loc.sh [date]           # Show complete GitHub statistics since date
# ./loc.sh --help           # Show this help
# ==============================================================================

# --- Configuration ---

# Check if help is requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [date]"
    echo "  date: Optional date in YYYY-MM-DD format (defaults to 30 days ago)"
    echo "Examples:"
    echo "  ./loc.sh                    # Last 30 days"
    echo "  ./loc.sh 2025-06-01         # Since June 1st, 2025"
    exit 0
fi

# Parse date argument
SINCE_DATE="$1"

# --- Main Execution ---

# Check if Python script exists
PYTHON_SCRIPT="scripts/analyze_git_stats.py"
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: $PYTHON_SCRIPT not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

echo "🚀 Generating Complete GitHub Statistics..."
echo "========================================================================"
echo

# Run the comprehensive Python analyzer
if [[ -n "$SINCE_DATE" ]]; then
    python3 "$PYTHON_SCRIPT" "$SINCE_DATE"
else
    python3 "$PYTHON_SCRIPT"
fi

echo
echo "========================================================================"
echo "📊 Lines of Code Breakdown (mvp_site directory)"
echo "========================================================================"

# Function to count lines in files
count_lines() {
    local pattern="$1"
    local files=$(find mvp_site -type f -name "$pattern" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/node_modules/*" 2>/dev/null)
    if [ -z "$files" ]; then
        echo "0"
    else
        echo "$files" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}'
    fi
}

# Function to count test vs non-test lines
count_test_vs_nontest() {
    local ext="$1"
    local test_lines=$(find mvp_site -type f -name "*.$ext" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/node_modules/*" 2>/dev/null | grep -i test | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
    local nontest_lines=$(find mvp_site -type f -name "*.$ext" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/node_modules/*" 2>/dev/null | grep -v -i test | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')

    # Handle empty results
    test_lines=${test_lines:-0}
    nontest_lines=${nontest_lines:-0}

    echo "$test_lines $nontest_lines"
}

# File extensions to track
FILE_TYPES=("py" "js" "html")

# Initialize totals
total_test_lines=0
total_nontest_lines=0
total_all_lines=0

# Associative arrays for storing results
declare -A test_lines_by_type
declare -A nontest_lines_by_type
declare -A total_lines_by_type

# Calculate lines for each file type
for ext in "${FILE_TYPES[@]}"; do
    read test_count nontest_count <<< $(count_test_vs_nontest "$ext")
    test_lines_by_type[$ext]=$test_count
    nontest_lines_by_type[$ext]=$nontest_count
    total_lines_by_type[$ext]=$((test_count + nontest_count))

    total_test_lines=$((total_test_lines + test_count))
    total_nontest_lines=$((total_nontest_lines + nontest_count))
    total_all_lines=$((total_all_lines + test_count + nontest_count))
done

# Display results by file type
echo "📈 Breakdown by File Type:"
echo "-----------------------------------"
printf "%-12s %10s %10s %10s %8s\n" "Type" "Test" "Non-Test" "Total" "Test %"
echo "-----------------------------------"

for ext in "${FILE_TYPES[@]}"; do
    test_count=${test_lines_by_type[$ext]}
    nontest_count=${nontest_lines_by_type[$ext]}
    total_count=${total_lines_by_type[$ext]}

    if [ $total_count -gt 0 ]; then
        test_percentage=$(( (test_count * 100) / total_count ))
    else
        test_percentage=0
    fi

    case $ext in
        py) type_name="Python" ;;
        js) type_name="JavaScript" ;;
        html) type_name="HTML" ;;
        *) type_name="$ext" ;;
    esac

    printf "%-12s %10d %10d %10d %7d%%\n" "$type_name" "$test_count" "$nontest_count" "$total_count" "$test_percentage"
done

echo "-----------------------------------"
printf "%-12s %10d %10d %10d %7d%%\n" "TOTAL" "$total_test_lines" "$total_nontest_lines" "$total_all_lines" "$(( (total_test_lines * 100) / total_all_lines ))"
echo "========================================================================"
