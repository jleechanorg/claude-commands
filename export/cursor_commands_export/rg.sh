#!/bin/bash
# RG command - Red-Green testing methodology
# Usage: ./rg.sh [test-name]

echo "=== Red-Green Testing Protocol ==="
echo ""

if [ -z "$1" ]; then
    echo "Usage: ./rg.sh [test-name]"
    echo "Example: ./rg.sh test_user_validation"
    echo ""
    echo "Red-Green Protocol:"
    echo "1. Write test that fails (RED)"
    echo "2. Verify test actually fails"
    echo "3. Write code to make it pass (GREEN)"
    echo "4. Verify test now passes"
    echo "5. Refactor if needed"
    exit 1
fi

test_name="$1"
echo "Starting Red-Green cycle for: $test_name"
echo ""
echo "Step 1: Create failing test"
echo "Example test structure:"
echo ""
echo "def $test_name():"
echo "    # Arrange"
echo "    expected = 'expected_value'"
echo "    "
echo "    # Act"
echo "    result = function_to_test()"
echo "    "
echo "    # Assert"
echo "    assert result == expected"
echo ""
echo "Step 2: Run test to confirm RED state"
echo "$ python -m pytest -v -k $test_name"
echo ""
echo "Step 3: Implement minimal code for GREEN"
echo "Step 4: Run test to confirm GREEN state"
echo "Step 5: Refactor while keeping GREEN"
echo ""
echo "Remember: Never skip the RED phase!"