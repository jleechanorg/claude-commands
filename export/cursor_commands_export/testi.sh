#!/bin/bash
# TestI command - Run integration tests
# Usage: ./testi.sh

echo "=== Running Integration Tests ==="

# Check for integration test directory
if [ -d "mvp_site/test_integration" ]; then
    cd mvp_site
    echo "Running integration tests..."
    TESTING=true python3 test_integration/test_integration.py
    result=$?
    cd ..
    
    if [ $result -eq 0 ]; then
        echo "✅ Integration tests passed"
    else
        echo "❌ Integration tests failed"
        exit 1
    fi
elif [ -d "test_integration" ]; then
    # Alternative location
    TESTING=true python3 test_integration/test_integration.py
else
    echo "No integration test directory found"
    echo "Integration tests verify end-to-end functionality"
fi

echo ""
echo "=== Integration Test Complete ==="