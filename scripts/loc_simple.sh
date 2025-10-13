#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

# Simple Lines of Code Counter - Accurate Production vs Test breakdown
# Excludes: venv/, roadmap/ (planning docs), and other non-production directories

echo "📊 Lines of Code Count (Production Focus)"
echo "=========================================="

# Function to count lines with proper exclusions
count_files() {
    local ext="$1"
    local mode="$2"
    local scope_pattern="${3:-}"

    local -a find_args=(
        find .
        -type f
        -name "*.${ext}"
        ! -path "*/node_modules/*"
        ! -path "*/.git/*"
        ! -path "*/venv/*"
        ! -path "*/__pycache__/*"
        ! -path "./tmp/*"
        ! -path "./roadmap/*"
    )

    if [[ -n "$scope_pattern" ]]; then
        local scope_glob="$scope_pattern"

        if [[ "$scope_glob" != ./* && "$scope_glob" != /* ]]; then
            scope_glob="./${scope_glob#./}"
        fi

        if [[ "$scope_glob" != *\** ]]; then
            scope_glob="${scope_glob%/}/*"
        elif [[ "$scope_glob" == */ ]]; then
            scope_glob="${scope_glob}*"
        fi

        find_args+=( -path "$scope_glob" )
    fi

    local -a test_selector=(
        \( -path "*/tests/*"
        -o -path "*/test/*"
        -o -path "*/testing/*"
        -o -path "*/spec/*"
        -o -name "test_*.${ext}"
        -o -name "*_test.${ext}"
        -o -name "*_tests.${ext}"
        -o -name "*.test.${ext}"
        -o -name "*.spec.${ext}"
        \)
    )

    local count
    if [[ "$mode" == "test" ]]; then
        count=$(
            "${find_args[@]}" "${test_selector[@]}" -exec wc -l {} + 2>/dev/null \
                | awk '!/ total$/ {sum += $1} END {print sum+0}'
        )
    else
        count=$(
            "${find_args[@]}" ! "${test_selector[@]}" -exec wc -l {} + 2>/dev/null \
                | awk '!/ total$/ {sum += $1} END {print sum+0}'
        )
    fi

    echo "${count:-0}"
}

# Overall language totals
echo "🐍 Python (.py):"
py_prod=$(count_files "py" "prod")
py_test=$(count_files "py" "test")
echo "  Production: ${py_prod:-0} lines"
echo "  Test:       ${py_test:-0} lines"

echo "🌟 JavaScript (.js):"
js_prod=$(count_files "js" "prod")
js_test=$(count_files "js" "test")
echo "  Production: ${js_prod:-0} lines"
echo "  Test:       ${js_test:-0} lines"

echo "🌐 HTML (.html):"
html_prod=$(count_files "html" "prod")
html_test=$(count_files "html" "test")
echo "  Production: ${html_prod:-0} lines"
echo "  Test:       ${html_test:-0} lines"

# Summary
echo ""
echo "📋 Summary:"
total_prod=$((${py_prod:-0} + ${js_prod:-0} + ${html_prod:-0}))
total_test=$((${py_test:-0} + ${js_test:-0} + ${html_test:-0}))
total_all=$((total_prod + total_test))

echo "  Production Code: $total_prod lines"
echo "  Test Code:       $total_test lines"
echo "  TOTAL CODEBASE:  $total_all lines"

if [[ $total_all -gt 0 ]]; then
    test_percentage=$(awk -v test="$total_test" -v all="$total_all" 'BEGIN {if (all > 0) printf "%.1f", test * 100 / all; else print "0"}')
    echo "  Test LOC share:  ${test_percentage}%"
fi

echo ""
echo "🎯 Production Code by Functionality:"
echo "===================================="

# Count major functional areas (production only)
count_functional_area() {
    local pattern="$1"
    local name="$2"

    py_count=$(count_files "py" "prod" "$pattern")
    js_count=$(count_files "js" "prod" "$pattern")
    html_count=$(count_files "html" "prod" "$pattern")

    total=$((py_count + js_count + html_count))

    if [[ $total -gt 0 ]]; then
        printf "  %-20s: %6d lines (py:%5d js:%4d html:%4d)\n" "$name" "$total" "$py_count" "$js_count" "$html_count"
    fi
}

# Major functional areas
count_functional_area "./mvp_site/" "Core Application"
count_functional_area "./scripts/" "Automation Scripts"
count_functional_area "./.claude/" "AI Assistant"
count_functional_area "./orchestration/" "Task Management"
count_functional_area "./prototype*/" "Prototypes"
count_functional_area "./testing_*/" "Test Infrastructure"

echo ""
echo "ℹ️  Exclusions:"
echo "  • Virtual environment (venv/)"
echo "  • Planning documents (roadmap/)"
echo "  • Node modules, git files"
echo "  • Temporary and cache files"
