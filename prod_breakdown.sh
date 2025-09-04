#!/bin/bash

echo "🏭 PRODUCTION CODE BREAKDOWN (Non-Test Only)"
echo "============================================="
echo ""

./simple_loc.sh | grep -E "^\./.*:" | while read line; do
    dir=$(echo "$line" | cut -d: -f1)

    # Extract non-test counts from format: (py:non-test/test js:non-test/test html:non-test/test)
    py_prod=$(echo "$line" | sed 's/.*py:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    js_prod=$(echo "$line" | sed 's/.*js:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    html_prod=$(echo "$line" | sed 's/.*html:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)

    total_prod=$((py_prod + js_prod + html_prod))

    if [[ $total_prod -gt 0 ]]; then
        printf "%-35s: %6d lines (py:%5d js:%5d html:%5d)\n" "$dir" "$total_prod" "$py_prod" "$js_prod" "$html_prod"
    fi
done | sort -k3 -nr

echo ""
echo "📊 PRODUCTION CODE BY FUNCTIONALITY:"
echo "===================================="

# Categorize by functionality
./simple_loc.sh | grep -E "^\./.*:" | while read line; do
    dir=$(echo "$line" | cut -d: -f1)
    py_prod=$(echo "$line" | sed 's/.*py:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    js_prod=$(echo "$line" | sed 's/.*js:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    html_prod=$(echo "$line" | sed 's/.*html:\([0-9]*\)\/.*/\1/' | grep -E '^[0-9]+$' || echo 0)
    total_prod=$((py_prod + js_prod + html_prod))

    if [[ $total_prod -gt 0 ]]; then
        # Categorize directories by functionality
        case "$dir" in
            "./mvp_site"*) category="🎯 Core Application" ;;
            "./orchestration"*) category="🤖 Task Management" ;;
            "./scripts"*) category="🛠️ Automation Scripts" ;;
            "./.claude"*) category="🤖 AI Assistant" ;;
            "./prototype"*) category="🧪 Prototypes" ;;
            "./roadmap"*) category="📋 Planning" ;;
            "./ajax-chat"*|"./gemini-demo"*) category="🔬 Demos" ;;
            "./claude-bot"*|"./mcp_servers"*) category="🤖 AI Assistant" ;;
            "./venv"*) category="🐍 Environment" ;;
            *) category="🔧 Other" ;;
        esac

        echo "$category|$total_prod|$py_prod|$js_prod|$html_prod"
    fi
done | sort -t'|' -k2 -nr | awk -F'|' '
BEGIN {
    current_cat = ""
    cat_total_py = 0
    cat_total_js = 0
    cat_total_html = 0
    cat_total = 0
}
{
    if ($1 != current_cat) {
        if (current_cat != "") {
            printf "  TOTAL: %6d lines (py:%5d js:%5d html:%5d)\n\n", cat_total, cat_total_py, cat_total_js, cat_total_html
        }
        current_cat = $1
        print current_cat
        cat_total = 0
        cat_total_py = 0
        cat_total_js = 0
        cat_total_html = 0
    }
    cat_total += $2
    cat_total_py += $3
    cat_total_js += $4
    cat_total_html += $5
}
END {
    if (current_cat != "") {
        printf "  TOTAL: %6d lines (py:%5d js:%5d html:%5d)\n", cat_total, cat_total_py, cat_total_js, cat_total_html
    }
}'
