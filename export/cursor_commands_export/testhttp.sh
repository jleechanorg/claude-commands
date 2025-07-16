#!/bin/bash
# TestHTTP command - Run HTTP tests with mock APIs
# Usage: ./testhttp.sh

echo "=== Running HTTP Tests (Mock Mode) ==="

# Check for test script
if [ -f "./claude_command_scripts/commands/test-http.sh" ]; then
    ./claude_command_scripts/commands/test-http.sh
elif [ -d "testing_http" ]; then
    # Fallback implementation
    cd testing_http
    echo "Running HTTP tests with mock APIs..."
    export MOCK_GEMINI=true
    
    # Find and run HTTP test files
    test_files=$(find . -name "test_*.py" -type f)
    if [ -n "$test_files" ]; then
        python -m pytest $test_files -v
    else
        echo "No HTTP test files found"
    fi
    cd ..
else
    echo "No HTTP testing directory found"
    echo "HTTP tests are for testing API endpoints without browser automation"
fi

echo ""
echo "=== HTTP Test Complete ==="