#!/bin/bash
# test_installation.sh - Local installation test script

set -e

echo "🧪 Testing Claude Commands Installation"
echo "========================================"
echo ""

# Test 1: Validate JSON files
echo "✓ Test 1: Validating JSON configuration files..."
python3 -m json.tool .claude-plugin/plugin.json > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ plugin.json is valid JSON"
else
    echo "  ❌ plugin.json is invalid JSON"
    exit 1
fi

python3 -m json.tool .claude-plugin/marketplace.json > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ marketplace.json is valid JSON"
else
    echo "  ❌ marketplace.json is invalid JSON"
    exit 1
fi

# Test 2: Check required fields in plugin.json
echo ""
echo "✓ Test 2: Checking required fields in plugin.json..."
REQUIRED_FIELDS=("name" "description" "version" "author" "repository" "license")
for field in "${REQUIRED_FIELDS[@]}"; do
    if python3 -c "import json; data=json.load(open('.claude-plugin/plugin.json')); exit(0 if '$field' in data else 1)"; then
        echo "  ✅ Field '$field' exists"
    else
        echo "  ❌ Field '$field' missing"
        exit 1
    fi
done

# Test 3: Verify command directory structure
echo ""
echo "✓ Test 3: Verifying command directory structure..."
if [ -d ".claude/commands" ]; then
    echo "  ✅ .claude/commands/ directory exists"
else
    echo "  ❌ .claude/commands/ directory not found"
    exit 1
fi

# Test 4: Count available commands
echo ""
echo "✓ Test 4: Counting available commands..."
MD_COUNT=$(find .claude/commands/ -name "*.md" -type f | wc -l)
PY_COUNT=$(find .claude/commands/ -name "*.py" -type f | wc -l)
echo "  ✅ Found $MD_COUNT markdown command files"
echo "  ✅ Found $PY_COUNT Python script files"

if [ "$MD_COUNT" -lt 100 ]; then
    echo "  ⚠️  Warning: Expected 145+ commands, found $MD_COUNT"
fi

# Test 5: Verify key commands exist
echo ""
echo "✓ Test 5: Verifying key commands exist..."
KEY_COMMANDS=("pr" "copilot" "execute" "orch" "test" "debug" "think")
for cmd in "${KEY_COMMANDS[@]}"; do
    if [ -f ".claude/commands/${cmd}.md" ] || [ -f ".claude/commands/${cmd}.py" ]; then
        echo "  ✅ Command /$cmd exists"
    else
        echo "  ⚠️  Warning: Command /$cmd not found"
    fi
done

# Test 6: Check INSTALL.md exists
echo ""
echo "✓ Test 6: Checking installation documentation..."
if [ -f "INSTALL.md" ]; then
    echo "  ✅ INSTALL.md exists"
else
    echo "  ❌ INSTALL.md not found"
    exit 1
fi

# Test 7: Verify GitHub CLI instructions in CLAUDE.md
echo ""
echo "✓ Test 7: Verifying GitHub CLI instructions..."
if grep -q "GITHUB CLI (gh) INSTALLATION" CLAUDE.md; then
    echo "  ✅ GitHub CLI installation instructions found in CLAUDE.md"
else
    echo "  ❌ GitHub CLI instructions missing from CLAUDE.md"
    exit 1
fi

# Test 8: Simulate plugin structure check
echo ""
echo "✓ Test 8: Simulating plugin structure validation..."
PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['name'])")
PLUGIN_VERSION=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
echo "  ✅ Plugin Name: $PLUGIN_NAME"
echo "  ✅ Plugin Version: $PLUGIN_VERSION"

# Test 9: Check marketplace configuration
echo ""
echo "✓ Test 9: Checking marketplace configuration..."
MARKETPLACE_PLUGIN_COUNT=$(python3 -c "import json; print(len(json.load(open('.claude-plugin/marketplace.json'))['plugins']))")
echo "  ✅ Marketplace contains $MARKETPLACE_PLUGIN_COUNT plugin(s)"

if [ "$MARKETPLACE_PLUGIN_COUNT" -lt 1 ]; then
    echo "  ❌ Marketplace must contain at least 1 plugin"
    exit 1
fi

# Test 10: Test command accessibility
echo ""
echo "✓ Test 10: Testing command file accessibility..."
UNREADABLE=0
for cmd_file in .claude/commands/*.md; do
    if [ ! -r "$cmd_file" ]; then
        echo "  ❌ Cannot read: $cmd_file"
        UNREADABLE=$((UNREADABLE + 1))
    fi
done

if [ $UNREADABLE -eq 0 ]; then
    echo "  ✅ All command files are readable"
else
    echo "  ❌ Found $UNREADABLE unreadable files"
    exit 1
fi

# Summary
echo ""
echo "========================================"
echo "✅ ALL TESTS PASSED!"
echo ""
echo "📊 Installation Summary:"
echo "  • Plugin: $PLUGIN_NAME v$PLUGIN_VERSION"
echo "  • Commands: $MD_COUNT markdown, $PY_COUNT Python"
echo "  • Configuration: Valid"
echo "  • Documentation: Complete"
echo ""
echo "🚀 Ready for marketplace installation!"
echo ""
echo "To install:"
echo "  /plugin marketplace add claude-commands-marketplace https://github.com/jleechanorg/claude-commands"
echo "  /plugin install claude-commands@claude-commands-marketplace"
