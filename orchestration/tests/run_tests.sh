#!/bin/bash
# Run tests for orchestration

echo "Running tests for orchestration..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FAILED=0

# Run all test files from project root
for test_file in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        echo "Running $test_file..."
        PYTHONPATH="$PROJECT_ROOT" python3 "$test_file" -v
        if [ $? -ne 0 ]; then
            echo "❌ Tests failed in $test_file"
            FAILED=1
        fi
    fi
done

if [ $FAILED -eq 0 ]; then
    echo "✅ All orchestration tests passed!"
else
    echo "❌ Some tests failed"
    return 1 2>/dev/null || exit 1
fi
