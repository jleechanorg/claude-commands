#!/bin/bash
# Coverage command - Generate test coverage report
# Usage: ./coverage.sh [format]

format="${1:-html}"

echo "=== Generating Test Coverage Report ==="
echo "Format: $format"
echo ""

# Check if coverage script exists
if [ -f "./coverage.sh" ] && [ "$(basename "$0")" != "coverage.sh" ]; then
    ./coverage.sh $format
elif [ -f "./run_tests.sh" ]; then
    # Run tests with coverage
    echo "Running tests with coverage..."
    ./run_tests.sh --coverage
    
    # Check coverage results location
    if [ -d "/tmp/worldarchitectai/coverage" ]; then
        echo ""
        echo "✅ Coverage report generated"
        echo "View HTML report at: file:///tmp/worldarchitectai/coverage/index.html"
        
        # Show summary if available
        if [ -f "/tmp/worldarchitectai/coverage/coverage.txt" ]; then
            echo ""
            echo "Summary:"
            tail -20 /tmp/worldarchitectai/coverage/coverage.txt | grep -E "(TOTAL|Name|Cover)"
        fi
    fi
else
    # Fallback coverage implementation
    echo "Running coverage with pytest..."
    coverage run -m pytest
    
    if [ "$format" = "html" ]; then
        coverage html
        echo "✅ HTML coverage report generated in htmlcov/"
        echo "Open htmlcov/index.html in your browser"
    else
        coverage report
    fi
fi

echo ""
echo "Coverage analysis complete!"