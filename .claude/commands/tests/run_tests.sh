#!/bin/bash
# Run tests for .claude/commands

echo "Running tests for .claude/commands..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Run all test files from project root
for test_file in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        echo "Running $test_file..."
        python3 "$test_file" -v
        if [ $? -ne 0 ]; then
            echo "❌ Tests failed in $test_file"
            exit 1
        fi
    fi
done

echo "✅ All .claude/commands tests passed!"
