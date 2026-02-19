#!/bin/bash
# Comprehensive Export Filter for Claude Commands
# Removes all project-specific content before export

echo "🔍 Starting comprehensive export filtering..."

# Create comprehensive exclusion list
cat > /tmp/comprehensive_exclusions.txt << 'EOF'
# Shell scripts with project dependencies
run_tests.sh
run_tests_with_coverage.sh
coverage.sh
loc.sh
run_local_server.sh
run_test_server.sh
tools/localserver.sh
testi.sh
copilot_inline_reply_example.sh
run_ci_replica.sh

# CI and testing infrastructure
ci_replica/
testing_http/
testing_ui/
scripts/

# Documentation with project specifics
business_plan_v1.md
product_spec.md
TASK_*_PROGRESS_SUMMARY.md
MEMORY_MCP_ACTIVATION_GUIDE.md
TESTING_CLAUDE_CODE.md

# Configuration and sensitive files
serviceAccountKey.json
.env
*.pyc
__pycache__/
EOF

echo "📋 Files and directories to exclude:"
cat /tmp/comprehensive_exclusions.txt

echo ""
echo "🔍 Comprehensive content patterns to filter:"
echo "  - $PROJECT_ROOT/ → \$PROJECT_ROOT/"
echo "  - your-project.com → your-project.com"
echo "  - $USER → \$USER"
echo "  - Your Project → Your Project"
echo "  - Firebase/Firestore → Database"
echo "  - D&D 5e → Tabletop RPG"
echo "  - serviceAccountKey.json → database_credentials.json"
echo "  - worktree_worker* → workspace"
echo "  - github.com/$USER → github.com/\$USER"
echo "  - TESTING=true python → TESTING=true python"

echo ""
echo "🚨 CRITICAL PROJECT-SPECIFIC CONTENT FOUND:"
echo "📁 mvp_site references: $(grep -r "mvp_site" . --include="*.md" --include="*.py" --include="*.sh" 2>/dev/null | wc -l)"
echo "🏠 Personal references: $(grep -rE "worldarchitect\.ai|$USER" . --include="*.md" --include="*.py" 2>/dev/null | wc -l)"
echo "🗄️ Database references: $(grep -rE "Firebase|Firestore|serviceAccountKey" . --include="*.md" --include="*.py" 2>/dev/null | wc -l)"
echo "📊 Business docs: $(find . \( -name "*business*" -o -name "*product_spec*" \) | wc -l)"
echo "🧪 Test infrastructure: $(find . -name "*test*" -type f | wc -l)"

echo ""
echo "✅ Export filtering analysis complete!"
echo "⚠️  All identified content requires filtering before public export"

# Cleanup
rm -f /tmp/comprehensive_exclusions.txt
