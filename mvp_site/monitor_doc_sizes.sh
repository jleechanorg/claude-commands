#!/bin/bash
# Monitor documentation file sizes to prevent API timeouts

echo "📊 Documentation Size Monitor"
echo "============================"

# Define thresholds
MAX_LINES=1500
WARNING_LINES=1000

# Function to check file
check_file() {
    local file=$1
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        if [ $lines -gt $MAX_LINES ]; then
            echo "❌ $file: $lines lines (EXCEEDS LIMIT)"
            return 1
        elif [ $lines -gt $WARNING_LINES ]; then
            echo "⚠️  $file: $lines lines (warning)"
            return 0
        else
            echo "✅ $file: $lines lines"
            return 0
        fi
    else
        echo "⏭️  $file: not found"
        return 0
    fi
}

# Check all documentation files (excluding archives folder)
# Keep in sync with test_documentation_performance.py
failed=0
check_file ".cursor/rules/rules.mdc" || failed=1
check_file ".cursor/rules/lessons.mdc" || failed=1
check_file ".cursor/rules/project_overview.md" || failed=1
check_file ".cursor/rules/planning_protocols.md" || failed=1
check_file ".cursor/rules/documentation_map.md" || failed=1
check_file ".cursor/rules/quick_reference.md" || failed=1
check_file ".cursor/rules/progress_tracking.md" || failed=1
check_file "CLAUDE.md" || failed=1

echo ""
if [ $failed -eq 0 ]; then
    echo "✅ All files within acceptable limits"
else
    echo "❌ Some files exceed size limits and may cause API timeouts!"
    echo "   Run: python3 mvp_site/test_documentation_performance.py for details"
    exit 1
fi