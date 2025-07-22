#!/bin/bash
# Mock CI replica script for testing

echo "Running CI replica tests..."
echo "======================"
echo "Running test suite..."
echo "94 passed, 1 failed, 2 skipped"
echo "======================"
echo "FAILED: test_example.py::test_mock_failure"

# Exit with failure to simulate CI failure
exit 1