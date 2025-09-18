#!/bin/bash
# Auto-Fix File Placement Hook
# Automatically detects and fixes file placement violations
# Triggers /learn for violation patterns
# Generic script - configurable for any project structure

# Configuration: Define target directories (can be overridden by environment)
PYTHON_DIR="${PYTHON_TARGET_DIR:-src}"
TEST_DIR="${TEST_TARGET_DIR:-tests}"
SCRIPT_DIR="${SCRIPT_TARGET_DIR:-scripts}"

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

# 🚨 SECURITY: Validate file path to prevent path traversal attacks
if [[ "$FILE_PATH" =~ \.\.|^/ ]]; then
    echo "SECURITY: Rejecting potentially malicious path: $FILE_PATH"
    exit 1
fi

# Additional security: Ensure FILE_PATH doesn't contain shell metacharacters
if [[ "$FILE_PATH" =~ [\;\&\|\`\$\(\)] ]]; then
    echo "SECURITY: Rejecting path with shell metacharacters: $FILE_PATH"
    exit 1
fi

# Get filename and extension
FILENAME=$(basename "$FILE_PATH")
EXTENSION="${FILENAME##*.}"

# Security: Validate filename doesn't contain dangerous characters
if [[ "$FILENAME" =~ [\;\&\|\`\$\(\)] ]]; then
    echo "SECURITY: Rejecting filename with shell metacharacters: $FILENAME"
    exit 1
fi

# Check for violations and fix automatically
VIOLATION_DETECTED=false
CORRECTIVE_ACTION=""

# Python files should be in designated directory not project root
if [[ "$EXTENSION" == "py" && "$FILE_PATH" != $PYTHON_DIR/* && "$FILE_PATH" != .claude/* ]]; then
    if [[ "$FILE_PATH" =~ ^[^/]+\.py$ ]]; then
        # File is in project root - VIOLATION!
        VIOLATION_DETECTED=true

        # Test files go to test directory, others to python directory
        if [[ "$FILENAME" == test_* || "$FILENAME" == *_test.py || "$FILENAME" == TEST_* ]]; then
            NEW_PATH="$TEST_DIR/$FILENAME"
            DEST_DIR="$TEST_DIR/"
        else
            NEW_PATH="$PYTHON_DIR/$FILENAME"
            DEST_DIR="$PYTHON_DIR/"
        fi

        # Auto-fix: Move file to correct location
        if [ -f "$FILE_PATH" ]; then
            # Check if destination already exists to prevent overwriting
            if [ -f "$NEW_PATH" ]; then
                echo "ERROR: Destination file already exists: $NEW_PATH"
                echo "Cannot auto-fix placement - manual intervention required"
                exit 1
            fi

            mkdir -p "$DEST_DIR"
            mv "$FILE_PATH" "$NEW_PATH"
            CORRECTIVE_ACTION="MOVED: $FILE_PATH → $NEW_PATH"

            # Output correction to chat (for PostToolUse hooks this goes to transcript)
            echo "🚨 AUTO-CORRECTED FILE PLACEMENT VIOLATION"
            echo "Moved: $FILE_PATH → $NEW_PATH"
            echo "Reason: Python files must be in $PYTHON_DIR/ per CLAUDE.md protocol"
            echo ""
        fi
    fi
fi

# Shell scripts should be in designated directory not project root
if [[ "$EXTENSION" == "sh" && "$FILE_PATH" != $SCRIPT_DIR/* && "$FILE_PATH" != .claude/* ]]; then
    if [[ "$FILE_PATH" =~ ^[^/]+\.sh$ ]]; then
        VIOLATION_DETECTED=true
        NEW_PATH="$SCRIPT_DIR/$FILENAME"

        if [ -f "$FILE_PATH" ]; then
            mkdir -p "$SCRIPT_DIR/"
            mv "$FILE_PATH" "$NEW_PATH"
            chmod +x "$NEW_PATH"  # Make executable
            CORRECTIVE_ACTION="MOVED: $FILE_PATH → $NEW_PATH (made executable)"

            echo "🚨 AUTO-CORRECTED FILE PLACEMENT VIOLATION"
            echo "Moved: $FILE_PATH → $NEW_PATH"
            echo "Reason: Shell scripts must be in $SCRIPT_DIR/ per CLAUDE.md protocol"
            echo ""
        fi
    fi
fi

# If violation detected, document the learning
if [ "$VIOLATION_DETECTED" = true ]; then
    echo "📚 LEARNING: File placement violation pattern auto-corrected"
    echo "Pattern: $EXTENSION files in project root → automatic relocation"
    echo "Action taken: $CORRECTIVE_ACTION"
    echo "Note: This violation was automatically fixed per CLAUDE.md protocols"
    echo ""

    # Log learning to memory system directly (with branch isolation)
    BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    LEARNING_LOG="/tmp/claude_placement_violations_${BRANCH_NAME}.log"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $CORRECTIVE_ACTION" >> "$LEARNING_LOG"
fi

exit 0
