#!/bin/bash
# Anti-Demo Detection Hook for Claude Code
# This version is specifically designed to work with Claude Code's hook system
# It receives JSON input via stdin and processes tool usage

# Find project root by looking for .git directory
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]] || [[ -f "$dir/CLAUDE.md" ]]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    echo "$PWD"  # Fallback to current directory
}

PROJECT_ROOT=$(find_project_root)
LOG_FILE="/tmp/claude_verify_implementation.txt"

# Read input from stdin
INPUT=$(cat)

# Handle both JSON input (from Claude Code hooks) and plain text input (from tests)
if echo "$INPUT" | jq -e . >/dev/null 2>&1; then
    # JSON input - Claude Code hook format
    TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
    
    # For Write tool, content is directly in tool_input.content
    # For Edit/MultiEdit, we need to check old_string and new_string
    if [ "$TOOL_NAME" = "Write" ]; then
        CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
    elif [ "$TOOL_NAME" = "Edit" ]; then
        CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
    elif [ "$TOOL_NAME" = "MultiEdit" ]; then
        # For MultiEdit, check all edits
        CONTENT=$(echo "$INPUT" | jq -r '.tool_input.edits[]?.new_string // empty' | tr '\n' ' ')
    fi
else
    # Plain text input - test format
    CONTENT="$INPUT"
    FILE_PATH="plain_text_input"
fi

# Only proceed if we have content to check
if [ -z "$CONTENT" ]; then
    exit 0
fi

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Suspicious patterns are defined in the check_pattern calls below

# Context-aware file type detection
is_test_file() {
    local path="$1"
    [[ "$path" =~ test_ ]] || \
    [[ "$path" =~ _test\. ]] || \
    [[ "$path" =~ /tests?/ ]] || \
    [[ "$path" =~ \.test\. ]]
}

is_mock_file() {
    local path="$1"
    [[ "$path" =~ mock ]] || \
    [[ "$path" =~ /mocks?/ ]] || \
    [[ "$path" =~ _mock\. ]]
}

# Track if we found any issues
FOUND_ISSUES=false
ISSUE_COUNT=0
ISSUE_DETAILS=""

# Check for patterns using simple approach
check_pattern() {
    local pattern="$1"
    local description="$2"
    
    if echo "$CONTENT" | grep -i -E "$pattern" > /dev/null 2>&1; then
        # Context-aware checking
        if is_test_file "$FILE_PATH" || is_mock_file "$FILE_PATH"; then
            return
        fi

        # Found suspicious pattern
        FOUND_ISSUES=true
        ISSUE_COUNT=$((ISSUE_COUNT + 1))

        # Build issue details
        ISSUE_DETAILS="${ISSUE_DETAILS}⚠️  ${description} detected in ${FILE_PATH}\n"
    fi
}

# Run pattern checks - Original patterns
check_pattern "TODO.*implement" "Unimplemented TODO markers"
check_pattern "return.*[\"']demo" "Demo return values"
check_pattern "return.*[\"']fake" "Fake return values"
check_pattern "[\"']simulation[\"']" "Simulation strings"
check_pattern "placeholder" "Placeholder code"
check_pattern "mock.*=.*[\"']" "Mock assignments (outside tests)"
check_pattern "dummy.*data" "Dummy data values"
check_pattern "[\"']example.*only[\"']" "Example-only markers"
check_pattern "not.*implemented" "Not implemented markers"
check_pattern "pass.*#.*implement" "Python pass with implement comment"
check_pattern "console\.log.*test.*data" "Test data logging"
check_pattern "//.*FIXME.*later" "FIXME later comments" 
check_pattern "sample.*response" "Sample response data"

# Data fabrication patterns (August 2025 enhancement)
check_pattern "~[0-9]+" "Estimated line count"
check_pattern "(around|approximately|roughly).*[0-9]+.*(lines?|line)" "Numeric approximation"
check_pattern "estimated.*[0-9]+.*(lines?|line)" "Line count estimation"
check_pattern "\|.*~[0-9]+.*\|" "Table estimation marker"

# Create response based on findings
if [ "$FOUND_ISSUES" = true ]; then
    # Log to verification file
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $FILE_PATH - $ISSUE_COUNT issues" >> "$LOG_FILE"

    # Create warning message
    WARNING_MSG=$(printf "${YELLOW}Anti-Demo Warning:${NC} Found $ISSUE_COUNT potential demo/placeholder patterns in $FILE_PATH")

    if echo "$INPUT" | jq -e . >/dev/null 2>&1; then
        # JSON mode - Claude Code hook format
        cat <<EOF
{
  "decision": "approve",
  "reason": "$WARNING_MSG\n$ISSUE_DETAILS\nConsider implementing real functionality instead of placeholders.",
  "suppressOutput": false
}
EOF
    else
        # Plain text mode - test format
        echo "FAKE CODE DETECTED: $ISSUE_DETAILS" >&2
        exit 2
    fi
else
    if echo "$INPUT" | jq -e . >/dev/null 2>&1; then
        # JSON mode - no issues found, approve silently
        echo '{"decision": "approve", "suppressOutput": true}'
    else
        # Plain text mode - no issues
        echo "No fake code detected" >&2
        exit 0
    fi
fi
