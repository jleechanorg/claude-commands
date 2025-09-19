#!/bin/bash
# PreToolUse Prevention Hook - Blocks CLAUDE.md violations BEFORE creation
# Enforces integration-first philosophy by preventing file creation
# Works with PostToolUse hook as safety net

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool information
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only process Write operations
if [ "$TOOL_NAME" != "Write" ]; then
    exit 0
fi

# Skip if no file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Get filename and extension
FILENAME=$(basename "$FILE_PATH")
EXTENSION="${FILENAME##*.}"

# 🚀 FAST PRE-SCREENING: Only check root-level violations for cross-repo compatibility
# Quick pattern-based check for obvious violations (instant response)
# Check if file is in project root (handle absolute paths from Claude Code)
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RELATIVE_FILE_PATH="${FILE_PATH#$PROJECT_ROOT/}"

if [[ "$RELATIVE_FILE_PATH" =~ ^[^/]+\.(py|sh|md)$ ]]; then
    # File is in project root - this is a clear violation, block immediately
    cat << EOF
{
  "decision": "block",
  "reason": "🚨 CLAUDE.md VIOLATION BLOCKED\\n\\n**REASON:** Creating '$FILENAME' in project root violates file placement rules.\\n\\n✅ **QUICK FIX**: Place files in appropriate directories:\\n- Python files (.py) → $PROJECT_ROOT/ or module directories\\n- Shell scripts (.sh) → scripts/ directory\\n- Documentation (.md) → docs/ directory\\n\\nFILE: $FILE_PATH\\n\\nPer CLAUDE.md INTEGRATION PREFERENCE HIERARCHY:\\n1. Add to existing file with similar purpose\\n2. Add to existing utility/helper file\\n3. Add to existing test file (NEVER create new test files)\\n4. LAST RESORT: Create new file (requires justification)\\n\\nTo override: Document why integration into existing files failed.",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "File creation blocked due to root directory violation. Fast pre-screening detected obvious placement violation."
  }
}
EOF
    exit 1  # Block the operation
fi

# File passed fast pre-screening - only run Claude CLI for complex analysis
# 🤖 INTELLIGENT CLAUDE CLI ANALYSIS for file placement violations
CLAUDE_PROMPT="Analyze if creating file '$FILE_PATH' violates CLAUDE.md file placement rules:

FILE PLACEMENT RULES:
- ❌ FORBIDDEN: ANY new .py, .sh, .md files in project root
- ✅ REQUIRED: Python files → $PROJECT_ROOT/ or module directories
- ✅ REQUIRED: Shell scripts → scripts/ directory
- ✅ REQUIRED: Test files → $PROJECT_ROOT/tests/ directory

ANTI-CREATION BIAS:
- Prefer integration into existing files over creating new ones
- New test files especially discouraged - integrate into existing test files

ANALYSIS REQUIRED:
1. Does '$FILE_PATH' violate file placement rules?
2. Could this functionality be integrated into existing files instead?
3. If violation detected, suggest 2-3 existing files for integration

RESPOND WITH:
VIOLATION: [YES/NO]
REASON: [Brief explanation if violation]
INTEGRATION_TARGETS: [List 2-3 existing files that could handle this, or NONE]

Be concise and direct."

# Execute Claude CLI analysis with 15-second timeout
CLAUDE_OUTPUT=$(echo "$CLAUDE_PROMPT" | timeout 15s claude --dangerously-skip-permissions --model sonnet 2>/dev/null || echo "VIOLATION: NO
REASON: Claude CLI not available or timed out, allowing creation
INTEGRATION_TARGETS: NONE")

# Parse Claude analysis (fixed regex and logic)
VIOLATION_DETECTED=$(echo "$CLAUDE_OUTPUT" | grep -i "violation.*yes\|violation:\s*yes" | head -1)
VIOLATION_REASON=$(echo "$CLAUDE_OUTPUT" | grep -i "reason\|creating.*violates" | head -1)
INTEGRATION_SUGGESTIONS=$(echo "$CLAUDE_OUTPUT" | grep -A 5 -i "integration.*target\|suggested.*files" | tail -3)

# Convert to boolean - check if violation line contains "yes"
if [[ -n "$VIOLATION_DETECTED" ]] && echo "$VIOLATION_DETECTED" | grep -qi "yes"; then
    VIOLATION_DETECTED=true
else
    VIOLATION_DETECTED=false
fi

# If violation detected, provide blocking response
if [ "$VIOLATION_DETECTED" = true ]; then
    # Create blocking JSON response
    cat << EOF
{
  "decision": "block",
  "reason": "🚨 CLAUDE.md VIOLATION BLOCKED\n\n$VIOLATION_REASON\n\nFILE: $FILE_PATH\n\n$INTEGRATION_SUGGESTIONS\n\nPer CLAUDE.md INTEGRATION PREFERENCE HIERARCHY:\n1. Add to existing file with similar purpose\n2. Add to existing utility/helper file\n3. Add to existing test file (NEVER create new test files)\n4. LAST RESORT: Create new file (requires justification)\n\nTo override: Document why integration into existing files failed.",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "File creation blocked due to CLAUDE.md violation. Integration required before new file creation."
  }
}
EOF

    # Log the prevention action
    {
        echo "$(date -Iseconds): BLOCKED_CREATION: $FILE_PATH - $VIOLATION_REASON"
    } >> .claude/blocked_violations.log 2>/dev/null

    exit 1  # Block the operation
fi

# No violation detected, allow creation
exit 0
