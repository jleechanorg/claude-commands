#!/bin/bash
# Run tests for .claude/commands

# Enable strict error handling
set -euo pipefail

echo "Running tests for .claude/commands..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Run all test files from project root
for test_file in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        echo "Running $test_file..."
        if ! python3 "$test_file" -v; then
            echo "❌ Tests failed in $test_file"
            exit 1
        fi
    fi
done

echo "✅ All .claude/commands tests passed!"
