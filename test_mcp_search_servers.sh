#!/bin/bash
echo "🔍 Comprehensive MCP Search Servers Test"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "\n${BLUE}🧪 Test $TOTAL_TESTS: $test_name${NC}"
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to check if server exists
check_server_exists() {
    local server_name="$1"
    claude mcp list | grep -q "^$server_name:"
}

# Function to check package availability
check_package_available() {
    local package="$1"
    npm view "$package" version >/dev/null 2>&1
}

echo -e "${BLUE}📋 Starting comprehensive MCP search server tests...${NC}"
echo ""

# Test 1: Check if DuckDuckGo package exists
run_test "DuckDuckGo package availability" "check_package_available '@oevortex/ddg_search'"

# Test 2: Check if Perplexity package exists  
run_test "Perplexity package availability" "check_package_available 'server-perplexity-ask'"

# Test 3: Check if DuckDuckGo server is installed
run_test "DuckDuckGo server installation" "check_server_exists 'ddg-search'"

# Test 4: Check if Perplexity server is installed
run_test "Perplexity server installation" "check_server_exists 'perplexity-ask'"

# Test 5: Token file exists
run_test "Token file exists" "[ -f '$HOME/.token' ]"

# Test 6: GitHub token in token file
run_test "GitHub token configured" "grep -q 'GITHUB_TOKEN' '$HOME/.token'"

# Test 7: Perplexity token in token file
run_test "Perplexity token configured" "grep -q 'PERPLEXITY_API_KEY' '$HOME/.token'"

# Test 8: Node.js availability
run_test "Node.js availability" "command -v node"

# Test 9: NPX availability
run_test "NPX availability" "command -v npx"

# Test 10: Claude MCP command availability
run_test "Claude MCP command availability" "command -v claude"

echo ""
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo "======================"
echo -e "${BLUE}Total tests: $TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! MCP search servers are properly configured.${NC}"
    
    echo -e "\n${BLUE}📋 Current MCP Server Status:${NC}"
    claude mcp list | grep -E "(ddg-search|perplexity-ask):" || echo -e "${YELLOW}⚠️ Search servers not found in MCP list${NC}"
    
    echo -e "\n${BLUE}🔧 Search Server Features:${NC}"
    echo -e "${GREEN}✅ DuckDuckGo (@oevortex/ddg_search):${NC}"
    echo "   - Free web search (no API key required)"
    echo "   - Privacy-focused using DuckDuckGo engine"  
    echo "   - Content extraction and metadata retrieval"
    echo "   - Felo AI search capabilities"
    
    echo -e "\n${GREEN}✅ Perplexity (server-perplexity-ask):${NC}"
    echo "   - AI-powered search with real-time research"
    echo "   - Advanced query processing"
    echo "   - Sonar API integration"
    echo "   - Premium features with API key authentication"
    
    echo -e "\n${BLUE}💡 Usage:${NC}"
    echo "Both servers are now available as MCP tools in Claude Code"
    echo "Use them for comprehensive web search and research capabilities"
    
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please check the configuration.${NC}"
    
    echo -e "\n${YELLOW}🔧 Troubleshooting:${NC}"
    if ! check_server_exists "ddg-search"; then
        echo "- DuckDuckGo server missing: Run './claude_mcp.sh' to install"
    fi
    
    if ! check_server_exists "perplexity-ask"; then
        echo "- Perplexity server missing: Ensure PERPLEXITY_API_KEY is in ~/.token"
    fi
    
    if [ ! -f "$HOME/.token" ]; then
        echo "- Token file missing: Create ~/.token with required API keys"
    fi
    
    exit 1
fi