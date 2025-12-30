#!/bin/bash
# Run tests for orchestration

echo "Running tests for orchestration..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Run all test files from project root
FAILED=0
for test_file in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        echo "Running $test_file..."
        PYTHONPATH=. python3 "$test_file" -v
        if [ $? -ne 0 ]; then
            echo "❌ Tests failed in $test_file"
            FAILED=1
        fi
    fi
done

if [ $FAILED -ne 0 ]; then
    echo "❌ Some orchestration tests failed!"
    return 1 2>/dev/null || exit 1
fi

echo "✅ All orchestration tests passed!"
