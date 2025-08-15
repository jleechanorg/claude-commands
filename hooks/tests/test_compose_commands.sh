#!/bin/bash
# Test suite for compose-commands.sh hook
# Red-Green-Refactor methodology

set -e
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Hook path
HOOK_SCRIPT="$(dirname "$0")/../compose-commands.sh"

# Test helper function
run_test() {
    local test_name="$1"
    local input_json="$2"
    local expected_output="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    # Run the hook with JSON input via stdin (robust against escapes); don't abort suite on non-zero
    set +e
    actual_output=$(printf '%s' "$input_json" | bash "$HOOK_SCRIPT")
    hook_status=$?
    set -e
    
    if [[ -z "$expected_output" ]]; then
        if [[ -z "$actual_output" ]]; then
            echo -e "${GREEN}✓${NC} $test_name"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} $test_name"
            echo "  Expected empty output"
            echo "  Actual output: $actual_output"
            echo "  Hook exit status: ${hook_status:-N/A}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    elif [[ "$actual_output" == *"$expected_output"* ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected substring: $expected_output"
        echo "  Actual output: $actual_output"
        echo "  Hook exit status: ${hook_status:-N/A}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo "Testing compose-commands.sh hook..."
echo "================================="

# Test 1: Single command should pass through unchanged
run_test "Single command passes through" \
    '{"prompt": "/think about this problem"}' \
    "/think about this problem"

# Test 2: Multiple commands should be detected and composed
run_test "Multiple commands detected" \
    '{"prompt": "/think /debug what is happening"}' \
    "🔍 Detected slash commands:/think /debug"

# Test 3: Multiple commands should include composition instruction
run_test "Composition instruction added" \
    '{"prompt": "/investigate /paranoid /diligent check the system"}' \
    "Use these approaches in combination:/investigate /paranoid /diligent"

# Test 4: No commands should pass through unchanged
run_test "No commands passes through" \
    '{"prompt": "just a regular message"}' \
    "just a regular message"

# Test 5: Commands with complex text
run_test "Complex text with multiple commands detected" \
    '{"prompt": "/analyze /optimize this complex code with multiple lines"}' \
    "🔍 Detected slash commands:/analyze /optimize"

# Test 6: Empty JSON prompt field
run_test "Empty prompt handled" \
    '{"prompt": ""}' \
    ""

# Test 7: Missing prompt field defaults to empty
run_test "Missing prompt field" \
    '{"session_id": "123"}' \
    ""

# Test 8: Three or more commands
run_test "Three+ commands composed" \
    '{"prompt": "/think /debug /analyze /optimize the system"}' \
    "🔍 Detected slash commands:/think /debug /analyze /optimize"

# Test 9: Text before slash commands
run_test "Text before commands detected" \
    '{"prompt": "Please help me /investigate /debug this issue"}' \
    "🔍 Detected slash commands:/investigate /debug"

# Test 10: Mixed text and commands preserved
run_test "Mixed text preserved correctly" \
    '{"prompt": "I need to /analyze /optimize performance in production"}' \
    "Apply this to: I need to performance in production"

# Test 11: Escaped quotes in prompt
run_test "Handles escaped quotes" \
    '{"prompt": "He said \"use /debug /test commands\" today"}' \
    "🔍 Detected slash commands:/debug /test"

# Test 12: Complex JSON with special characters
run_test "Handles special characters" \
    '{"prompt": "Test /analyze with special: \n\t{}[]\"'\''"}' \
    "/analyze"

# Test 13: Unicode characters
run_test "Handles Unicode" \
    '{"prompt": "Unicode test /debug 你好 /analyze 🚀"}' \
    "🔍 Detected slash commands:/debug /analyze"

# Test 14: Malformed JSON fallback (should pass through as plain text)
run_test "Handles malformed JSON gracefully" \
    'not valid json' \
    "not valid json"

# Test 15: GitHub PR page text with many slashes (real-world edge case)
pr_page_text='Skip to content
Navigation Menu
jleechanorg
your-project.com

