#!/bin/bash
# Test case for PR text with many "/" characters that shouldn't be detected as commands

set -e
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Hook path
HOOK_SCRIPT="$(dirname "$0")/../compose-commands.sh"

echo "Testing PR text edge cases..."
echo "================================="

# Test 1: Simple PR text with file paths
pr_text="/think about these comments. Skip to content Navigation Menu jleechanorg/worldarchitect.ai .claude/hooks/compose-commands.sh /dev/null"

# Secure JSON creation - no shell interpolation
json_input=$(
  printf '%s' "$pr_text" | python3 -c 'import sys, json; print(json.dumps({"prompt": sys.stdin.read()}))'
)

set +e
actual_output=$(printf '%s' "$json_input" | bash "$HOOK_SCRIPT")
hook_status=$?
set -e

if [[ $hook_status -ne 0 ]]; then
    echo "Warning: Hook returned non-zero status: $hook_status"
fi

if [[ "$actual_output" == "🔍 Detected slash commands:/think"* ]]; then
    echo -e "${GREEN}✓${NC} Test 1: Simple PR text handled correctly with composition"
else
    echo -e "${RED}✗${NC} Test 1: Simple PR text failed"
    echo "Expected: 🔍 Detected slash commands:/think..."
    echo "Actual: $actual_output"
    exit 1
fi

echo ""

# Test 2: GitHub PR text in MIDDLE of prompt (merged from test_pr_text_in_middle.sh)
echo "Test 2: PR text in middle of prompt..."

# Check if PR page file exists
PR_TEXT_FILE="$(dirname "$0")/github_pr_page.txt"
if [ ! -f "$PR_TEXT_FILE" ]; then
    echo -e "${GREEN}✓${NC} Test 2: Skipped (github_pr_page.txt not found)"
else
    full_pr_text=$(<"$PR_TEXT_FILE")
    
    # User's exact request: PR text in middle of prompt
    middle_input="in the test case I want this full text here in the middle of the prompt. $full_pr_text and then continue with more text after it"
    
    # Secure JSON creation (no shell interpolation)
    json_middle=$(
      printf '%s' "$middle_input" | python3 -c 'import sys, json; print(json.dumps({"prompt": sys.stdin.read()}))'
    )
    
    set +e
    actual_output=$(printf '%s' "$json_middle" | bash "$HOOK_SCRIPT")
    hook_status=$?
    set -e
    
    if [[ $hook_status -ne 0 ]]; then
        echo "Warning: Hook returned non-zero status: $hook_status"
    fi
    
    # With context-aware detection, this should pass through unchanged (pasted content)
    if [[ "$actual_output" == *"in the test case I want this full text"* ]]; then
        echo -e "${GREEN}✓${NC} Test 2: PR text in middle handled correctly (context-aware)"
    else
        echo -e "${RED}✗${NC} Test 2: PR text in middle failed"
        echo "Expected substring: 'in the test case I want this full text'"
        echo "Actual: ${actual_output:0:100}..."
        exit 1
    fi
fi

echo ""

# Test 3: Commands before and after PR text (as requested by user)
echo "Test 3: Commands before/after PR text..."

if [ ! -f "$PR_TEXT_FILE" ]; then
    echo -e "${GREEN}✓${NC} Test 3: Skipped (github_pr_page.txt not found)"
else
    full_pr_text=$(<"$PR_TEXT_FILE")
    
    # User's request: "/diligent ... $full_pr_text and /careful make sure we found all the commands"
    commands_around_input="/diligent in this test case $full_pr_text and /careful make sure we found all the commands"
    
    # Secure JSON creation
    json_commands=$(
      printf '%s' "$commands_around_input" | python3 -c 'import sys, json; print(json.dumps({"prompt": sys.stdin.read()}))'
    )
    
    set +e
    actual_output=$(printf '%s' "$json_commands" | bash "$HOOK_SCRIPT")
    hook_status=$?
    set -e
    
    if [[ $hook_status -ne 0 ]]; then
        echo "Warning: Hook returned non-zero status: $hook_status"
    fi
    
    # Should detect /diligent and /careful commands at boundaries despite pasted content
    if [[ "$actual_output" == *"🔍 Detected slash commands:"*"/diligent"*"/careful"* ]]; then
        echo -e "${GREEN}✓${NC} Test 3: Commands before/after PR text detected correctly"
    else
        echo -e "${RED}✗${NC} Test 3: Commands before/after PR text failed"
        echo "Expected: Commands detected (/diligent and /careful)"
        echo "Actual: ${actual_output:0:100}..."
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}All PR text tests passed!${NC}"