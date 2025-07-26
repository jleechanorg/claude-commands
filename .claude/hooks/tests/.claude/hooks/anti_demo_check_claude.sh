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

# Read JSON input from stdin
INPUT=$(cat)

# Extract relevant fields using jq
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

# Only proceed if we have content to check
if [ -z "$CONTENT" ]; then
    exit 0
fi

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Define suspicious patterns
declare -A PATTERNS=(
    ["TODO.*implement"]="Unimplemented TODO markers"
    ["return.*[\"']demo"]="Demo return values"
    ["return.*[\"']fake"]="Fake return values"
    ["[\"']simulation[\"']"]="Simulation strings"
    ["placeholder"]="Placeholder code"
    ["mock.*=.*[\"']"]="Mock assignments (outside tests)"
    ["dummy.*data"]="Dummy data values"
    ["[\"']example.*only[\"']"]="Example-only markers"
    ["not.*implemented"]="Not implemented markers"
    ["pass.*#.*implement"]="Python pass with implement comment"
    ["console\.log.*test.*data"]="Test data logging"
    ["//.*FIXME.*later"]="FIXME later comments"
    ["sample.*response"]="Sample response data"
)

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

# Check for patterns
for pattern in "${!PATTERNS[@]}"; do
    if echo "$CONTENT" | grep -i -E "$pattern" > /dev/null 2>&1; then
        description="${PATTERNS[$pattern]}"

        # Context-aware checking
        if is_test_file "$FILE_PATH" || is_mock_file "$FILE_PATH"; then
            continue
        fi

        # Found suspicious pattern
        FOUND_ISSUES=true
        ((ISSUE_COUNT++))

        # Build issue details
        ISSUE_DETAILS="${ISSUE_DETAILS}⚠️  ${description} detected in ${FILE_PATH}\n"
    fi
done

# Create response based on findings
if [ "$FOUND_ISSUES" = true ]; then
    # Log to verification file
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $FILE_PATH - $ISSUE_COUNT issues" >> "$LOG_FILE"

    # Create warning message
    WARNING_MSG=$(printf "${YELLOW}Anti-Demo Warning:${NC} Found $ISSUE_COUNT potential demo/placeholder patterns in $FILE_PATH")

    # Output JSON response to block or warn
    cat <<EOF
{
  "decision": "approve",
  "reason": "$WARNING_MSG\n$ISSUE_DETAILS\nConsider implementing real functionality instead of placeholders.",
  "suppressOutput": false
}
EOF
else
    # No issues found, approve silently
    echo '{"decision": "approve", "suppressOutput": true}'
fi
