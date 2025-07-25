#!/bin/bash

# ==============================================================================
# Enhanced Line Counter Script
#
# Description:
# This script provides comprehensive line count analysis for a codebase:
# 1. Total lines by file type (.py, .js, .html)
# 2. Test vs non-test code breakdown
# 3. Git contribution analysis by author (optional)
#
# Usage:
# ./loc.sh                  # Show codebase statistics
# ./loc.sh --git            # Include git contribution analysis
# ./loc.sh --git <email>    # Git analysis for specific author
# ./loc.sh --help           # Show this help
# ==============================================================================

# --- Configuration ---

# File extensions to track. Add or remove types as needed.
FILE_TYPES=("py" "js" "html")

# Time frame for the log search.
TIME_FRAME="1 month ago"

# Parse command line arguments
SHOW_GIT_STATS=false
AUTHOR_EMAIL=""
TARGET_DIR="mvp_site"

while [[ $# -gt 0 ]]; do
    case $1 in
        --git)
            SHOW_GIT_STATS=true
            shift
            if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
                AUTHOR_EMAIL="$1"
                shift
            fi
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --git          Include git contribution analysis"
            echo "  --git <email>  Git analysis for specific author"
            echo "  --help         Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# --- Main Analysis Functions ---

# Function to count lines in files
count_lines() {
    local pattern="$1"
    local files=$(find "$TARGET_DIR" -type f -name "$pattern" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/node_modules/*" 2>/dev/null)
    if [ -z "$files" ]; then
        echo "0"
    else
        echo "$files" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}'
    fi
}

# Function to count test vs non-test lines
count_test_vs_nontest() {
    local ext="$1"
    local test_lines=$(find "$TARGET_DIR" -type f -name "*.$ext" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/node_modules/*" 2>/dev/null | grep -i test | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
    local nontest_lines=$(find "$TARGET_DIR" -type f -name "*.$ext" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/node_modules/*" 2>/dev/null | grep -v -i test | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')

    # Handle empty results
    test_lines=${test_lines:-0}
    nontest_lines=${nontest_lines:-0}

    echo "$test_lines $nontest_lines"
}

# --- Codebase Statistics ---

echo "📊 Codebase Statistics for $TARGET_DIR"
echo "========================================================================"
echo ""

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

# --- Git Statistics (optional) ---

if [ "$SHOW_GIT_STATS" = true ]; then
    echo ""
    echo "📊 Git Contribution Analysis"
    echo "========================================================================"

    # Determine author email
    if [ -z "$AUTHOR_EMAIL" ]; then
        AUTHOR_EMAIL=$(git config user.email)
    fi

    if [ -z "$AUTHOR_EMAIL" ]; then
        echo "Error: Could not determine Git author email."
        echo "Please specify with: ./loc.sh --git <email>"
        exit 1
    fi

    echo "Author: $AUTHOR_EMAIL"
    echo "Since: $TIME_FRAME"
    echo "-----------------------------------"

    # Initialize git stats
    git_total=0
    declare -A git_lines_by_type

    # Calculate git contributions
    for ext in "${FILE_TYPES[@]}"; do
        lines_added=$(git log --author="$AUTHOR_EMAIL" --since="$TIME_FRAME" --pretty=tformat: --numstat -- "*.$ext" | awk '{s+=$1} END {print s+0}')
        git_lines_by_type[$ext]=$lines_added
        git_total=$((git_total + lines_added))
    done

    # Display git results
    printf "%-15s: %d lines\n" "Python (.py)" "${git_lines_by_type[py]}"
    printf "%-15s: %d lines\n" "JavaScript (.js)" "${git_lines_by_type[js]}"
    printf "%-15s: %d lines\n" "HTML (.html)" "${git_lines_by_type[html]}"
    echo "-----------------------------------"
    printf "✅ Total Lines Added: %d lines\n" "$git_total"
    echo "========================================================================"
fi
