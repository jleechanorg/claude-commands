#!/bin/bash
# Browser test runner script
# Runs all browser tests in sequence

set -e

echo "🚀 WorldArchitect.AI Browser Test Suite"
echo "======================================="

# Activate virtual environment
source venv/bin/activate

# Set testing environment
export TESTING=true

# Array of test files
tests=(
    "testing_ui/test_campaign_creation_browser_v2.py"
    "testing_ui/test_continue_campaign_browser_v2.py"
    "testing_ui/test_god_mode_browser.py"
    "testing_ui/test_campaign_deletion_browser.py"
    "testing_ui/test_character_management_browser.py"
    "testing_ui/test_combat_system_browser.py"
    "testing_ui/test_multi_campaign_browser.py"
    "testing_ui/test_error_handling_browser.py"
    "testing_ui/test_settings_management_browser.py"
    "testing_ui/test_search_functionality_browser.py"
    "testing_ui/test_long_story_performance_browser.py"
    "testing_ui/test_concurrent_session_browser.py"
    "testing_ui/test_story_download_browser.py"
    "testing_ui/test_story_sharing_browser.py"
    "testing_ui/test_mobile_responsive_browser.py"
    "testing_ui/test_accessibility_browser.py"
)

# Track results
total_tests=${#tests[@]}
passed_tests=0
failed_tests=0
failed_test_names=()

echo "Running $total_tests browser tests..."
echo ""

# Run each test
for test in "${tests[@]}"; do
    test_name=$(basename "$test" .py)
    echo "🧪 Running $test_name..."
    
    if python "$test"; then
        echo "✅ $test_name PASSED"
        ((passed_tests++))
    else
        echo "❌ $test_name FAILED"
        ((failed_tests++))
        failed_test_names+=("$test_name")
    fi
    
    echo "---"
done

# Summary
echo ""
echo "📊 Test Results Summary"
echo "======================="
echo "Total tests: $total_tests"
echo "Passed: $passed_tests"
echo "Failed: $failed_tests"

if [ $failed_tests -gt 0 ]; then
    echo ""
    echo "❌ Failed tests:"
    for failed_test in "${failed_test_names[@]}"; do
        echo "  - $failed_test"
    done
    echo ""
    echo "📸 Screenshots saved to /tmp/worldarchitect_browser_screenshots/"
    exit 1
else
    echo ""
    echo "✅ All browser tests passed!"
    exit 0
fi