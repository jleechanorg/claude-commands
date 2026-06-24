#!/bin/bash
# test_installation.sh - Local installation test script

# Graceful error handling - track failures instead of exiting
TEST_FAILURES=0
TOTAL_TESTS=0
ROOT_CHECK_FAILED=0

# Verify we're in the repository root
if [ ! -f "CLAUDE.md" ] || [ ! -d ".claude/commands" ]; then
    echo "⚠️  Warning: This script should be run from the repository root"
    echo "Looking for CLAUDE.md and .claude/commands directory..."
    # Try to find project root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # FIX: Check for BOTH CLAUDE.md AND .claude/commands (Cursor bot issue)
    if [ -f "$SCRIPT_DIR/CLAUDE.md" ] && [ -d "$SCRIPT_DIR/.claude/commands" ]; then
        if ! cd "$SCRIPT_DIR"; then
            echo "❌ Cannot change to script directory"
            if [ -t 0 ]; then read -p "Press Enter to continue..."; fi
            ROOT_CHECK_FAILED=1
        fi
    else
        echo "❌ Cannot find repository root. Please run from project root directory."
        if [ -t 0 ]; then read -p "Press Enter to continue..."; fi
        ROOT_CHECK_FAILED=1
    fi
fi

if [ "$ROOT_CHECK_FAILED" -ne 0 ]; then
    TEST_FAILURES=$((TEST_FAILURES + 1))
fi

echo "🧪 Testing Claude Commands Installation"
echo "========================================"
echo ""

# Helper to check JSON validity
check_json() {
    local file=$1
    if command -v jq >/dev/null 2>&1; then
        jq empty "$file" >/dev/null 2>&1
        return $?
    elif command -v python3 >/dev/null 2>&1;
     then
        python3 -m json.tool "$file" >/dev/null 2>&1
        return $?
    else
        echo "  ⚠️  Skipping JSON validation (jq and python3 not available)"
        return 0 # Skip validation if tools missing
    fi
}