Type / to search
Code
Issues
5
Pull requests
53
Actions
Projects
Security
Insights
Settings
fix: Universal command composition hook with JSON stdin parsing and comprehensive tests #1290
 Open
jleechan2015 wants to merge 6 commits into main from compose-test  
+413 −15 
 Conversation 29
 Commits 6
 Checks 3
 Files changed 7
/think about this PR'

# Escape the text properly for JSON
escaped_pr_text=$(printf '%s' "$pr_page_text" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
run_test "Handles GitHub PR page text with file paths" \
    "{\"prompt\": \"$escaped_pr_text\"}" \
    "/think"

# Test 16: Commands with numbers (SHOULD be detected)
run_test "Commands with numbers" \
    '{"prompt": "/test123 /debug456 analyze this"}' \
    "🔍 Detected slash commands:/test123 /debug456"  # EXPECTING: Numbers should be supported

# Test 17: Commands with underscores (SHOULD be fully detected)
run_test "Commands with underscores" \
    '{"prompt": "/test_command /debug_mode run"}' \
    "🔍 Detected slash commands:/test_command /debug_mode"  # Full commands with underscores

# Test 18: Commands with hyphens (SHOULD be fully detected)
run_test "Commands with hyphens" \
    '{"prompt": "/test-feature /debug-mode check"}' \
    "🔍 Detected slash commands:/test-feature /debug-mode"  # Full commands with hyphens

# Test 19: Commands in middle of text (SHOULD be detected)
run_test "Commands in middle of text" \
    '{"prompt": "text before /command1 middle text /command2 text after"}' \
    "🔍 Detected slash commands:/command1 /command2"  # Commands anywhere in text should be detected

# Test 20: Commands with punctuation
run_test "Commands with punctuation" \
    '{"prompt": "/think, /debug. /analyze! check the system"}' \
    "🔍 Detected slash commands:/think /debug /analyze"

# Test 21: Null prompt field (Python prints "None" for null)
run_test "Null prompt field" \
    '{"prompt": null}' \
    "None"  # Python's json.load returns None which prints as "None"

# Test 22: Very many commands (10+)
run_test "Many commands (10+)" \
    '{"prompt": "/a /b /c /d /e /f /g /h /i /j /k analyze"}' \
    "🔍 Detected slash commands:/a /b /c /d /e /f /g /h /i /j /k"

# Test 23: Commands with extra spaces
run_test "Commands with extra spaces" \
    '{"prompt": "/think  /debug   /analyze    check"}' \
    "🔍 Detected slash commands:/think /debug /analyze"

# Test 24: Empty slash (edge case)
run_test "Empty slash" \
    '{"prompt": "/ // /// test"}' \
    "test"

# Test 24b: Commands with file paths - paths must be preserved (CodeRabbit suggestion)
run_test "Commands with file paths preserved" \
    '{"prompt": "/analyze please check /var/log/syslog and /etc/hosts on prod"}' \
    "/analyze please check /var/log/syslog and /etc/hosts on prod"

# Test 25: File paths should NOT be detected as commands
run_test "File paths not detected as commands" \
    '{"prompt": "Check /etc/passwd and /usr/bin/python files"}' \
    "Check /etc/passwd and /usr/bin/python files"

# Test 26: Full GitHub PR page text (from file)
if [ -f "$(dirname "$0")/github_pr_page.txt" ]; then
    pr_full_text=$(<"$(dirname "$0")/github_pr_page.txt")
    # Create JSON input with proper escaping
    # Secure JSON creation - no shell interpolation
    json_with_pr=$(
      printf '%s' "$pr_full_text" | python3 -c 'import sys, json; print(json.dumps({"prompt": sys.stdin.read()}))'
    )
    run_test "Full GitHub PR page (from file)" \
        "$json_with_pr" \
        "🔍 Detected slash commands:/investigate /paranoid /diligent"
fi

# Test 27: PR text in middle of prompt (user's specific request)
if [ -f "$(dirname "$0")/github_pr_page.txt" ]; then
    pr_middle_text=$(<"$(dirname "$0")/github_pr_page.txt")
    # User's exact request: "in the test case I want this full text here in the middle of the prompt"
    middle_input="in the test case I want this full text here in the middle of the prompt. $pr_middle_text and then continue"
    # Secure JSON creation - no shell interpolation
    json_middle=$(
      printf '%s' "$middle_input" | python3 -c 'import sys, json; print(json.dumps({"prompt": sys.stdin.read()}))'
    )
    run_test "PR text in middle of prompt" \
        "$json_middle" \
        "this full text here in the middle"
fi

# Test 28: Mixed case commands
run_test "Mixed case commands" \
    '{"prompt": "/THINK /Debug /MiXeD analyze this"}' \
    "🔍 Detected slash commands:/THINK /Debug /MiXeD"

# Test 29: Very long command names
run_test "Long command names" \
    '{"prompt": "/verylongcommandnamethatexceedsreasonablelength /another_long_command-name test"}' \
    "🔍 Detected slash commands:/verylongcommandnamethatexceedsreasonablelength /another_long_command-name"

# Test 30: Commands with parentheses around them (parentheses preserved)
run_test "Commands in parentheses" \
    '{"prompt": "(/think /debug) analyze this"}' \
    "(/think /debug) analyze this"  # Parentheses at start prevent detection

# Test 31: Array prompt field (Python will convert to string repr)
run_test "Array prompt field" \
    '{"prompt": ["array", "not", "string"]}' \
    "['array', 'not', 'string']"

# Test 32: Boolean prompt field
run_test "Boolean prompt field" \
    '{"prompt": true}' \
    "True"

# Test 33: Numeric prompt field
run_test "Numeric prompt field" \
    '{"prompt": 12345}' \
    "12345"

# Test 34: Commands at very end of text
run_test "Commands at end" \
    '{"prompt": "analyze this text /think /debug"}' \
    "🔍 Detected slash commands:/think /debug"

# Test 35: Command injection attempt (security test)
run_test "Command injection blocked" \
    '{"prompt": "/think; rm -rf / /debug"}' \
    "🔍 Detected slash commands:/think /debug"

# Test 36: FAILING TEST - Over-detection of pasted GitHub content (RED)
# This should NOT detect /investigate /paranoid /diligent as they appear in pasted PR content
pasted_github_text='# fix: Universal command composition hook with JSON stdin parsing and comprehensive tests #1290
Open
jleechan2015 wants to merge 6 commits into main from compose-test
+413 −15
Conversation 29
Commits 6
Checks 3
Files changed 7

This PR adds comprehensive universal command composition. Test this with /investigate /paranoid /diligent check the system then /commentreply to see results.'
escaped_github=$(printf '%s' "$pasted_github_text" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
run_test "Context-aware: Ignore commands in pasted GitHub content" \
    "{\"prompt\": \"$escaped_github\"}" \
    "# fix: Universal command composition hook"  # Should pass through unchanged

# Test 37: Intentional commands should still work even with some GitHub patterns  
run_test "Context-aware: Detect intentional commands with minimal GitHub patterns" \
    '{"prompt": "/think /debug this PR #1290 looks good"}' \
    "🔍 Detected slash commands:/think /debug"  # Should detect as this has minimal GitHub markers

# Additional context-aware tests merged from test_context_aware_commands.sh
echo
echo "Extended Context-Aware Tests"
echo "============================"

# Test 38: Commands at beginning of pasted content
run_test "Context: Commands at beginning of pasted content" \
    '{"prompt": "/investigate this PR: Type / to search Navigation Menu Pull requests Files changed Skip to content"}' \
    "/investigate this PR: Type / to search"

# Test 39: Commands buried in GitHub PR page should be ignored
github_pr_content='Skip to content
Navigation Menu
$USER
your-project.com
Type / to search
Code
Issues
5
Pull requests  
53
Actions
Projects
Security
Insights
/investigate /paranoid /diligent check the system
Some other content with /debug embedded
Files changed 7'

# Escape for JSON
escaped_content=$(printf '%s' "$github_pr_content" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
run_test "Context: Commands buried in pasted content ignored" \
    "{\"prompt\": \"$escaped_content\"}" \
    "Skip to content"

# Test 40: Commands at end of pasted content (≤2 commands, so detected)  
run_test "Context: Commands at end of pasted content (few commands)" \
    '{"prompt": "Type / to search Pull requests Navigation Menu Files changed then /analyze /optimize"}' \
    "🔍 Detected slash commands:/analyze /optimize"

# Test 41: Mixed intentional and pasted commands should pass through (detected as pasted)
run_test "Context: Intentional commands with pasted content" \
    '{"prompt": "/think about this: Type / to search Pull requests Navigation Menu"}' \
    "/think about this: Type / to search"

# Test 42: File paths should not trigger pasted content detection
run_test "Context: File paths don't trigger pasted detection" \
    '{"prompt": "/analyze files in /etc/passwd and /usr/bin/python"}' \
    "/analyze files in /etc/passwd"

# Test 43: Excessive slashes should trigger pasted detection
excessive_slashes='Check /var/log/file1 /usr/bin/tool /etc/config /home/user/docs /opt/app/bin /tmp/cache /run/lock /dev/null /proc/meminfo /sys/class /boot/grub /lib/modules /sbin/init /media/disk /mnt/drive /srv/www /root/.config /var/cache /usr/local/bin /etc/systemd /var/lib/docker /usr/share/doc'
escaped_excessive=$(printf '%s' "$excessive_slashes" | sed 's/"/\\"/g')
run_test "Context: Excessive slashes trigger pasted detection" \
    "{\"prompt\": \"$escaped_excessive\"}" \
    "Check /var/log/file1"

# Test 44: Commands with underscores and hyphens still work
run_test "Context: Complex command names still work" \
    '{"prompt": "/test_feature /debug-mode analyze"}' \
    "🔍 Detected slash commands:/test_feature /debug-mode"

# Test 45: Commands in quotes (normal text without pasted patterns)
json_with_quotes=$(
  printf '%s' 'The documentation says "use /investigate /debug commands" for troubleshooting' | python3 -c 'import sys, json; print(json.dumps({"prompt": sys.stdin.read()}))'
)
run_test "Context: Commands in quotes (normal text)" \
    "$json_with_quotes" \
    "🔍 Detected slash commands:/investigate /debug"

# Test 46: Real GitHub PR page scenario should pass through (detected as pasted)
real_pr_scenario='/commentfetch and handle all the issues in this PR page: Skip to content Navigation Menu Type / to search Pull requests Files changed Conversation Commits Check /path/file.txt'
run_test "Context: Real PR scenario" \
    "{\"prompt\": \"$real_pr_scenario\"}" \
    "/commentfetch and handle all the issues"

# Test 47: No false positives on normal text with slashes
run_test "Context: Normal text with slashes" \
    '{"prompt": "The price is $10/hour and delivery is 24/7 service"}' \
    'The price is $10/hour and delivery is 24/7 service'

# Security regression tests for the critical vulnerability fixes
echo
echo "Security Regression Tests"
echo "========================="

# Test 48: Regex injection vulnerability test - special regex characters
run_test "Security: Regex injection prevention with special chars" \
    '{"prompt": "/test[0-9]+ /analysis* some normal text"}' \
    "🔍 Detected slash commands:/test /analysis"

# Test 49: Command count consistency test - ensure filtered count matches strategy
run_test "Security: Command count consistency in pasted content" \
    '{"prompt": "Type / to search Pull requests /cmd1 /cmd2 /cmd3 /cmd4 Files changed"}' \
    "Type / to search Pull requests"

# Test 50: Boundary detection with regex special characters
run_test "Security: Boundary detection with special chars" \
    '{"prompt": "Start content /test.+ middle content /debug? end content"}' \
    "🔍 Detected slash commands:/test /debug"

# Test 51: Grep failure prevention with problematic patterns
run_test "Security: Prevent grep failures with problematic patterns" \
    '{"prompt": "/test( /debug) normal text"}' \
    "🔍 Detected slash commands:/test /debug"

# Summary
echo "================================="
echo -e "Tests run: $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

# Exit with failure if any tests failed (for CI/CD)
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}TESTS FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
fi