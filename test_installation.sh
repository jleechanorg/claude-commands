#!/bin/bash
# test_installation.sh - Local installation test script

# Graceful error handling - track failures instead of exiting
FAILED_TESTS=0
TOTAL_TESTS=0

# Verify we're in the repository root
ROOT_CHECK_FAILED=0
if [ ! -f "CLAUDE.md" ] || [ ! -d ".claude/commands" ]; then
    echo "⚠️  Warning: This script should be run from the repository root"
    echo "Looking for CLAUDE.md and .claude/commands directory..."
    # Try to find project root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$SCRIPT_DIR/CLAUDE.md" ]; then
        if ! cd "$SCRIPT_DIR"; then
            echo "❌ Cannot change to script directory"
            read -p "Press Enter to continue..."
            ROOT_CHECK_FAILED=1
        fi
    else
        echo "❌ Cannot find repository root. Please run from project root directory."
        read -p "Press Enter to continue..."
        ROOT_CHECK_FAILED=1
    fi
fi

if [ "$ROOT_CHECK_FAILED" -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "Skipping remaining tests due to missing repository root."
else
echo "🧪 Testing Claude Commands Installation"
echo "========================================"
echo ""

# Test 1: Validate JSON files
echo "✓ Test 1: Validating JSON configuration files..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if python3 -m json.tool .claude-plugin/plugin.json > /dev/null 2>&1; then
    echo "  ✅ plugin.json is valid JSON"
else
    echo "  ❌ plugin.json is invalid JSON"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

if python3 -m json.tool .claude-plugin/marketplace.json > /dev/null 2>&1; then
    echo "  ✅ marketplace.json is valid JSON"
else
    echo "  ❌ marketplace.json is invalid JSON"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 2: Check required fields in plugin.json
echo ""
echo "✓ Test 2: Checking required fields in plugin.json..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
REQUIRED_FIELDS=("name" "description" "version" "author" "repository" "license")
MISSING_FIELDS=0
for field in "${REQUIRED_FIELDS[@]}"; do
    if python3 -c "import json; data=json.load(open('.claude-plugin/plugin.json')); exit(0 if '$field' in data else 1)" 2>/dev/null; then
        echo "  ✅ Field '$field' exists"
    else
        echo "  ❌ Field '$field' missing"
        MISSING_FIELDS=$((MISSING_FIELDS + 1))
    fi
done
if [ "$MISSING_FIELDS" -gt 0 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 3: Verify command directory structure
echo ""
echo "✓ Test 3: Verifying command directory structure..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -d ".claude/commands" ]; then
    echo "  ✅ .claude/commands/ directory exists"
else
    echo "  ❌ .claude/commands/ directory not found"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 4: Count available commands
echo ""
echo "✓ Test 4: Counting available commands..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
MD_COUNT=$(find .claude/commands/ -name "*.md" -type f 2>/dev/null | wc -l)
PY_COUNT=$(find .claude/commands/ -name "*.py" -type f 2>/dev/null | wc -l)
echo "  ✅ Found $MD_COUNT markdown command files"
echo "  ✅ Found $PY_COUNT Python script files"

if [ "$MD_COUNT" -lt 145 ]; then
    echo "  ⚠️  Warning: Expected 145+ commands, found $MD_COUNT"
fi

# Test 5: Verify key commands exist
echo ""
echo "✓ Test 5: Verifying key commands exist..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
KEY_COMMANDS=("pr" "copilot" "execute" "orch" "test" "debug" "think")
MISSING_COMMANDS=0
for cmd in "${KEY_COMMANDS[@]}"; do
    if [ -f ".claude/commands/${cmd}.md" ] || [ -f ".claude/commands/${cmd}.py" ]; then
        echo "  ✅ Command /$cmd exists"
    else
        echo "  ⚠️  Warning: Command /$cmd not found"
        MISSING_COMMANDS=$((MISSING_COMMANDS + 1))
    fi
done
if [ "$MISSING_COMMANDS" -gt 0 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 6: Check INSTALL.md exists
echo ""
echo "✓ Test 6: Checking installation documentation..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "INSTALL.md" ]; then
    echo "  ✅ INSTALL.md exists"
else
    echo "  ❌ INSTALL.md not found"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 7: Verify GitHub CLI instructions in CLAUDE.md
echo ""
echo "✓ Test 7: Verifying GitHub CLI instructions..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if grep -q "GITHUB CLI (gh) INSTALLATION" CLAUDE.md 2>/dev/null; then
    echo "  ✅ GitHub CLI installation instructions found in CLAUDE.md"
else
    echo "  ❌ GitHub CLI instructions missing from CLAUDE.md"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 8: Simulate plugin structure check
echo ""
echo "✓ Test 8: Simulating plugin structure validation..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['name'])" 2>/dev/null) && \
   PLUGIN_VERSION=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])" 2>/dev/null); then
    echo "  ✅ Plugin Name: $PLUGIN_NAME"
    echo "  ✅ Plugin Version: $PLUGIN_VERSION"