if [ "$ROOT_CHECK_FAILED" -eq 0 ]; then
    # Test 1: Validate JSON files
    echo "✓ Test 1: Validating JSON configuration files..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    TEST_1_FAILED=0

    if check_json ".claude-plugin/plugin.json"; then
        echo "  ✅ plugin.json is valid JSON"
    else
        echo "  ❌ plugin.json is invalid JSON"
        TEST_1_FAILED=1
    fi

    if check_json ".claude-plugin/marketplace.json"; then
        echo "  ✅ marketplace.json is valid JSON"
    else
        echo "  ❌ marketplace.json is invalid JSON"
        TEST_1_FAILED=1
    fi

    if [ $TEST_1_FAILED -eq 1 ]; then
        TEST_FAILURES=$((TEST_FAILURES + 1))
    fi

    # Test 2: Check required fields in plugin.json
    echo ""
    echo "✓ Test 2: Checking required fields in plugin.json..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    REQUIRED_FIELDS=("name" "description" "version" "author" "repository" "license")
    MISSING_FIELDS=0

    if command -v python3 >/dev/null 2>&1; then
        for field in "${REQUIRED_FIELDS[@]}"; do
            if python3 -c "import json; data=json.load(open('.claude-plugin/plugin.json')); exit(0 if '$field' in data else 1)" 2>/dev/null;
             then
                echo "  ✅ Field '$field' exists"
            else
                echo "  ❌ Field '$field' missing"
                MISSING_FIELDS=$((MISSING_FIELDS + 1))
            fi
        done
        if [ "$MISSING_FIELDS" -gt 0 ]; then
            TEST_FAILURES=$((TEST_FAILURES + 1))
        fi
    else
        echo "  ⚠️  Skipping field validation (python3 not available)"
    fi

    # Test 3: Verify command directory structure
    echo ""
    echo "✓ Test 3: Verifying command directory structure..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ -d ".claude/commands" ]; then
        echo "  ✅ .claude/commands/ directory exists"
    else
        echo "  ❌ .claude/commands/ directory not found"
        TEST_FAILURES=$((TEST_FAILURES + 1))
    fi

    # Test 4: Count available commands
    echo ""
    echo "✓ Test 4: Counting available commands..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    # Recursive count to match accessibility test
    MD_COUNT=$(find .claude/commands -name "*.md" -type f | wc -l)
    PY_COUNT=$(find .claude/commands -name "*.py" -type f | wc -l)
    echo "  ✅ Found $MD_COUNT markdown command files"
    echo "  ✅ Found $PY_COUNT Python script files"

    # Warning threshold matched to documented count
    if [ "$MD_COUNT" -lt 145 ]; then
        echo "  ❌ Expected 145+ commands, found $MD_COUNT"
        TEST_FAILURES=$((TEST_FAILURES + 1))
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
        TEST_FAILURES=$((TEST_FAILURES + 1))
    fi

    # Test 6: Check INSTALL.md exists
    echo ""
    echo "✓ Test 6: Checking installation documentation..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ -f "INSTALL.md" ]; then
        echo "  ✅ INSTALL.md exists"
    else
        echo "  ❌ INSTALL.md not found"
        TEST_FAILURES=$((TEST_FAILURES + 1))
    fi

    # Test 7: Verify GitHub CLI instructions in CLAUDE.md
    echo ""
    echo "✓ Test 7: Verifying GitHub CLI instructions..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if grep -q "GITHUB CLI (gh) INSTALLATION" CLAUDE.md 2>/dev/null;
     then
        echo "  ✅ GitHub CLI installation instructions found in CLAUDE.md"
    else
        echo "  ❌ GitHub CLI instructions missing from CLAUDE.md"
        TEST_FAILURES=$((TEST_FAILURES + 1))
    fi

    # Test 8: Simulating plugin structure check
    echo ""
    echo "✓ Test 8: Simulating plugin structure validation..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    PLUGIN_NAME=""
    PLUGIN_VERSION=""

    if command -v python3 >/dev/null 2>&1;
     then
        if PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['name'])" 2>/dev/null) && \
           PLUGIN_VERSION=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])" 2>/dev/null);
         then
            echo "  ✅ Plugin Name: $PLUGIN_NAME"
            echo "  ✅ Plugin Version: $PLUGIN_VERSION"
        else
            echo "  ❌ Cannot read plugin metadata"
            TEST_FAILURES=$((TEST_FAILURES + 1))
        fi
    else
        echo "  ⚠️  Skipping plugin metadata check (python3 not available)"
        PLUGIN_NAME="claude-commands"
        PLUGIN_VERSION="1.0.0"
    fi

    # Test 9: Check marketplace configuration
    echo ""
    echo "✓ Test 9: Checking marketplace configuration..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if command -v python3 >/dev/null 2>&1;
     then
        if MARKETPLACE_PLUGIN_COUNT=$(python3 -c "import json; print(len(json.load(open('.claude-plugin/marketplace.json'))['plugins']))" 2>/dev/null);
         then
            echo "  ✅ Marketplace contains $MARKETPLACE_PLUGIN_COUNT plugin(s)"
            if [ "$MARKETPLACE_PLUGIN_COUNT" -lt 1 ]; then
                echo "  ❌ Marketplace must contain at least 1 plugin"
                TEST_FAILURES=$((TEST_FAILURES + 1))
            fi
        else
            echo "  ❌ Cannot read marketplace configuration"
            TEST_FAILURES=$((TEST_FAILURES + 1))
        fi
    else
        echo "  ⚠️  Skipping marketplace validation (python3 not available)"
    fi

    # Test 10: Test command file accessibility (recursive)
    echo ""
    echo "✓ Test 10: Testing command file accessibility..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    UNREADABLE=0

    # Check all found files
    while IFS= read -r cmd_file; do
        if [ ! -r "$cmd_file" ]; then
            echo "  ❌ Cannot read: $cmd_file"
            UNREADABLE=$((UNREADABLE + 1))
        fi
    done < <(find .claude/commands -type f \( -name "*.md" -o -name "*.py" \))

    if [ $UNREADABLE -eq 0 ]; then
        echo "  ✅ All command files are readable (.md and .py)"
    else
        echo "  ❌ Found $UNREADABLE unreadable files"
        TEST_FAILURES=$((TEST_FAILURES + 1))
    fi

    # Test 11: Validate YAML frontmatter in all SKILL.md files
    echo ""
    echo "✓ Test 11: Validating YAML frontmatter in SKILL.md files..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    INVALID_FRONTMATTER=0

    if command -v python3 >/dev/null 2>&1; then
        while IFS= read -r skill_file; do
            if ! python3 -c "
import sys, yaml
try:
    content = open('$skill_file').read()
    parts = content.split('---')
    if len(parts) < 3:
        print('  ❌ $skill_file: Missing YAML frontmatter delimiters (---)')
        sys.exit(1)
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        print('  ❌ $skill_file: Frontmatter is not a key-value mapping')
        sys.exit(1)
    if 'name' not in fm:
        print('  ❌ $skill_file: Missing required field \"name\"')
        sys.exit(1)
    if 'description' not in fm:
        print('  ❌ $skill_file: Missing required field \"description\"')
        sys.exit(1)
except Exception as e:
    print(f'  ❌ $skill_file: Invalid YAML frontmatter: {e}')
    sys.exit(1)
" 2>/dev/null; then
                INVALID_FRONTMATTER=$((INVALID_FRONTMATTER + 1))
            else
                echo "  ✅ $skill_file frontmatter is valid"
            fi
        done < <(find .claude/skills -name "SKILL.md" -type f)

        if [ $INVALID_FRONTMATTER -eq 0 ]; then
            echo "  ✅ All SKILL.md frontmatter files are valid"
        else
            echo "  ❌ Found $INVALID_FRONTMATTER invalid SKILL.md files"
            TEST_FAILURES=$((TEST_FAILURES + 1))
        fi
    else
        echo "  ⚠️  Skipping SKILL.md frontmatter validation (python3 not available)"
    fi
fi

# Summary
echo ""
echo "========================================"
if [ $TEST_FAILURES -eq 0 ]; then
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
    echo "❌ TESTS FAILED: $TEST_FAILURES out of $TOTAL_TESTS tests failed"
    echo ""
    echo "Please review the errors above and fix the issues."
    echo ""
    # Only wait for input if running interactively
    if [ -t 0 ]; then
        read -p "Press Enter to continue..."
    fi
fi
