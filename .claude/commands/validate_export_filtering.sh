#!/bin/bash
# Validation script for export filtering rules
# Tests that all project-specific content is properly filtered

echo "🔍 Validating export filtering rules..."

# Create temporary test directory
TEST_DIR="/tmp/export_filter_test_$(date +%s)"
mkdir -p "$TEST_DIR"

echo "📋 Checking for files that should be excluded..."

# List of files that should NOT be in public export
EXCLUDED_FILES=(
    "testi.sh"
    "run_tests.sh" 
    "copilot_inline_reply_example.sh"
    "run_ci_replica.sh"
)

echo "❌ Files that should be excluded from export:"
for file in "${EXCLUDED_FILES[@]}"; do
    if find .claude/commands -name "$file" -type f | grep -q .; then
        echo "  - $file (FOUND - should be filtered)"
    fi
done

echo ""
echo "🔍 Scanning for project-specific content that needs filtering..."

# Check for mvp_site references
echo "📁 mvp_site references:"
grep -r "mvp_site" .claude/commands --include="*.md" --include="*.py" | head -5
echo "   ... ($(grep -r "mvp_site" .claude/commands --include="*.md" --include="*.py" | wc -l) total references found)"

echo ""
echo "🏠 Personal/project references:"
grep -r "worldarchitect\.ai\|jleechan\|WorldArchitect\.AI" .claude/commands --include="*.md" --include="*.py" | head -3
echo "   ... ($(grep -r "worldarchitect\.ai\|jleechan\|WorldArchitect\.AI" .claude/commands --include="*.md" --include="*.py" | wc -l) total references found)"

echo ""
echo "🐍 Python sys.path modifications:"
grep -r "sys\.path\.insert.*mvp_site" .claude/commands --include="*.py"

echo ""
echo "🧪 Project-specific test commands:"
grep -r "TESTING=true vpython\|mvp_site/test" .claude/commands --include="*.md" --include="*.sh" | head -3

echo ""
echo "✅ Export filtering validation complete!"
echo "📊 Summary:"
echo "   - Found $(find .claude/commands -name "*.sh" -not -path "*/tests/*" | wc -l) shell scripts"
echo "   - Found $(grep -r "mvp_site" .claude/commands --include="*.md" --include="*.py" | wc -l) mvp_site references" 
echo "   - Found $(grep -r "worldarchitect\.ai\|jleechan" .claude/commands --include="*.md" --include="*.py" | wc -l) personal references"

# Cleanup
rm -rf "$TEST_DIR"