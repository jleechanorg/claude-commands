#!/bin/bash
# test-integration.sh - Run integration tests
# Replaces unreliable /testi command behavior

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if vpython command is available
if ! command -v vpython &> /dev/null; then
    echo -e "${RED}❌ 'vpython' command not found${NC}"
    echo "vpython is required for running integration tests."
    echo "Make sure you're in the project root and vpython script is available."
    echo "Fallback: Use 'python' instead if vpython is not available."
    echo "Note: This may cause different behavior compared to production environment."
    exit 1
fi

# Help function
show_help() {
    echo "test-integration.sh - Run integration tests for Claude Code"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  --specific FILE  Run a specific test file only"
    echo "  --verbose        Show detailed test output"
    echo "  --real-apis      Use real APIs instead of mocks (costs money!)"
    echo ""
    echo "Description:"
    echo "  This script runs integration tests that validate:"
    echo "  - Multiple components working together"
    echo "  - End-to-end workflows"
    echo "  - Data flow through the system"
    echo "  - API integration points"
    echo ""
    echo "Example:"
    echo "  $0                                           # Run all integration tests (mock)"
    echo "  $0 --specific test_game_workflow.py          # Run specific test"
    echo "  $0 --real-apis                               # Use real APIs (costs money!)"
    echo ""
    echo "Notes:"
    echo "  - Default: Uses mock APIs (TESTING=true)"
    echo "  - Integration tests are in mvp_site/test_integration/"
    echo "  - Tests full workflows like campaign creation → game play"
    echo "  - May be slower than unit tests"
    exit 0
}

# Parse arguments
SPECIFIC_TEST=""
VERBOSE=false
USE_REAL_APIS=false

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
        --real-apis)
            USE_REAL_APIS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🔗 Integration Test Runner${NC}"
echo "========================="

# Check project root
if [[ ! -f "mvp_site/main.py" ]]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    echo "Please run from the WorldArchitect.AI project root"
    exit 1
fi

# Warn about real APIs
if [[ "$USE_REAL_APIS" == "true" ]]; then
    echo -e "${YELLOW}⚠️  Using REAL APIs - this will cost money!${NC}"
    echo "Press Enter to continue or Ctrl+C to cancel..."
    read -r
fi

# Check for existing integration test
if [[ -f "mvp_site/test_integration/test_integration.py" ]] && [[ -z "$SPECIFIC_TEST" ]]; then
    echo -e "${GREEN}✓ Found test_integration.py${NC}"

    # Run the main integration test
    echo -e "\n${GREEN}🧪 Running integration tests...${NC}"

    if [[ "$USE_REAL_APIS" == "true" ]]; then
        echo "Mode: REAL APIs"
        cmd="python mvp_site/test_integration/test_integration.py"
    else
        echo "Mode: Mock APIs"
        cmd="env TESTING=true python mvp_site/test_integration/test_integration.py"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        $cmd
    else
        BRANCH=$(git branch --show-current)
        SANITIZED_BRANCH=$(echo "$BRANCH" | sed 's/[^a-zA-Z0-9._-]/_/g' | sed 's/^[.-]*//g')
        if $cmd > "/tmp/integration_output_${SANITIZED_BRANCH}.log" 2>&1; then
            echo -e "${GREEN}✅ Integration tests passed!${NC}"
            exit 0
        else
            echo -e "${RED}❌ Integration tests failed!${NC}"
            echo ""
            echo "Error output:"
            tail -30 /tmp/integration_output_${SANITIZED_BRANCH}.log
            exit 1
        fi
    fi
else
    # Run specific tests or search for test files
    echo -e "\n${GREEN}🔍 Looking for integration tests...${NC}"

    # Determine which tests to run
    if [[ -n "$SPECIFIC_TEST" ]]; then
        if [[ -f "mvp_site/test_integration/$SPECIFIC_TEST" ]]; then
            test_files="mvp_site/test_integration/$SPECIFIC_TEST"
        else
            echo -e "${RED}❌ Test file not found: $SPECIFIC_TEST${NC}"
            exit 1
        fi
    else
        # Find all integration test files
        test_files=$(find mvp_site/test_integration -name "test_*.py" -type f 2>/dev/null | sort)
    fi

    if [[ -z "$test_files" ]]; then
        echo -e "${YELLOW}⚠️  No integration test files found${NC}"
        echo ""
        echo "Integration tests should be in mvp_site/test_integration/"
        echo "Example: mvp_site/test_integration/test_game_workflow.py"
        exit 0
    fi

    # Run each test
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0

    for test_file in $test_files; do
        echo -e "\n${BLUE}Running: $test_file${NC}"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))

        # Build command
        if [[ "$USE_REAL_APIS" == "true" ]]; then
            cmd="vpython $test_file"
        else
            cmd="env TESTING=true vpython $test_file"
        fi

        if [[ "$VERBOSE" == "true" ]]; then
            if $cmd; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo -e "${GREEN}✅ PASSED${NC}"
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
                echo -e "${RED}❌ FAILED${NC}"
            fi
        else
            if $cmd > /tmp/test_output_${SANITIZED_BRANCH}.log 2>&1; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo -e "${GREEN}✅ PASSED${NC}"
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
                echo -e "${RED}❌ FAILED${NC}"
                echo "Error output:"
                tail -20 /tmp/test_output_${SANITIZED_BRANCH}.log
            fi
        fi
    done

    # Summary
    echo -e "\n${BLUE}📊 Test Summary${NC}"
    echo "==============="
    echo "Total tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

    if [[ "$USE_REAL_APIS" == "true" ]]; then
        echo -e "\n${YELLOW}💰 These tests used REAL API calls${NC}"
    fi

    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "\n${GREEN}✅ All integration tests passed! 🎉${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some integration tests failed!${NC}"
        exit 1
    fi
fi
