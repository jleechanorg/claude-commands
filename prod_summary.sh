#!/bin/bash

echo "🏭 PRODUCTION CODE BY FUNCTIONALITY"
echo "==================================="

# Create temporary file for processing
temp_file=$(mktemp)

./simple_loc.sh | grep -E "^\./.*:" | while read line; do
    dir=$(echo "$line" | cut -d: -f1)
    py_prod=$(echo "$line" | sed 's/.*py:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    js_prod=$(echo "$line" | sed 's/.*js:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    html_prod=$(echo "$line" | sed 's/.*html:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    total_prod=$((py_prod + js_prod + html_prod))

    if [[ $total_prod -gt 0 ]]; then
        # Categorize directories
        case "$dir" in
            "./mvp_site"*) category="Core Application" ;;
            "./orchestration"*) category="Task Management" ;;
            "./scripts"*) category="Automation Scripts" ;;
            "./.claude"*) category="AI Assistant" ;;
            "./prototype"*) category="Prototypes" ;;
            "./roadmap"*) category="Planning" ;;
            "./ajax-chat"*|"./gemini-demo"*) category="Demos" ;;
            "./claude-bot"*|"./mcp_servers"*) category="AI Assistant" ;;
            "./testing_"*) category="Testing Infrastructure" ;;
            "./venv"*) category="Environment" ;;
            *) category="Other" ;;
        esac

        echo "$category $total_prod $py_prod $js_prod $html_prod"
    fi
done > "$temp_file"

# Process and sum by category
declare -A cat_totals
declare -A cat_py
declare -A cat_js
declare -A cat_html

while read category total py js html; do
    cat_totals["$category"]=$((${cat_totals["$category"]} + total))
    cat_py["$category"]=$((${cat_py["$category"]} + py))
    cat_js["$category"]=$((${cat_js["$category"]} + js))
    cat_html["$category"]=$((${cat_html["$category"]} + html))
done < "$temp_file"

# Sort and display
for category in "${!cat_totals[@]}"; do
    printf "%s|%d|%d|%d|%d\n" "$category" "${cat_totals[$category]}" "${cat_py[$category]}" "${cat_js[$category]}" "${cat_html[$category]}"
done | sort -t'|' -k2 -nr | while IFS='|' read category total py js html; do
    printf "🎯 %-20s: %6d lines (py:%5d js:%5d html:%5d)\n" "$category" "$total" "$py" "$js" "$html"
done

rm "$temp_file"

echo ""
echo "📊 PRODUCTION CODE TOTALS BY LANGUAGE:"
echo "======================================"

# Get overall totals from simple_loc.sh
py_total=$(./simple_loc.sh | grep "Non-test:" | head -1 | awk '{print $2}')
js_total=$(./simple_loc.sh | grep "Non-test:" | head -2 | tail -1 | awk '{print $2}')
html_total=$(./simple_loc.sh | grep "Non-test:" | tail -1 | awk '{print $2}')
overall_total=$(./simple_loc.sh | grep "Total Non-Test:" | awk '{print $3}')

printf "🐍 Python:    %6d lines (%.1f%%)\n" "$py_total" "$(echo "scale=1; $py_total * 100 / $overall_total" | bc)"
printf "🌟 JavaScript: %6d lines (%.1f%%)\n" "$js_total" "$(echo "scale=1; $js_total * 100 / $overall_total" | bc)"
printf "🌐 HTML:       %6d lines (%.1f%%)\n" "$html_total" "$(echo "scale=1; $html_total * 100 / $overall_total" | bc)"
printf "📋 TOTAL:      %6d lines\n" "$overall_total"
