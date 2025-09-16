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

# Get relative path from project root
RELATIVE_PATH=$(realpath --relative-to="$PROJECT_ROOT" "$ABSOLUTE_FILE_PATH" 2>/dev/null || echo "$FILE_PATH")

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
CLAUDE_OUTPUT_FILE="/tmp/claude_file_validation_output_$$.txt"

# Execute Claude with the specified parameters
if command -v claude >/dev/null 2>&1; then
    claude --dangerously-skip-permissions --model sonnet -p "$CLAUDE_PROMPT" > "$CLAUDE_OUTPUT_FILE" 2>&1
    CLAUDE_EXIT_CODE=$?

    # Read Claude's analysis
    CLAUDE_RESPONSE=$(cat "$CLAUDE_OUTPUT_FILE" 2>/dev/null || echo "Failed to read Claude response")

    # Log Claude's response
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Claude analysis for $RELATIVE_PATH:" >> "$LOG_FILE"
    echo "$CLAUDE_RESPONSE" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"

    # Check if Claude found violations
    if echo "$CLAUDE_RESPONSE" | grep -q "❌ VIOLATION"; then
        # Extract warning message for main conversation
        WARNING_MSG=$(echo "$CLAUDE_RESPONSE" | grep -A 10 "❌ VIOLATION" | head -20)

        # Create notification for main conversation thread
        echo "🚨 FILE PLACEMENT VIOLATION DETECTED by post-creation validator hook:"
        echo "File: $RELATIVE_PATH"
        echo "Analysis: $WARNING_MSG"
        echo ""
        echo "Please review file placement against CLAUDE.md protocols."

        # Call /learn if Claude recommends it
        if echo "$CLAUDE_RESPONSE" | grep -q "/learn"; then
            echo "Triggering /learn command due to detected violation pattern..."
            # Note: In actual implementation, this would trigger /learn through appropriate mechanism
        fi
    fi

    # Clean up temporary file
    rm -f "$CLAUDE_OUTPUT_FILE"
else
    echo "⚠️ Claude CLI not available for file validation analysis" >> "$LOG_FILE"
fi

# Always exit successfully to not block the workflow
exit 0
