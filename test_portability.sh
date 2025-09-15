#!/bin/bash
# Test script to verify infrastructure portability improvements

echo "🧪 Testing Infrastructure Script Portability"
echo "=============================================="

# Test 1: Configuration file detection
echo "📝 Test 1: Configuration file support"
if [[ -f ".infrastructure.conf.example" ]]; then
    echo "✅ Configuration template exists"
else
    echo "❌ Configuration template missing"
fi

if [[ -f "infrastructure_common.sh" ]]; then
    echo "✅ Common infrastructure functions exist"
    # Test sourcing the common functions
    if source infrastructure_common.sh 2>/dev/null; then
        echo "✅ Common functions can be sourced"
    else
        echo "❌ Common functions have syntax errors"
    fi
else
    echo "❌ Common infrastructure functions missing"
fi

# Test 2: Auto-detection functions
echo ""
echo "🔍 Test 2: Auto-detection mechanisms"
if source infrastructure_common.sh 2>/dev/null; then
    PROJECT_NAME=$(detect_project_name)
    SOURCE_DIR=$(detect_source_directory)
    REPO_URL=$(detect_repo_url)
    EMAIL=$(detect_email)

    echo "✅ Project name detected: $PROJECT_NAME"
    echo "✅ Source directory detected: $SOURCE_DIR"
    echo "✅ Repository URL detected: ${REPO_URL:-<not in git repo>}"
    echo "✅ Email detected: ${EMAIL:-<not configured>}"
else
    echo "❌ Auto-detection functions failed"
fi

# Test 3: Enhanced scripts check for portability patterns
echo ""
echo "🔧 Test 3: Enhanced script portability"

scripts_to_check=(
    "setup_email.sh"
    "setup-github-runner.sh"
    "push.sh"
    "loc.sh"
    "run_tests_with_coverage.sh"
)

for script in "${scripts_to_check[@]}"; do
    if [[ -f "$script" ]]; then
        echo "📄 Checking $script:"

        # Check for hardcoded paths/emails
        if grep -q "jleechantest@gmail.com" "$script" 2>/dev/null; then
            echo "   ❌ Still contains hardcoded email"
        else
            echo "   ✅ No hardcoded email found"
        fi

        if grep -q "~/worldarchitect.ai\|~/your-project.com" "$script" 2>/dev/null; then
            echo "   ❌ Still contains hardcoded project paths"
        else
            echo "   ✅ No hardcoded project paths found"
        fi

        # Check for git-based detection
        if grep -q "git rev-parse\|git config" "$script" 2>/dev/null; then
            echo "   ✅ Uses git-based auto-detection"
        else
            echo "   ⚠️  No git-based detection found"
        fi

    else
        echo "📄 $script: ❌ Not found"
    fi
done

echo ""
echo "🎯 Portability Test Complete"
echo "=============================================="
