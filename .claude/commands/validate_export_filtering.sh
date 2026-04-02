#!/bin/bash
# Validation script for export filtering rules
# Tests that all project-specific content is properly filtered

echo "🔍 Validating export filtering rules..."

# Note: Removed unused TEST_DIR variable per CodeRabbit feedback

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
    if find .claude/commands -name "$file" -type f -quit | grep -q .; then
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
grep -r "worldarchitect\.ai\|\$USER\|WorldArchitect\.AI" .claude/commands --include="*.md" --include="*.py" 2>/dev/null | head -3
echo "   ... ($(grep -r "worldarchitect\.ai\|\$USER\|WorldArchitect\.AI" .claude/commands --include="*.md" --include="*.py" 2>/dev/null | wc -l) total references found)"

echo ""
echo "📁 Hardcoded user paths (should be filtered):"
grep -rE "$HOME/|/Users/\$USER/projects/worktree_ralph|projects_other/ralph|orch_worldai_ralph|worldai_genesis2|worldai_ralph2" .claude/commands --include="*.md" --include="*.py" --include="*.sh" 2>/dev/null | head -5
echo "   ... ($(grep -rE "$HOME/|/Users/\$USER/projects/worktree_ralph|projects_other/ralph|orch_worldai_ralph|worldai_genesis2|worldai_ralph2" .claude/commands --include="*.md" --include="*.py" --include="*.sh" 2>/dev/null | wc -l) total matches)"

echo ""
echo "🐍 Python sys.path modifications:"
grep -r "sys\.path\.insert.*mvp_site" .claude/commands --include="*.py"

echo ""
echo "🧪 Project-specific test commands:"
grep -r "TESTING=true python\|\$PROJECT_ROOT/test" .claude/commands --include="*.md" --include="*.sh" | head -3

echo ""
echo "🖼️ Checking for asset files (should be excluded)..."
ASSET_EXTS=("*.png" "*.jpg" "*.jpeg" "*.pdf" "*.gif" "*.webp" "*.mp4" "*.mov")
ASSET_FOUND=0
for ext in "${ASSET_EXTS[@]}"; do
    FOUND=$(find .claude orchestration automation ralph -name "$ext" -type f 2>/dev/null | head -n 5)
    if [[ -n "$FOUND" ]]; then
        echo "❌ Found asset files matching $ext (SHOULD BE EXCLUDED):"
        echo "$FOUND" | sed 's/^/  /'
        ASSET_FOUND=$((ASSET_FOUND + 1))
    fi
done

if [[ $ASSET_FOUND -eq 0 ]]; then
    echo "✅ No asset files found in code directories."
fi

echo ""
echo "✅ Export filtering validation complete!"
echo "📊 Summary:"
echo "   - Found $(find .claude/commands -name "*.sh" -not -path "*/tests/*" | wc -l) shell scripts"
echo "   - Found $(grep -r "mvp_site" .claude/commands --include="*.md" --include="*.py" | wc -l) mvp_site references"
echo "   - Found $(grep -r "worldarchitect\.ai\|\$USER\|WorldArchitect\.AI" .claude/commands --include="*.md" --include="*.py" | wc -l) personal references"

# Note: No cleanup needed since TEST_DIR was removed
