#!/bin/bash
# TestUIF command - Run browser UI tests with REAL APIs (costs money!)
# Usage: ./testuif.sh

echo "=== Running UI Tests (FULL/REAL APIs) ==="
echo "⚠️  WARNING: This will use REAL Gemini API calls and incur costs!"
echo ""
echo "Continue? (yes/no)"
read -r response

if [ "$response" != "yes" ]; then
    echo "Test cancelled"
    exit 0
fi

# Run UI tests without mocking
if [ -f "./run_ui_tests.sh" ]; then
    ./run_ui_tests.sh full
else
    # Fallback implementation
    echo "Running UI tests with real APIs..."
    export MOCK_GEMINI=false
    export HEADLESS=true
    
    if [ -d "testing_ui" ]; then
        cd testing_ui
        test_files=$(find . -name "test_*.py" -type f)
        if [ -n "$test_files" ]; then
            python -m pytest $test_files -v
        fi
        cd ..
    fi
fi

echo ""
echo "=== Full UI Test Complete ==="
echo "Check your API usage/costs!"