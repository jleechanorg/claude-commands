#!/bin/bash
# test-ui-full.sh - Run browser tests with REAL APIs
# Replaces unreliable /testuif command behavior

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Help function
show_help() {
    echo "test-ui-full.sh - Run browser tests with REAL APIs for Claude Code"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  --specific FILE  Run a specific test file only"
    echo "  --verbose        Show detailed test output"
    echo "  --confirm        Skip cost warning (you know it costs money)"
    echo ""
    echo "Description:"
    echo "  This script runs browser automation tests using Playwright with REAL APIs:"
    echo "  - ⚠️  WARNING: This COSTS MONEY (Gemini API calls)"
    echo "  - Activates virtual environment"
    echo "  - Verifies Playwright installation"
    echo "  - Starts test server WITHOUT mock mode"
    echo "  - Runs browser tests against real backend"
    echo "  - Captures screenshots for all tests"
    echo ""
    echo "Example:"
    echo "  $0 --confirm                                # Run all UI tests (real APIs)"
    echo "  $0 --specific test_homepage.py --confirm    # Run specific test"
    echo ""
    echo "Notes:"
    echo "  - ⚠️  COSTS MONEY - Each test makes real Gemini API calls"
    echo "  - Test server runs on port 8081 WITHOUT TESTING=true"
    echo "  - Screenshots saved to testing_ui/screenshots/"
    echo "  - Use /testui (mock) for development testing"
    exit 0
}

# Parse arguments
SPECIFIC_TEST=""
VERBOSE=false
CONFIRMED=false

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
        --confirm)
            CONFIRMED=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🌐 Browser Test Runner (REAL APIs)${NC}"
echo "=================================="

# Cost warning
if [[ "$CONFIRMED" != "true" ]]; then
    echo -e "${RED}⚠️  WARNING: This will make REAL API calls and COST MONEY!${NC}"
    echo ""
    echo "Each test will:"
    echo "  - Make real Gemini API calls"
    echo "  - Use your actual API quota"
    echo "  - Potentially create real data"
    echo ""
    echo -e "${YELLOW}Are you sure you want to continue? (yes/no)${NC}"
    read -r response
    if [[ "$response" != "yes" ]]; then
        echo "Aborted. Use --confirm to skip this warning."
        exit 0
    fi
fi

# Check project root
if [[ ! -f "mvp_site/main.py" ]]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    echo "Please run from the WorldArchitect.AI project root"
    exit 1
fi

# Use existing runner if available
if [[ -f "./run_ui_tests.sh" ]] && [[ -z "$SPECIFIC_TEST" ]]; then
    echo -e "${GREEN}✓ Found run_ui_tests.sh - using existing test runner${NC}"
    echo -e "${YELLOW}⚠️  Running with REAL APIs${NC}"
    exec ./run_ui_tests.sh  # No 'mock' argument = real APIs
else
    # Manual execution
    echo -e "\n${GREEN}🔍 Checking Playwright installation...${NC}"
    if ! vpython -c "import playwright" 2>/dev/null; then
        echo -e "${RED}❌ Playwright not installed in venv!${NC}"
        echo "Cannot run browser tests - Playwright not installed"
        exit 1
    fi
    echo "✓ Playwright is installed"
    
    # Source shared port utilities
    source "$(dirname "$0")/../port-utils.sh"
    
    REAL_PORT=$(find_available_port)
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}❌ No available ports in range $BASE_PORT-$((BASE_PORT + MAX_PORTS - 1))${NC}"
        exit 1
    fi
    
    # Start REAL server (no TESTING=true)
    echo -e "\n${GREEN}🚀 Starting REAL server on port $REAL_PORT...${NC}"
    echo -e "${YELLOW}⚠️  Server running with REAL APIs${NC}"
    PORT=$REAL_PORT vpython mvp_site/main.py serve &
    SERVER_PID=$!
    
    # Wait for server
    sleep 3
    
    # Verify server
    if ! curl -s http://localhost:8081 > /dev/null; then
        echo -e "${RED}❌ Server failed to start!${NC}"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    echo "✓ Server running on http://localhost:8081 (REAL MODE)"
    
    # Run tests
    echo -e "\n${GREEN}🧪 Running browser tests with REAL APIs...${NC}"
    
    # Determine tests
    if [[ -n "$SPECIFIC_TEST" ]]; then
        test_files="testing_ui/$SPECIFIC_TEST"
    else
        test_files=$(find testing_ui -name "test_*.py" -type f 2>/dev/null | sort)
    fi
    
    if [[ -z "$test_files" ]]; then
        echo -e "${YELLOW}⚠️  No test files found${NC}"
        kill $SERVER_PID 2>/dev/null || true
        exit 0
    fi
    
    # Run each test
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    
    for test_file in $test_files; do
        echo -e "\n${BLUE}Running: $test_file (REAL APIs)${NC}"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        
        if [[ "$VERBOSE" == "true" ]]; then
            if vpython "$test_file"; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo -e "${GREEN}✅ PASSED${NC}"
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
                echo -e "${RED}❌ FAILED${NC}"
            fi
        else
            if vpython "$test_file" > /tmp/test_output.log 2>&1; then
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
    
    # Cleanup
    echo -e "\n${GREEN}🧹 Cleaning up...${NC}"
    kill $SERVER_PID 2>/dev/null || true
    
    # Summary
    echo -e "\n${BLUE}📊 Test Summary (REAL APIs)${NC}"
    echo "=========================="
    echo "Total tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo ""
    echo -e "${YELLOW}💰 Remember: These tests used REAL API calls${NC}"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "\n${GREEN}✅ All tests passed! 🎉${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed!${NC}"
        echo "Check testing_ui/screenshots/ for failure screenshots"
        exit 1
    fi
fi