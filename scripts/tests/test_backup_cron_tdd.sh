#!/bin/bash

# RED-GREEN TDD Test for Backup Cron System Verification
# Tests that claude_mcp.sh can verify backup system is working via cron entries

set -euo pipefail
trap 'echo "❌ Test harness error at line $LINENO"; exit 1' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Test counters
PASS_COUNT=0
FAIL_COUNT=0

echo "=== RED-GREEN TDD: Backup Cron System Verification ==="
echo "Phase: RED - Writing failing tests first"
echo ""

# Assertion helpers with secure evaluation (no eval)
assert_true() {
    local condition="$1"
    local test_name="$2"

    set +e
    bash -c "$condition"
    if [[ $? -eq 0 ]]; then
        echo "✅ PASS: $test_name"
        ((PASS_COUNT++))
    else
        echo "❌ FAIL: $test_name"
        ((FAIL_COUNT++))
    fi
    set -e
}

assert_false() {
    local condition="$1"
    local test_name="$2"

    set +e
    bash -c "$condition"
    if [[ $? -ne 0 ]]; then
        echo "✅ PASS: $test_name"
        ((PASS_COUNT++))
    else
        echo "❌ FAIL: $test_name"
        ((FAIL_COUNT++))
    fi
    set -e
}

# RED PHASE: These tests should FAIL initially
echo "=== RED Phase: Tests That Should Fail Initially ==="

# Test 1: Cron setup script should create hourly backup job
echo "Test 1: Cron Setup Functionality"
assert_true "[[ -f \"$SCRIPT_DIR/claude_backup.sh\" ]]" "claude_backup.sh exists"
assert_true "grep -q 'setup_cron' \"$SCRIPT_DIR/claude_backup.sh\"" "setup_cron function exists"

# Test 2: Cron entry should be created for hourly backup
echo ""
echo "Test 2: Hourly Cron Entry Creation"
# This should FAIL initially - no cron entry exists yet
if crontab -l 2>/dev/null | grep -q "claude_backup"; then
    cron_exists=true
else
    cron_exists=false
fi
assert_false "[[ $cron_exists == false ]]" "Cron entry for claude_backup should exist (EXPECTED TO FAIL in RED phase)"

# Test 3: claude_mcp.sh should have backup verification function
echo ""
echo "Test 3: claude_mcp.sh Backup Verification"
CLAUDE_MCP_SCRIPT="$PROJECT_ROOT/claude_mcp.sh"
# NOTE: claude_mcp.sh has been replaced by scripts/install_mcp_servers.sh
# Backup verification is now handled by dedicated scripts in scripts/ directory
if [[ -f "$CLAUDE_MCP_SCRIPT" ]]; then
    assert_true "grep -q 'backup.*check\\|verify.*backup' \"$CLAUDE_MCP_SCRIPT\"" "claude_mcp.sh has backup verification logic (EXPECTED TO FAIL in RED phase)"
else
    echo "SKIP: claude_mcp.sh has been replaced by unified installer (scripts/install_mcp_servers.sh)"
    # Don't count as failure since this is expected after migration
fi

# Test 4: Backup verification should check cron entries
echo ""
echo "Test 4: Cron Entry Verification Function"
# This should FAIL - function doesn't exist yet
assert_true "[[ -f \"$PROJECT_ROOT/scripts/verify_backup_cron.sh\" ]]" "Backup cron verification script exists (EXPECTED TO FAIL in RED phase)"

# Test 5: Integration test - full backup system health check
echo ""
echo "Test 5: Full System Integration"
# This comprehensive test should FAIL initially but now should pass
integration_test_result=0

# Check if cron is set up
if ! crontab -l 2>/dev/null | grep -q "claude_backup"; then
    integration_test_result=1
fi

# Check if backup script works
if ! "$SCRIPT_DIR/claude_backup.sh" --help > /dev/null 2>&1; then
    integration_test_result=1
fi

# Check if verification is integrated (skip if claude_mcp.sh doesn't exist - it's been replaced)
if [[ -f "$PROJECT_ROOT/claude_mcp.sh" ]]; then
    if ! grep -q "verify_backup_system\|backup.*verify" "$PROJECT_ROOT/claude_mcp.sh" 2>/dev/null; then
        integration_test_result=1
    fi
fi

if [ $integration_test_result -eq 0 ]; then
    echo "✅ PASS: Full backup system health check passes (GREEN PHASE SUCCESS!)"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: Full backup system health check passes (EXPECTED TO FAIL in RED phase)"
    ((FAIL_COUNT++))
fi

echo ""
echo "=== RED Phase Results ==="
echo "PASSED: $PASS_COUNT"
echo "FAILED: $FAIL_COUNT"
echo ""

if [[ $FAIL_COUNT -gt 0 ]]; then
    echo "✅ RED PHASE SUCCESS!"
    echo "Tests are failing as expected. Ready to implement GREEN phase."
    echo ""
    echo "Next Steps for GREEN Phase:"
    echo "1. Set up hourly cron job using: ./scripts/claude_backup.sh --setup-cron"
    echo "2. Create backup verification function in claude_mcp.sh"
    echo "3. Add cron entry verification script"
    echo "4. Integrate backup health check into startup process"
    exit 0
else
    echo "❌ RED PHASE FAILED!"
    echo "No tests failed - this means the implementation already exists or tests are wrong."
    echo "RED phase should have failing tests to drive development."
    exit 1
fi
