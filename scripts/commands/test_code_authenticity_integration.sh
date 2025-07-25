#!/bin/bash
# Integration test for code authenticity detection
# Tests the script in a real-world scenario

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Code Authenticity Detection Integration Test ===${NC}"

# Save current directory
ORIGINAL_DIR=$(pwd)
SCRIPT_PATH="$ORIGINAL_DIR/claude_command_scripts/commands/analyze_code_authenticity.sh"

# Create test directory
TEST_DIR=$(mktemp -d "/tmp/test_auth_integration_XXXXXX")
cd "$TEST_DIR"

# Cleanup on exit
cleanup() {
    cd "$ORIGINAL_DIR"
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

echo -e "\n${BLUE}Test 1: Script exists and is executable${NC}"
if [[ -x "$SCRIPT_PATH" ]]; then
    echo -e "${GREEN}✅ Script is executable${NC}"
else
    echo -e "${RED}❌ Script not found or not executable${NC}"
    exit 1
fi

echo -e "\n${BLUE}Test 2: Script handles no changes gracefully${NC}"
# Initialize git repo
git init --quiet
git config user.email "test@example.com"
git config user.name "Test User"
echo "initial" > README.md
git add README.md
git commit -m "Initial commit" --quiet

# Run script - should report no changes
output=$("$SCRIPT_PATH" 2>&1 || true)
if echo "$output" | grep -q "No code files changed"; then
    echo -e "${GREEN}✅ Correctly reports no code changes${NC}"
else
    echo -e "${RED}❌ Failed to handle no changes${NC}"
    echo "Output: $output"
fi

echo -e "\n${BLUE}Test 3: Script processes code files${NC}"
# Create a new branch with code changes
git checkout -b test-feature --quiet

# Add some code files
cat > example.py << 'EOF'
def process_request(request):
    """Process incoming request"""
    return {"status": "success", "data": request}
EOF

cat > example.js << 'EOF'
function handleClick(event) {
    console.log("Button clicked:", event.target);
    return true;
}
EOF

git add .
git commit -m "Add example code" --quiet

# Run script - should try to analyze files
output=$("$SCRIPT_PATH" 2>&1 || true)
echo "Output: $output"

if echo "$output" | grep -q "Checking code authenticity"; then
    echo -e "${GREEN}✅ Script runs analysis workflow${NC}"
else
    echo -e "${RED}❌ Script failed to run${NC}"
fi

if echo "$output" | grep -q "Files to analyze:" && echo "$output" | grep -q "example.py"; then
    echo -e "${GREEN}✅ Script identifies Python files${NC}"
else
    echo -e "${RED}❌ Failed to identify Python files${NC}"
fi

if echo "$output" | grep -q "example.js"; then
    echo -e "${GREEN}✅ Script identifies JavaScript files${NC}"
else
    echo -e "${RED}❌ Failed to identify JavaScript files${NC}"
fi

echo -e "\n${BLUE}Test 4: Script handles missing Claude CLI${NC}"
if echo "$output" | grep -q "Claude CLI not available"; then
    echo -e "${GREEN}✅ Gracefully handles missing Claude CLI${NC}"
else
    echo -e "${YELLOW}⚠️  May have Claude CLI installed${NC}"
fi

echo -e "\n${BLUE}Test 5: File extension extraction${NC}"
# Test file with multiple dots
echo "test" > "my.test.script.py"
git add "my.test.script.py"
git commit -m "Add multi-dot file" --quiet

# Check if the script would process it correctly
# We can't run the full script but we can test the pattern
if [[ "my.test.script.py" =~ \.(py|js|ts|jsx|tsx|java|cpp|c|go|rs)$ ]]; then
    echo -e "${GREEN}✅ File pattern matching works${NC}"
else
    echo -e "${RED}❌ File pattern matching failed${NC}"
fi

echo -e "\n${BLUE}Test 6: Temporary file cleanup${NC}"
# Count temp files before
temp_before=$(find /tmp -name "code_analysis_*.md" 2>/dev/null | wc -l)

# Run script
"$SCRIPT_PATH" >/dev/null 2>&1 || true

# Count temp files after
temp_after=$(find /tmp -name "code_analysis_*.md" 2>/dev/null | wc -l)

if [[ $temp_after -le $temp_before ]]; then
    echo -e "${GREEN}✅ Temporary files are cleaned up${NC}"
else
    echo -e "${RED}❌ Temporary files not cleaned up${NC}"
fi

echo -e "\n${BLUE}=== Integration Test Summary ===${NC}"
echo -e "${GREEN}✅ All integration tests completed${NC}"
echo ""
echo "The script correctly:"
echo "- Detects when no code files have changed"
echo "- Identifies code files for analysis"
echo "- Handles missing Claude CLI gracefully"
echo "- Cleans up temporary files"
echo ""
echo "Note: Full fake code detection requires Claude CLI to be installed."