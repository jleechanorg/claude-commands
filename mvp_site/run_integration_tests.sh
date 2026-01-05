#!/bin/bash
# Script to run integration tests that make real API calls
# These tests are excluded from GitHub Actions CI

echo "================================================"
echo "Running WorldArchitect Integration Tests"
echo "================================================"
echo ""
echo "WARNING: These tests make real API calls to:"
echo "  - Google Gemini API"
echo "  - Firebase Firestore"
echo ""
echo "Ensure you have:"
echo "  - GEMINI_API_KEY environment variable set"
echo "  - serviceAccountKey.json in the project root"
echo ""
echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
sleep 5

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Find all test files in test_integration directory
echo "Finding integration tests in test_integration/..."
integration_tests=$(find test_integration -name "test_*.py" -type f | sort)

# Run tests
failed_tests=0
total_tests=0
failed_list=""

for test_file in $integration_tests; do
    echo "Running $test_file..."
    total_tests=$((total_tests + 1))

    if TESTING_AUTH_BYPASS=true python -m unittest "${test_file%%.py}" 2>/dev/null; then
        echo "✅ $test_file passed"
    else
        echo "❌ $test_file failed"
        failed_tests=$((failed_tests + 1))
        failed_list="$failed_list\n  - $test_file"
    fi
    echo "----------------------------------------"
done

# Summary
echo ""
echo "========================================"
echo "INTEGRATION TEST SUMMARY: $((total_tests - failed_tests))/$total_tests tests passed"
echo "========================================"

if [ $failed_tests -gt 0 ]; then
    echo ""
    echo -e "Failed tests:$failed_list"
    exit 1
fi
