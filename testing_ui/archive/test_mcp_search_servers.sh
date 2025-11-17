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

# Test 2: Check if Perplexity MCP package exists
run_test "Perplexity MCP package availability" "check_package_available '@jschuller/perplexity-mcp'"

# Test 3: Check if DuckDuckGo server is installed
run_test "DuckDuckGo server installation" "check_server_exists 'ddg-search'"

# Test 4: Check if Perplexity MCP server is installed (requires PERPLEXITY_API_KEY)
if [ -n "${PERPLEXITY_API_KEY:-}" ]; then
    run_test "Perplexity MCP server installation" "check_server_exists 'perplexity-mcp'"
else
    echo -e "${YELLOW}⚠️  Skipping Perplexity MCP server installation check (PERPLEXITY_API_KEY not set)${NC}"
fi

# Test 5: Check if Grok server is installed (requires GROK_API_KEY/XAI_API_KEY)
if [ -n "${GROK_API_KEY:-}" ] || [ -n "${XAI_API_KEY:-}" ]; then
    run_test "Grok server installation" "check_server_exists 'grok-mcp'"
else
    echo -e "${YELLOW}⚠️  Skipping Grok server installation check (GROK_API_KEY or XAI_API_KEY not set)${NC}"
fi

# Test 6: GitHub token available (environment variable or token file)
run_test "GitHub token available" "[ -n \"\${GITHUB_TOKEN:-}\" ] || [ -f '$HOME/.token' ]"

# Test 7: GitHub token configured (environment variable or in token file)
run_test "GitHub token configured" "[ -n \"\${GITHUB_TOKEN:-}\" ] || grep -q 'GITHUB_TOKEN' '$HOME/.token'"

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
    claude mcp list | grep -E "(perplexity-mcp|ddg-search|grok-mcp):" || echo -e "${YELLOW}⚠️ Search servers not found in MCP list${NC}"

    echo -e "\n${BLUE}🔧 Search Server Features:${NC}"
    echo -e "${GREEN}✅ DuckDuckGo (@oevortex/ddg_search):${NC}"
    echo "   - Free web search (no API key required)"
    echo "   - Privacy-focused using DuckDuckGo engine"
    echo "   - Content extraction and metadata retrieval"
    echo "   - Felo AI search capabilities"

    echo -e "\n${GREEN}✅ Perplexity (@jschuller/perplexity-mcp):${NC}"
    echo "   - Premium deep research with Sonar models"
    echo "   - Supports recency filters, temperature, and token controls"
    echo "   - Returns citations and reasoning traces via perplexity_search_web"
    echo "   - Requires PERPLEXITY_API_KEY environment variable"

    echo -e "\n${GREEN}✅ Grok (grok-mcp):${NC}"
    echo "   - Real-time intelligence and trending insights"
    echo "   - Complements Claude WebSearch with fast signal"
    echo "   - Conversational responses for synthesis"

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

    if ! check_server_exists "perplexity-mcp"; then
        echo "- Perplexity server missing: Ensure PERPLEXITY_API_KEY is set and rerun ./claude_mcp.sh"
    fi

    if ([ -n "${GROK_API_KEY:-}" ] || [ -n "${XAI_API_KEY:-}" ]) && ! check_server_exists "grok-mcp"; then
        echo "- Grok server missing: Re-run './claude_mcp.sh' after configuring GROK credentials"
    fi

    if [ -z "$GITHUB_TOKEN" ] && [ -z "$PERPLEXITY_API_KEY" ]; then
        echo "- API keys missing: Set GITHUB_TOKEN and PERPLEXITY_API_KEY environment variables"
    fi

    exit 1
fi
