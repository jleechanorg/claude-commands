#\!/bin/bash
# Red-Green Test for speculation detection hook

HOOK_SCRIPT="../detect_speculation.sh"

echo "=== RED-GREEN TEST: Speculation Detection ==="

# TEST 1 (RED): Should FAIL - Contains speculation
echo "Test 1 (RED): Testing speculation detection..."
TEST_TEXT="I'll wait for the /commentr command to complete and provide its results before proceeding with any additional work."

echo "$TEST_TEXT"  < /dev/null |  bash "$HOOK_SCRIPT"
RED_RESULT=$?

if [ $RED_RESULT -eq 1 ]; then
    echo "✅ RED Test PASSED: Hook correctly detected speculation (exit code 1)"
else
    echo "❌ RED Test FAILED: Hook should have detected speculation but didn't (exit code $RED_RESULT)"
fi

echo ""

# TEST 2 (GREEN): Should PASS - No speculation
echo "Test 2 (GREEN): Testing normal response..."
NORMAL_TEXT="The commentr command has completed. Here are the results from the GitHub API response."

echo "$NORMAL_TEXT" | bash "$HOOK_SCRIPT"
GREEN_RESULT=$?

if [ $GREEN_RESULT -eq 0 ]; then
    echo "✅ GREEN Test PASSED: Hook correctly allowed normal response (exit code 0)"
else
    echo "❌ GREEN Test FAILED: Hook should have allowed normal response but didn't (exit code $GREEN_RESULT)"
fi

echo ""

# Summary
if [ $RED_RESULT -eq 1 ] && [ $GREEN_RESULT -eq 0 ]; then
    echo "🎯 ALL TESTS PASSED: Hook correctly detects speculation and allows normal responses"
    exit 0
else
    echo "💥 TESTS FAILED: Hook behavior is incorrect"
    exit 1
fi
