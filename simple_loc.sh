#!/bin/bash

# Simple Lines of Code Counter - Test vs Non-Test breakdown with directory analysis
echo "📊 Simple Lines of Code Count"
echo "============================="

# Function to count lines in a directory
count_dir_lines() {
    local dir="$1"
    local ext="$2"
    local test_filter="$3"

    if [[ "$test_filter" == "test" ]]; then
        find "$dir" -maxdepth 1 -name "*.$ext" \( -name "*test*.$ext" -o -path "*/test*" \) 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0
    else
        find "$dir" -maxdepth 1 -name "*.$ext" ! -name "*test*.$ext" ! -path "*/test*" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0
    fi
}

# Overall totals
echo "🐍 Python (.py):"
py_non_test=$(find . -name "*.py" ! -path "*/test*" ! -name "*test*.py" | grep -v node_modules | grep -v .git | grep -v venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
py_test=$(find . -name "*.py" \( -path "*/test*" -o -name "*test*.py" \) | grep -v node_modules | grep -v .git | grep -v venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
echo "  Non-test: ${py_non_test:-0} lines"
echo "  Test:     ${py_test:-0} lines"

echo "🌟 JavaScript (.js):"
js_non_test=$(find . -name "*.js" ! -path "*/test*" ! -name "*test*.js" | grep -v node_modules | grep -v .git | grep -v venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
js_test=$(find . -name "*.js" \( -path "*/test*" -o -name "*test*.js" \) | grep -v node_modules | grep -v .git | grep -v venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
echo "  Non-test: ${js_non_test:-0} lines"
echo "  Test:     ${js_test:-0} lines"

echo "🌐 HTML (.html):"
html_non_test=$(find . -name "*.html" ! -path "*/test*" ! -name "*test*.html" | grep -v node_modules | grep -v .git | grep -v venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
html_test=$(find . -name "*.html" \( -path "*/test*" -o -name "*test*.html" \) | grep -v node_modules | grep -v .git | grep -v venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
echo "  Non-test: ${html_non_test:-0} lines"
echo "  Test:     ${html_test:-0} lines"

# Summary
echo ""
echo "📋 Overall Summary:"
total_non_test=$((${py_non_test:-0} + ${js_non_test:-0} + ${html_non_test:-0}))
total_test=$((${py_test:-0} + ${js_test:-0} + ${html_test:-0}))
total_all=$((total_non_test + total_test))

echo "  Total Non-Test: $total_non_test lines"
echo "  Total Test:     $total_test lines"
echo "  GRAND TOTAL:    $total_all lines"

# Directory breakdown
echo ""
echo "📁 Directory Breakdown:"
echo "======================="

# Get top-level directories with code files
dirs=$(find . -maxdepth 2 -type d ! -name "." ! -name ".git" ! -name "node_modules" ! -name "__pycache__" ! -path "./tmp*" | sort)

for dir in $dirs; do
    dir_py_non=$(find "$dir" -maxdepth 1 -name "*.py" ! -name "*test*.py" 2>/dev/null | grep -v venv | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    dir_py_test=$(find "$dir" -maxdepth 1 -name "*test*.py" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    dir_js_non=$(find "$dir" -maxdepth 1 -name "*.js" ! -name "*test*.js" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    dir_js_test=$(find "$dir" -maxdepth 1 -name "*test*.js" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    dir_html_non=$(find "$dir" -maxdepth 1 -name "*.html" ! -name "*test*.html" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    dir_html_test=$(find "$dir" -maxdepth 1 -name "*test*.html" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)

    dir_total=$((${dir_py_non:-0} + ${dir_py_test:-0} + ${dir_js_non:-0} + ${dir_js_test:-0} + ${dir_html_non:-0} + ${dir_html_test:-0}))

    if [[ $dir_total -gt 0 ]]; then
        printf "%-30s: %8d lines (py:%d/%d js:%d/%d html:%d/%d)\n" \
               "$dir" "$dir_total" \
               "${dir_py_non:-0}" "${dir_py_test:-0}" \
               "${dir_js_non:-0}" "${dir_js_test:-0}" \
               "${dir_html_non:-0}" "${dir_html_test:-0}"
    fi
done
