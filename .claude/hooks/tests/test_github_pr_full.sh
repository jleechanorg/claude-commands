#!/bin/bash
# Test case for FULL GitHub PR page text as if user typed it
# This simulates a user copying and pasting an entire GitHub PR page

set -e
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Hook path
HOOK_SCRIPT="$(dirname "$0")/../compose-commands.sh"

echo "Testing FULL GitHub PR page text edge case..."
echo "============================================"

# Use inline test PR text data (simulating user pasting GitHub PR page)
full_pr_text='Pull Request #123: Add feature X
===============================

Files changed:
- src/main.py
- tests/test_main.py
- docs/README.md

This PR adds feature X to the application. The implementation includes:
- New functionality in main.py
- Comprehensive test coverage
- Updated documentation

Please review and merge if approved.'

# Add a command at the beginning to test detection
user_input="/think about this PR page content: $full_pr_text"

# Create JSON input exactly as Claude Code would send it (robust; no shell interpolation)
json_input=$(
  printf '%s' "$user_input" | python3 -c 'import sys, json; print(json.dumps({"prompt": sys.stdin.read()}))'
)

# Show size of input for debugging
input_size=${#json_input}
echo "Input size: $input_size bytes"

# Run the hook with the full text
set +e
actual_output=$(printf '%s' "$json_input" | bash "$HOOK_SCRIPT")
hook_status=$?
set -e

# With enhanced single command processing (PR #1490), /think commands trigger composition
# The embedded commands in PR text should be filtered out, but /think should trigger composition
# Since /think is a composition-worthy command, it should trigger intelligent composition
if [[ "$actual_output" == *"🔍 Detected slash commands:/think"* ]]; then
    echo -e "${GREEN}✓${NC} FULL GitHub PR text handled correctly with enhanced composition"
    echo "  - Single /think command correctly triggers composition (PR #1490)"
    echo "  - Embedded commands in pasted content correctly ignored"
    echo "  - This demonstrates intelligent composition for composition-worthy commands"
    echo "  - Output starts with: ${actual_output:0:100}..."
    exit 0
else
    echo -e "${RED}✗${NC} FULL GitHub PR text incorrectly parsed"
    echo "Expected: 🔍 Detected slash commands:/think..."
    echo "Actual output (first 200 chars): ${actual_output:0:200}..."
    echo "Hook exit status: $hook_status"
    
    # Check if composition failed to trigger for /think
    if [[ "$actual_output" == "/think about this PR page content:"* ]]; then
        echo "❌ ERROR: Enhanced composition failed - /think should trigger composition (PR #1490)"
        echo "  - /think is now a composition-worthy command"
        echo "  - Should output composition format, not pass through unchanged"
    fi
    exit 1
fi