else
    echo "  ❌ Cannot read plugin metadata"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 9: Check marketplace configuration
echo ""
echo "✓ Test 9: Checking marketplace configuration..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if MARKETPLACE_PLUGIN_COUNT=$(python3 -c "import json; print(len(json.load(open('.claude-plugin/marketplace.json'))['plugins']))" 2>/dev/null); then
    echo "  ✅ Marketplace contains $MARKETPLACE_PLUGIN_COUNT plugin(s)"
    if [ "$MARKETPLACE_PLUGIN_COUNT" -lt 1 ]; then
        echo "  ❌ Marketplace must contain at least 1 plugin"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo "  ❌ Cannot read marketplace configuration"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 10: Test command file accessibility (both .md and .py files)
echo ""
echo "✓ Test 10: Testing command file accessibility..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
UNREADABLE=0

# Check .md files
shopt -s nullglob  # Enable nullglob to handle no matches gracefully
MD_FILES=(.claude/commands/*.md)
if [ ${#MD_FILES[@]} -eq 0 ]; then
    echo "  ⚠️  Warning: No .md files found in .claude/commands/"
else
    for cmd_file in "${MD_FILES[@]}"; do
        if [ ! -r "$cmd_file" ]; then
            echo "  ❌ Cannot read: $cmd_file"
            UNREADABLE=$((UNREADABLE + 1))
        fi
    done
fi

# Check .py files
PY_FILES=(.claude/commands/*.py)
if [ ${#PY_FILES[@]} -eq 0 ]; then
    echo "  ⚠️  Warning: No .py files found in .claude/commands/"
else
    for cmd_file in "${PY_FILES[@]}"; do
        if [ ! -r "$cmd_file" ]; then
            echo "  ❌ Cannot read: $cmd_file"
            UNREADABLE=$((UNREADABLE + 1))
        fi
    done
fi

shopt -u nullglob  # Disable nullglob

if [ $UNREADABLE -eq 0 ]; then
    echo "  ✅ All command files are readable (.md and .py)"
else
    echo "  ❌ Found $UNREADABLE unreadable files"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
fi

# Summary
echo ""
echo "========================================"
if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ ALL $TOTAL_TESTS TESTS PASSED!"
    echo ""
    echo "📊 Installation Summary:"
    echo "  • Plugin: ${PLUGIN_NAME:-unknown} v${PLUGIN_VERSION:-unknown}"
    echo "  • Commands: $MD_COUNT markdown, $PY_COUNT Python"
    echo "  • Configuration: Valid"
    echo "  • Documentation: Complete"
    echo ""
    echo "🚀 Ready for marketplace installation!"
    echo ""
    echo "To install:"
    echo "  /plugin marketplace add claude-commands-marketplace https://github.com/jleechanorg/claude-commands"
    echo "  /plugin install claude-commands@claude-commands-marketplace"
else
    echo "❌ TESTS FAILED: $FAILED_TESTS out of $TOTAL_TESTS tests failed"
    echo ""
    echo "Please review the errors above and fix the issues."
    echo ""
    read -p "Press Enter to continue..."
fi
