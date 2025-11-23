#!/bin/bash
# Playwright Smoke Test Script
#
# Runs Playwright browser smoke tests for WorldArchitect.AI
# Integrates with existing smoke test infrastructure
#
# Usage:
#   ./scripts/playwright_smoke_test.sh
#   ./scripts/playwright_smoke_test.sh --headless

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_DIR="$PROJECT_ROOT/skills/playwright-worldarchitect"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎭 WorldArchitect Playwright Smoke Tests${NC}"
echo "============================================"
echo ""

# Parse arguments
HEADLESS=false
if [[ "$1" == "--headless" ]]; then
  HEADLESS=true
  echo -e "${YELLOW}⚙️  Running in headless mode${NC}"
fi

# Step 1: Check if skill is installed
echo -e "${BLUE}📦 Step 1: Checking Playwright skill installation...${NC}"
if [ ! -d "$SKILL_DIR" ]; then
  echo -e "${RED}❌ Playwright skill not found at: $SKILL_DIR${NC}"
  echo "Please run: cd $SKILL_DIR && npm install"
  exit 1
fi

if [ ! -f "$SKILL_DIR/node_modules/.bin/playwright" ]; then
  echo -e "${YELLOW}⚠️  Playwright not installed, installing now...${NC}"
  cd "$SKILL_DIR"
  npm install
  npx playwright install chromium
  cd "$PROJECT_ROOT"
fi

echo -e "${GREEN}✅ Playwright skill installed${NC}"
echo ""

# Step 2: Check if server is running
echo -e "${BLUE}🔍 Step 2: Checking for running server...${NC}"
SERVER_PORTS=(5000 8000 8080 3000 5173 8081)
SERVER_URL=""

for port in "${SERVER_PORTS[@]}"; do
  if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port" 2>/dev/null | grep -q "200\|302\|301"; then
    SERVER_URL="http://localhost:$port"
    echo -e "${GREEN}✅ Server detected at $SERVER_URL${NC}"
    break
  fi
done

if [ -z "$SERVER_URL" ]; then
  echo -e "${YELLOW}⚠️  No server detected, attempting to start...${NC}"
  echo "Please ensure the dev server is running:"
  echo "  cd mvp_site && python main.py"
  exit 1
fi

echo ""

# Step 3: Set environment variables
echo -e "${BLUE}⚙️  Step 3: Setting environment variables...${NC}"
export PLAYWRIGHT_HEADLESS="$HEADLESS"
export PLAYWRIGHT_SLOW_MO=50
export PLAYWRIGHT_TIMEOUT=30000
export BASE_URL="$SERVER_URL"
echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Step 4: Run smoke tests
echo -e "${BLUE}🚀 Step 4: Running Playwright smoke tests...${NC}"
echo "============================================"
echo ""

cd "$SKILL_DIR"

# Run the smoke test
TEST_EXIT_CODE=0
node run.js examples/smoke-test.js || TEST_EXIT_CODE=$?

echo ""
echo "============================================"

# Step 5: Report results
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ ✅ ✅ All Playwright smoke tests passed! ✅ ✅ ✅${NC}"
  exit 0
else
  echo -e "${RED}❌ Playwright smoke tests failed${NC}"
  echo -e "${YELLOW}Check the output above for details${NC}"
  exit 1
fi
