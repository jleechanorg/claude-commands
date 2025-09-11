#!/bin/bash

# Simple Lines of Code Counter - Accurate Production vs Test breakdown
# Excludes: venv/, roadmap/ (planning docs), and other non-production directories

echo "📊 Lines of Code Count (Production Focus)"
echo "=========================================="

# Function to count lines with proper exclusions
count_files() {
    local ext="$1"
    local test_filter="$2"

    if [[ "$test_filter" == "test" ]]; then
        find . -name "*.$ext" \( -path "*/test*" -o -name "*test*.$ext" \) \
            | grep -v node_modules | grep -v .git | grep -v venv | grep -v __pycache__ | grep -v tmp/ \
            | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0
    else
        find . -name "*.$ext" ! -path "*/test*" ! -name "*test*.$ext" \
            | grep -v node_modules | grep -v .git | grep -v venv | grep -v __pycache__ | grep -v tmp/ \
            | grep -v roadmap/ \
            | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0
    fi
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
    test_percentage=$(echo "scale=1; $total_test * 100 / $total_all" | bc -l 2>/dev/null || echo "0")
    echo "  Test Coverage:   ${test_percentage}%"
fi

echo ""
echo "🎯 Production Code by Functionality:"
echo "===================================="

# Count major functional areas (production only)
count_functional_area() {
    local pattern="$1"
    local name="$2"

    py_count=$(find . -name "*.py" -path "*$pattern*" ! -path "*/test*" ! -name "*test*.py" \
        | grep -v node_modules | grep -v .git | grep -v venv | grep -v roadmap/ \
        | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)

    js_count=$(find . -name "*.js" -path "*$pattern*" ! -path "*/test*" ! -name "*test*.js" \
        | grep -v node_modules | grep -v .git | grep -v venv \
        | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)

    html_count=$(find . -name "*.html" -path "*$pattern*" ! -path "*/test*" ! -name "*test*.html" \
        | grep -v node_modules | grep -v .git | grep -v venv \
        | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)

    total=$((py_count + js_count + html_count))

    if [[ $total -gt 0 ]]; then
        printf "  %-20s: %6d lines (py:%5d js:%4d html:%4d)\n" "$name" "$total" "$py_count" "$js_count" "$html_count"
    fi
}

# Major functional areas
count_functional_area "mvp_site" "Core Application"
count_functional_area "scripts" "Automation Scripts"
count_functional_area ".claude" "AI Assistant"
count_functional_area "orchestration" "Task Management"
count_functional_area "prototype" "Prototypes"
count_functional_area "testing_" "Test Infrastructure"

echo ""
echo "ℹ️  Exclusions:"
echo "  • Virtual environment (venv/)"
echo "  • Planning documents (roadmap/)"
echo "  • Node modules, git files"
echo "  • Temporary and cache files"
