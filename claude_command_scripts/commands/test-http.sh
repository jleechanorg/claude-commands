#!/bin/bash
# test-http.sh - Run HTTP tests with mock APIs
# Replaces unreliable /testhttp command behavior

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Help function
show_help() {
    echo "test-http.sh - Run HTTP/API tests with mock responses for Claude Code"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  --specific FILE  Run a specific test file only"
    echo "  --verbose        Show detailed test output"
    echo "  --port PORT      Use specific port (default: 8086)"
    echo ""
    echo "Description:"
    echo "  This script runs HTTP/API tests using requests library with mock responses:"
    echo "  - Starts test server with TESTING=true for mock responses"
    echo "  - Runs HTTP endpoint tests"
    echo "  - Validates API contracts"
    echo "  - No browser automation (pure HTTP)"
    echo ""
    echo "Example:"
    echo "  $0                                    # Run all HTTP tests"
    echo "  $0 --specific test_api_auth.py        # Run specific test"
    echo "  $0 --port 8090                        # Use custom port"
    echo ""
    echo "Notes:"
    echo "  - Uses mock APIs to avoid costs"
    echo "  - Tests HTTP endpoints directly (no browser)"
    echo "  - Faster than browser tests"
    echo "  - Good for API contract testing"
    exit 0
}

# Parse arguments
SPECIFIC_TEST=""
VERBOSE=false
PORT=8086

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
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🔌 HTTP Test Runner (Mock APIs)${NC}"
echo "==============================="

# Check project root
if [[ ! -f "mvp_site/main.py" ]]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    echo "Please run from the WorldArchitect.AI project root"
    exit 1
fi

# Check for test directory
if [[ ! -d "testing_http" ]]; then
    echo -e "${YELLOW}⚠️  No testing_http directory found${NC}"
    echo "Creating testing_http directory..."
    mkdir -p testing_http
fi

# Start test server
echo -e "\n${GREEN}🚀 Starting test server on port $PORT...${NC}"
TESTING=true PORT=$PORT vpython mvp_site/main.py serve &
SERVER_PID=$!

# Wait for server
sleep 3

# Verify server
if ! curl -s http://localhost:$PORT > /dev/null; then
    echo -e "${RED}❌ Test server failed to start!${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi
echo "✓ Test server running on http://localhost:$PORT (mock mode)"

# Run tests
echo -e "\n${GREEN}🧪 Running HTTP tests...${NC}"

# Determine tests
if [[ -n "$SPECIFIC_TEST" ]]; then
    test_files="testing_http/$SPECIFIC_TEST"
else
    test_files=$(find testing_http -name "test_*.py" -type f 2>/dev/null | sort)
fi

if [[ -z "$test_files" ]]; then
    echo -e "${YELLOW}⚠️  No test files found in testing_http/${NC}"
    echo ""
    echo "HTTP tests should be placed in testing_http/ directory"
    echo "Example test structure:"
    echo "  testing_http/test_api_auth.py"
    echo "  testing_http/test_api_game.py"
    echo "  testing_http/test_api_validation.py"
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
    
    # Set test server URL for tests
    export TEST_SERVER_URL="http://localhost:$PORT"
    
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

# Cleanup
echo -e "\n${GREEN}🧹 Cleaning up...${NC}"
kill $SERVER_PID 2>/dev/null || true

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "==============="
echo "Total tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "\n${GREEN}✅ All HTTP tests passed! 🎉${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some HTTP tests failed!${NC}"
    exit 1
fi