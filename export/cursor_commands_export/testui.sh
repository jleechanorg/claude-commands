#!/bin/bash
# TestUI command - Run browser UI tests with mock APIs
# Usage: ./testui.sh

echo "=== Running UI Tests (Mock Mode) ==="

# Check if the test script exists
if [ -f "./run_ui_tests.sh" ]; then
    ./run_ui_tests.sh mock
else
    # Fallback to find and run UI test files
    echo "Looking for UI test files..."
    if [ -d "testing_ui" ]; then
        cd testing_ui
        # Find all test files
        test_files=$(find . -name "test_*.py" -type f)
        if [ -n "$test_files" ]; then
            echo "Found UI test files:"
            echo "$test_files"
            echo ""
            # Run tests with mock environment
            export MOCK_GEMINI=true
            export HEADLESS=true
            python -m pytest $test_files -v
        else
            echo "No UI test files found in testing_ui/"
        fi
        cd ..
    else
        echo "No testing_ui directory found"
    fi
fi

echo ""
echo "=== UI Test Complete ==="
echo "Note: These tests used mock APIs to avoid costs"
echo "For real API testing, use ./testuif.sh"