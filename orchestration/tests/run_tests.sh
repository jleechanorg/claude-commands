#!/bin/bash
# Run tests for orchestration

echo "Running tests for orchestration..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Compute project root (two levels up from tests directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Run all test files with project root in PYTHONPATH
for test_file in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        echo "Running $test_file..."
        PYTHONPATH="$PROJECT_ROOT" python3 "$test_file" -v
        if [ $? -ne 0 ]; then
            echo "❌ Tests failed in $test_file"
            exit 1
        fi
    fi
done

echo "✅ All orchestration tests passed!"
