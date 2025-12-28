#!/bin/bash
# Run tests for orchestration

echo "Running tests for orchestration..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$(dirname "$SCRIPT_DIR")" && cd .. && pwd)"

# Run all test files from project root
for test_file in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        echo "Running $test_file..."
        PYTHONPATH="$PROJECT_ROOT" python3 "$test_file" -v
        if [ $? -ne 0 ]; then
            echo "❌ Tests failed in $test_file"
            return 1
        fi
    fi
done

echo "✅ All orchestration tests passed!"
