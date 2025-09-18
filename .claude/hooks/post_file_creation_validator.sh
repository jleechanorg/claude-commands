#!/bin/bash
# Post-File Creation Validator Hook for Claude Code
# Validates new file placement using Claude analysis against CLAUDE.md protocols
# Triggers after Write operations to ensure proper file organization

# Find project root by looking for .git directory or CLAUDE.md
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
LOG_FILE="/tmp/claude_file_validator_log.txt"

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool information from input
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only process Write operations (file creation/editing)
if [ "$TOOL_NAME" != "Write" ]; then
    exit 0
fi

# Skip if no file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Convert to absolute path if relative
if [[ "$FILE_PATH" = /* ]]; then
    ABSOLUTE_FILE_PATH="$FILE_PATH"
else
    ABSOLUTE_FILE_PATH="$PROJECT_ROOT/$FILE_PATH"
fi

# Get relative path from project root (cross-platform compatible)
if command -v realpath >/dev/null 2>&1; then
    RELATIVE_PATH=$(realpath --relative-to="$PROJECT_ROOT" "$ABSOLUTE_FILE_PATH" 2>/dev/null || true)
fi
if [ -z "${RELATIVE_PATH:-}" ]; then
    RELATIVE_PATH="${ABSOLUTE_FILE_PATH#"$PROJECT_ROOT"/}"
fi

# Create log file with secure permissions
touch "$LOG_FILE" 2>/dev/null || true
chmod 600 "$LOG_FILE" 2>/dev/null || true

# Log the file creation event
echo "$(date '+%Y-%m-%d %H:%M:%S') - File validation triggered: $RELATIVE_PATH" >> "$LOG_FILE"

# Create Claude prompt for file justification analysis
CLAUDE_PROMPT="🚨 CRITICAL FILE JUSTIFICATION ANALYSIS REQUIRED

A new file has been created: $RELATIVE_PATH

Please analyze this file creation against CLAUDE.md protocols:

1. **FILE JUSTIFICATION PROTOCOL CHECK**:
   - Read CLAUDE.md file justification protocols
   - Verify if this file placement follows the NEW FILE CREATION PROTOCOL
   - Check if integration into existing files was attempted first
   - Validate against the INTEGRATION PREFERENCE HIERARCHY

2. **FILE PLACEMENT ANALYSIS**:
   - Is this file in the correct directory according to CLAUDE.md?
   - Should this be integrated into an existing file instead?
   - Does this violate the ANTI-CREATION BIAS protocol?

3. **REQUIRED ACTIONS**:
   - If placement is INCORRECT: Warn main conversation with specific violation
   - If integration was skipped: Call /learn to document the pattern
   - If placement is correct: Silently approve

4. **RESPONSE FORMAT**:
   - Start with ✅ APPROVED or ❌ VIOLATION
   - Provide specific CLAUDE.md rule citations
   - Suggest corrective actions if needed

Remember: You are analyzing file placement to prevent violations of CLAUDE.md protocols and maintain proper project organization."

# Run Claude analysis with specified parameters
CLAUDE_TIMEOUT="${CLAUDE_VALIDATOR_TIMEOUT:-60s}"
CLAUDE_OUTPUT_FILE="$(mktemp /tmp/claude_file_validation_output_XXXXXX)"

# Execute Claude with the specified parameters and timeout
if command -v claude >/dev/null 2>&1; then
    if command -v timeout >/dev/null 2>&1; then
        echo "$CLAUDE_PROMPT" | timeout "$CLAUDE_TIMEOUT" claude --dangerously-skip-permissions --model sonnet > "$CLAUDE_OUTPUT_FILE" 2>&1
    else
        echo "$CLAUDE_PROMPT" | claude --dangerously-skip-permissions --model sonnet > "$CLAUDE_OUTPUT_FILE" 2>&1
    fi
    CLAUDE_EXIT_CODE=$?

    # Read Claude's analysis
    CLAUDE_RESPONSE=$(cat "$CLAUDE_OUTPUT_FILE" 2>/dev/null || echo "Failed to read Claude response")

    # Log Claude's response
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Claude analysis for $RELATIVE_PATH:" >> "$LOG_FILE"
    echo "$CLAUDE_RESPONSE" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"

    # Always output Claude analysis to chat
    echo "📋 POST-CREATION VALIDATOR ANALYSIS for $RELATIVE_PATH:" >&2
    echo "$CLAUDE_RESPONSE" >&2
    echo "" >&2

    # Check if Claude found violations and provide additional context
    if echo "$CLAUDE_RESPONSE" | grep -q "❌ VIOLATION"; then
        echo "⚠️ VIOLATION DETECTED - Please review file placement against CLAUDE.md protocols." >&2

        # Call /learn if Claude recommends it
        if echo "$CLAUDE_RESPONSE" | grep -q "/learn"; then
            echo "📚 /learn command recommended due to detected violation pattern" >&2
        fi
    elif echo "$CLAUDE_RESPONSE" | grep -q "✅ APPROVED"; then
        echo "✅ File placement approved by validator" >&2
    fi

    # Clean up temporary file
    rm -f "$CLAUDE_OUTPUT_FILE"
else
    echo "⚠️ Claude CLI not available for file validation analysis" >> "$LOG_FILE"
fi

# Always exit successfully to not block the workflow
exit 0
