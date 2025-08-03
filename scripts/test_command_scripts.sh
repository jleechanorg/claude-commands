#!/bin/bash
# test_command_scripts.sh - Validate all slash command scripts
# Ensures scripts are well-formed and functioning correctly

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Command Script Validator${NC}"
echo "=========================="

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SCRIPT_DIR="$(dirname "$0")/commands"

# Function to test a script
test_script() {
    local script="$1"
    local script_name=$(basename "$script")

    echo -e "\n${BLUE}Testing: $script_name${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # Test 1: Check if executable
    if [[ ! -x "$script" ]]; then
        echo -e "  ${RED}❌ Not executable${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    echo -e "  ${GREEN}✓ Executable${NC}"

    # Test 2: Syntax check
    if ! bash -n "$script" 2>/dev/null; then
        echo -e "  ${RED}❌ Syntax error${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    echo -e "  ${GREEN}✓ Valid syntax${NC}"

    # Test 3: Check for help flag
    if ! grep -q -- '--help' "$script"; then
        echo -e "  ${YELLOW}⚠️  No --help flag found${NC}"
    else
        # Test help flag execution
        if "$script" --help > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ Help flag works${NC}"
        else
            echo -e "  ${RED}❌ Help flag failed${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi

    # Test 4: Check for set flags
    if ! grep -q 'set -euo pipefail' "$script"; then
        echo -e "  ${YELLOW}⚠️  Missing 'set -euo pipefail'${NC}"
    else
        echo -e "  ${GREEN}✓ Error handling enabled${NC}"
    fi

    # Test 5: Check for color definitions
    if grep -q 'GREEN=' "$script" && grep -q 'NC=' "$script"; then
        echo -e "  ${GREEN}✓ Color output supported${NC}"
    else
        echo -e "  ${YELLOW}⚠️  No color definitions${NC}"
    fi

    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "  ${GREEN}✅ Script validation passed${NC}"
    return 0
}

# Find all command scripts
echo -e "\n${GREEN}🔍 Scanning for command scripts...${NC}"

if [[ ! -d "$SCRIPT_DIR" ]]; then
    echo -e "${RED}❌ Script directory not found: $SCRIPT_DIR${NC}"
    exit 1
fi

scripts=$(find "$SCRIPT_DIR" -name "*.sh" -type f | sort)

if [[ -z "$scripts" ]]; then
    echo -e "${RED}❌ No scripts found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Test each script
for script in $scripts; do
    test_script "$script" || true
done

# Summary
echo -e "\n${BLUE}📊 Validation Summary${NC}"
echo "===================="
echo "Total scripts: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

# Additional checks
echo -e "\n${BLUE}📝 Additional Checks${NC}"
echo "==================="

# Check for README
if [[ -f "$(dirname "$0")/../SLASH_COMMANDS_README.md" ]]; then
    echo -e "${GREEN}✓ SLASH_COMMANDS_README.md exists${NC}"
else
    echo -e "${YELLOW}⚠️  SLASH_COMMANDS_README.md not found${NC}"
fi

# Check for git-header.sh (required for /header command)
if [[ -f "$SCRIPT_DIR/../git-header.sh" ]] || [[ -f "$(dirname "$0")/git-header.sh" ]]; then
    echo -e "${GREEN}✓ git-header.sh exists${NC}"
else
    echo -e "${YELLOW}⚠️  git-header.sh not found (needed for /header)${NC}"
fi

# Check script naming convention
echo -e "\n${BLUE}📏 Naming Convention Check${NC}"
for script in $scripts; do
    script_name=$(basename "$script" .sh)
    if [[ "$script_name" =~ ^[a-z]+(-[a-z]+)*$ ]]; then
        echo -e "${GREEN}✓ $script_name - follows kebab-case${NC}"
    else
        echo -e "${YELLOW}⚠️  $script_name - doesn't follow kebab-case${NC}"
    fi
done

# Final result
echo ""
if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}✅ All scripts validated successfully! 🎉${NC}"
    exit 0
else
    echo -e "${RED}❌ Some scripts failed validation!${NC}"
    exit 1
fi
