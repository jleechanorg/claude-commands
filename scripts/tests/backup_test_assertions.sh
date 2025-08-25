#!/bin/bash

# TDD Test Assertions for Backup System
# Provides clear pass/fail test functions with proper error handling

# Test counter globals
PASS_COUNT=0
FAIL_COUNT=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Basic assertion function - expects command to succeed
assert_true() {
    local condition="$1"
    local test_name="$2"
    
    if eval "$condition" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        ((FAIL_COUNT++))
    fi
}

# Basic assertion function - expects command to fail
assert_false() {
    local condition="$1"
    local test_name="$2"
    
    if ! eval "$condition" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        ((FAIL_COUNT++))
    fi
}

# Assert that cron job exists matching pattern
assert_cron_job_exists() {
    local pattern="$1"
    assert_true "crontab -l 2>/dev/null | grep -E '$pattern'" "Cron job exists matching pattern: $pattern"
}

# Assert that cron job does not exist
assert_cron_job_missing() {
    local pattern="$1"
    assert_false "crontab -l 2>/dev/null | grep -E '$pattern'" "Cron job missing (expected): $pattern"
}

# Assert file exists
assert_file_exists() {
    local filepath="$1"
    assert_true "[[ -f '$filepath' ]]" "File exists: $filepath"
}

# Assert file does not exist
assert_file_missing() {
    local filepath="$1"
    assert_false "[[ -f '$filepath' ]]" "File missing (expected): $filepath"
}

# Assert file is executable
assert_file_executable() {
    local filepath="$1"
    assert_true "[[ -x '$filepath' ]]" "File is executable: $filepath"
}

# Assert backup health is integrated in claude_mcp.sh
assert_backup_health_integrated() {
    local claude_mcp_path="$1"
    assert_true "grep -q 'verify_backup_system' '$claude_mcp_path'" "Backup health check integrated in claude_mcp.sh"
}

# Assert environment variable is set
assert_env_var_set() {
    local var_name="$1"
    assert_true "[[ -n \"\${$var_name:-}\" ]]" "Environment variable set: $var_name"
}

# Assert environment variable is not set
assert_env_var_unset() {
    local var_name="$1"
    assert_false "[[ -n \"\${$var_name:-}\" ]]" "Environment variable unset (expected): $var_name"
}

# Print test summary
print_test_summary() {
    echo ""
    echo "=== TEST SUMMARY ==="
    echo -e "${GREEN}PASSED: $PASS_COUNT${NC}"
    echo -e "${RED}FAILED: $FAIL_COUNT${NC}"
    
    if [[ $FAIL_COUNT -eq 0 ]]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED${NC}"
        return 1
    fi
}