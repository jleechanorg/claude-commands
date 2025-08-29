#!/bin/bash
# Test Pattern-Based Slash Command Composition Detection
# Tests both existing commands and conceptual/non-existent commands

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_SCRIPT="$PROJECT_ROOT/.claude/hooks/compose-commands.sh"

# Export REPO_ROOT for test stability (fix for CodeRabbit feedback)
export REPO_ROOT="$PROJECT_ROOT"

echo "🧪 Testing Pattern-Based Slash Command Composition Detection"
echo "============================================================"

# Test helper function
test_command_detection() {
    local input="$1"
    local expected_behavior="$2" 
    local test_name="$3"
    
    echo "Test: $test_name"
    echo "Input: $input"
    
    result=$(echo "$input" | "$COMPOSE_SCRIPT" 2>/dev/null || echo "$input")
    
    case "$expected_behavior" in
        "should_compose")
            if [[ "$result" == *"Detected slash commands"* ]]; then
                echo "✅ PASS - Composition triggered"
                return 0
            else
                echo "❌ FAIL - Should have triggered composition"
                echo "Result: $result"
                return 1
            fi
            ;;
        "should_pass_through")
            if [[ "$result" == "$input" ]]; then
                echo "✅ PASS - Passed through unchanged"
                return 0
            else
                echo "❌ FAIL - Should have passed through unchanged"
                echo "Result: $result"
                return 1
            fi
            ;;
    esac
}

echo ""
echo "🔍 Testing Existing Commands"
test_command_detection "/pr create new pull request" "should_compose" "Existing /pr command"
test_command_detection "/fake3 check for fake code" "should_compose" "Existing /fake3 command"

echo ""
echo "🆕 Testing Non-Existent Conceptual Commands"
test_command_detection "/paranoid security check everything" "should_compose" "Conceptual /paranoid command"
test_command_detection "/creative generate innovative solutions" "should_compose" "Conceptual /creative command"
test_command_detection "/ultrafast optimize for maximum speed" "should_compose" "Conceptual /ultrafast command"

echo ""
echo "🚫 Testing Non-Command Patterns (Should NOT Compose)"
test_command_detection "The file is at /usr/local/bin" "should_pass_through" "Unix path pattern"
test_command_detection "Visit https://example.com/path" "should_pass_through" "URL pattern"
test_command_detection "Regular text with no commands" "should_pass_through" "Plain text"

echo ""
echo "🔒 Testing Security Validations (Should NOT Compose)"
test_command_detection "/../../etc/passwd traverse attempt" "should_pass_through" "Path traversal attack"
test_command_detection "/../secret/file" "should_pass_through" "Parent directory traversal"
test_command_detection "/usr malicious system path" "should_pass_through" "System path false positive"
test_command_detection "/etc configuration access" "should_pass_through" "Etc path false positive"

echo ""
echo "🔄 Testing Mixed Scenarios"
test_command_detection "/pr /paranoid create secure PR with paranoid checks" "should_compose" "Mixed existing + conceptual"
test_command_detection "/creative /arch design innovative architecture" "should_compose" "Mixed conceptual + existing"

echo ""
echo "🎯 Test Summary"
echo "Pattern-based detection should:"
echo "✅ Compose existing commands (have .md files)"
echo "✅ Compose conceptual commands (slash + word pattern)"
echo "❌ Ignore path-like patterns"
echo "❌ Ignore URLs"
echo "❌ Ignore plain text"