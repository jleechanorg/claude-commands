#!/bin/bash
# test-ui.sh - Run browser tests with mock APIs
# Replaces unreliable /testui command behavior

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Help function
show_help() {
    echo "test-ui.sh - Run browser tests with mock APIs for Claude Code"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  --specific FILE  Run a specific test file only"
    echo "  --verbose        Show detailed test output"
    echo ""
    echo "Description:"
    echo "  This script runs browser automation tests using Playwright with mock APIs:"
    echo "  - Activates virtual environment"
    echo "  - Verifies Playwright installation"
    echo "  - Starts test server on port 6006"
    echo "  - Runs all browser tests with mock responses"
    echo "  - Captures screenshots for failures"
    echo "  - Provides clear test results"
    echo ""
    echo "Example:"
    echo "  $0                                          # Run all UI tests"
    echo "  $0 --specific test_homepage.py              # Run specific test"
    echo "  $0 --verbose                                # Show detailed output"
    echo ""
    echo "Notes:"
    echo "  - Uses mock APIs to avoid costs"
    echo "  - Test server runs on port 6006 with TESTING=true"
    echo "  - Screenshots saved to testing_ui/screenshots/"
    echo "  - Requires Playwright installed in venv"
    exit 0
}

# Parse arguments
SPECIFIC_TEST=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        --specific)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🌐 Browser Test Runner (Mock APIs)${NC}"
echo "=================================="

# 1. Check if we're in project root
if [[ ! -f "mvp_site/main.py" ]]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    echo "Please run from the WorldArchitect.AI project root"
    exit 1
fi

# 2. Use the existing run_ui_tests.sh if available
if [[ -f "./run_ui_tests.sh" ]]; then
    echo -e "${GREEN}✓ Found run_ui_tests.sh - using existing test runner${NC}"
    
    # Build command
    cmd="./run_ui_tests.sh mock"
    
    if [[ -n "$SPECIFIC_TEST" ]]; then
        # For specific test, we'll need to run manually
        echo -e "${YELLOW}⚠️  Specific test requested - running manually${NC}"
        
        # Start test server
        echo -e "\n${GREEN}🚀 Starting test server...${NC}"
        TESTING=true PORT=6006 vpython mvp_site/main.py serve &
        SERVER_PID=$!
        sleep 3
        
        # Run specific test
        echo -e "\n${GREEN}🧪 Running test: $SPECIFIC_TEST${NC}"
        if TESTING=true vpython "testing_ui/$SPECIFIC_TEST"; then
            echo -e "${GREEN}✅ Test passed!${NC}"
            EXIT_CODE=0
        else
            echo -e "${RED}❌ Test failed!${NC}"
            EXIT_CODE=1
        fi
        
        # Cleanup
        kill $SERVER_PID 2>/dev/null || true
        exit $EXIT_CODE
    else
        # Run all tests
        exec $cmd
    fi
else
    echo -e "${YELLOW}⚠️  run_ui_tests.sh not found - running manually${NC}"
    
    # Manual test execution
    # 3. Verify Playwright installation
    echo -e "\n${GREEN}🔍 Checking Playwright installation...${NC}"
    if ! vpython -c "import playwright" 2>/dev/null; then
        echo -e "${RED}❌ Playwright not installed in venv!${NC}"
        echo "Cannot run browser tests - Playwright not installed"
        exit 1
    fi
    echo "✓ Playwright is installed"
    
    # 4. Start test server
    echo -e "\n${GREEN}🚀 Starting test server on port 6006...${NC}"
    TESTING=true PORT=6006 vpython mvp_site/main.py serve &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Verify server is running
    if ! curl -s http://localhost:6006 > /dev/null; then
        echo -e "${RED}❌ Test server failed to start!${NC}"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    echo "✓ Test server running on http://localhost:6006"
    
    # 5. Run tests
    echo -e "\n${GREEN}🧪 Running browser tests...${NC}"
    
    # Determine which tests to run
    if [[ -n "$SPECIFIC_TEST" ]]; then
        test_files="testing_ui/$SPECIFIC_TEST"
    else
        # Find all test files
        test_files=$(find testing_ui -name "test_*.py" -type f 2>/dev/null | sort)
    fi
    
    if [[ -z "$test_files" ]]; then
        echo -e "${YELLOW}⚠️  No test files found in testing_ui/${NC}"
        kill $SERVER_PID 2>/dev/null || true
        exit 0
    fi
    
    # Run each test
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    
    for test_file in $test_files; do
        echo -e "\n${BLUE}Running: $test_file${NC}"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        
        if [[ "$VERBOSE" == "true" ]]; then
            if TESTING=true vpython "$test_file"; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo -e "${GREEN}✅ PASSED${NC}"
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
                echo -e "${RED}❌ FAILED${NC}"
            fi
        else
            if TESTING=true vpython "$test_file" > /tmp/test_output.log 2>&1; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo -e "${GREEN}✅ PASSED${NC}"
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
                echo -e "${RED}❌ FAILED${NC}"
                echo "Error output:"
                tail -20 /tmp/test_output.log
            fi
        fi
    done
    
    # 6. Cleanup
    echo -e "\n${GREEN}🧹 Cleaning up...${NC}"
    kill $SERVER_PID 2>/dev/null || true
    
    # 7. Summary
    echo -e "\n${BLUE}📊 Test Summary${NC}"
    echo "==============="
    echo "Total tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "\n${GREEN}✅ All tests passed! 🎉${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed!${NC}"
        echo "Check testing_ui/screenshots/ for failure screenshots"
        exit 1
    fi
fi