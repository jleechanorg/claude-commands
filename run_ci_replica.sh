#!/bin/bash
# CI Replica Runner - Runs CI environment replication from project root
# Simplified wrapper to fix path issues

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 Running CI Environment Replica${NC}"
echo "=================================="

# Check if we're in project root
if [[ ! -f "mvp_site/requirements.txt" ]]; then
    echo -e "${RED}❌ Must run from project root (mvp_site/requirements.txt not found)${NC}"
    exit 1
fi

# Run the test suite that matches CI exactly
echo -e "${GREEN}🧪 Running test suite that matches CI...${NC}"

# Set CI environment variables
export CI=true
export GITHUB_ACTIONS=true
export TESTING=true
export TEST_MODE=mock

# Run the same tests that CI runs
if ! ./run_tests.sh; then
    echo -e "${RED}❌ CI replica tests failed${NC}"
    echo "This indicates the same failures would occur in GitHub Actions CI"
    exit 1
fi

echo -e "${GREEN}✅ CI replica tests passed${NC}"
echo "Tests should pass in GitHub Actions CI"
