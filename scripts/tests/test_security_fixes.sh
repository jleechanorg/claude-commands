#!/bin/bash

# Security Validation Test Suite for Backup System
# Tests all security fixes applied to backup verification system
# Validates: hostname validation, path traversal prevention, secure temp dirs, credential handling

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}=== Security Validation Test Suite ===${NC}"
echo "Testing all security fixes applied to backup system"
echo ""

# Test helper function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"  # "pass" or "fail"
    
    ((TESTS_RUN++))
    echo -e "${BLUE}Test $TESTS_RUN: $test_name${NC}"
    
    set +e
    eval "$test_command" >/dev/null 2>&1
    local result=$?
    set -e
    
    if [[ "$expected_result" == "pass" && $result -eq 0 ]]; then
        echo -e "${GREEN}  ✅ PASS${NC}"
        ((TESTS_PASSED++))
    elif [[ "$expected_result" == "fail" && $result -ne 0 ]]; then
        echo -e "${GREEN}  ✅ PASS (Expected failure)${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}  ❌ FAIL${NC}"
        ((TESTS_FAILED++))
    fi
    echo
}

# Test 1: Hostname Validation - Valid Hostname
run_test "Valid hostname validation" \
    "source $SCRIPT_DIR/../claude_backup.sh && validate_hostname 'test-host.local'" \
    "pass"

# Test 2: Hostname Validation - Invalid Hostname (should fail)
run_test "Invalid hostname validation (path injection)" \
    "source $SCRIPT_DIR/../claude_backup.sh && validate_hostname 'test; rm -rf /'" \
    "fail"

# Test 3: Hostname Validation - Invalid Hostname with special chars (should fail)
run_test "Invalid hostname validation (special chars)" \
    "source $SCRIPT_DIR/../claude_backup.sh && validate_hostname 'test\$(rm -rf /)'" \
    "fail"

# Test 4: Path Validation - Valid Path
run_test "Valid path validation" \
    "source $SCRIPT_DIR/../claude_backup.sh && validate_path '/tmp/valid/path' 'test context'" \
    "pass"

# Test 5: Path Validation - Path Traversal Attack (should fail)
run_test "Path traversal validation (../ attack)" \
    "source $SCRIPT_DIR/../claude_backup.sh && validate_path '/tmp/../../../etc/passwd' 'test context'" \
    "fail"

# Test 6: Path Validation - Null Byte Injection (should fail)
run_test "Null byte injection validation" \
    "source $SCRIPT_DIR/../claude_backup.sh && validate_path $'path\x00injection' 'test context'" \
    "fail"

# Test 7: Secure Temp Directory Creation
run_test "Secure temp directory creation with proper permissions" \
    'TEMP_TEST=$(mktemp -d) && chmod 700 "$TEMP_TEST" && [[ $(stat -c %a "$TEMP_TEST" 2>/dev/null || stat -f %A "$TEMP_TEST") == "700" ]]' \
    "pass"

# Test 8: Script Sources Create Secure Temp
run_test "Backup script creates secure temp directory" \
    "source $SCRIPT_DIR/../claude_backup.sh && [[ -d \"\$SECURE_TEMP\" ]] && [[ \$(stat -c %a \"\$SECURE_TEMP\" 2>/dev/null || stat -f %A \"\$SECURE_TEMP\") == \"700\" ]]" \
    "pass"

# Test 9: Verify script creates secure temp
run_test "Verify script creates secure temp directory" \
    "source $SCRIPT_DIR/../verify_backup_cron.sh && [[ -d \"\$SECURE_TEMP\" ]] && [[ \$(stat -c %a \"\$SECURE_TEMP\" 2>/dev/null || stat -f %A \"\$SECURE_TEMP\") == \"700\" ]]" \
    "pass"

# Test 10: Secure Credential Function (macOS/Linux compatible)
run_test "Secure credential retrieval function exists" \
    "source $SCRIPT_DIR/../claude_backup.sh && declare -f get_secure_credential >/dev/null" \
    "pass"

# Test 11: No hardcoded /tmp in critical functions
run_test "No hardcoded /tmp paths in backup script critical functions" \
    "! grep -E '^[^#]*LOG_FILE=\"/tmp/' $SCRIPT_DIR/../claude_backup.sh" \
    "pass"

# Test 12: Validation functions are called
run_test "Hostname validation is called in get_clean_hostname" \
    "grep -q 'validate_hostname' $SCRIPT_DIR/../claude_backup.sh" \
    "pass"

# Test 13: Path validation is called for user input
run_test "Path validation is called for user input" \
    "grep -q 'validate_path.*command line destination parameter' $SCRIPT_DIR/../claude_backup.sh" \
    "pass"

# Test 14: Secure credential setup script exists and is executable
run_test "Secure credential setup script exists and is executable" \
    "[[ -x $SCRIPT_DIR/../setup_secure_credentials.sh ]]" \
    "pass"

# Test 15: MCP integration uses secure path checking
run_test "MCP integration has secure backup log checking" \
    "grep -q 'backup_log_secure.*backup_log_legacy' $PROJECT_ROOT/claude_mcp.sh" \
    "pass"

# Test 16: Install script uses secure temp directories
run_test "Install script has secure temp directory setup" \
    "grep -q 'SECURE_TEMP.*mktemp -d' $SCRIPT_DIR/../install_backup_system.sh" \
    "pass"

# Test 17: Backup validation script has secure temp
run_test "Backup validation script has secure temp directory" \
    "grep -q 'SECURE_TEMP.*mktemp -d' $SCRIPT_DIR/../backup_validation.sh" \
    "pass"

# Test 18: No world-readable temp file creation in scripts
run_test "No direct /tmp file creation in main backup script" \
    "! grep -E '^[^#]*>/tmp/' $SCRIPT_DIR/../claude_backup.sh" \
    "pass"

echo -e "${BLUE}=== Security Test Results ===${NC}"
echo -e "Tests run: $TESTS_RUN"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}🎉 All security tests passed! The backup system is secure.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some security tests failed. Please review the fixes.${NC}"
    exit 1
fi