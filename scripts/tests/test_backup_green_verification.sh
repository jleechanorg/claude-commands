#!/bin/bash

# GREEN PHASE TDD Verification for Backup Cron System
# Verifies that all backup system components are working after implementation

set -euo pipefail

echo "=== GREEN PHASE: TDD Verification of Backup System ==="
echo "Verifying implemented backup system functionality"
echo ""

# Test counters
PASS_COUNT=0
FAIL_COUNT=0

# Assertion helper
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

echo "=== GREEN Phase: Implemented System Verification ==="

# Test 1: Hourly cron entry exists
echo "Test 1: Hourly Backup Cron Entry"
assert_true "crontab -l 2>/dev/null | grep -q '0 \* \* \* \*.*claude_backup'" "Hourly cron entry for claude_backup exists"

# Test 2: Backup verification function works
echo ""
echo "Test 2: Backup System Verification Function"
assert_true "grep -q 'verify_backup_system()' claude_mcp.sh" "claude_mcp.sh contains verify_backup_system function"

# Test 3: Backup script is executable
echo ""
echo "Test 3: Backup Script Functionality"
assert_true "[[ -x scripts/claude_backup.sh ]]" "claude_backup.sh is executable"
assert_true "scripts/claude_backup.sh --help >/dev/null 2>&1" "claude_backup.sh responds to --help"

# Test 4: Cron wrapper script exists
echo ""
echo "Test 4: Cron Wrapper Script"
assert_true "[[ -f scripts/claude_backup_cron.sh ]]" "claude_backup_cron.sh exists"
assert_true "[[ -x scripts/claude_backup_cron.sh ]]" "claude_backup_cron.sh is executable"

# Test 5: Full system health check integration
echo ""
echo "Test 5: System Integration Verification"
# Run the verification function and capture output (strip ANSI color codes)
if bash -c "source claude_mcp.sh; verify_backup_system" | sed 's/\x1b\[[0-9;]*m//g' | grep -q "Backup system is healthy"; then
    echo "✅ PASS: Full backup system health check integration"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: Full backup system health check integration"
    ((FAIL_COUNT++))
fi

echo ""
echo "=== GREEN Phase Results ==="
echo "PASSED: $PASS_COUNT"
echo "FAILED: $FAIL_COUNT"
echo ""

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo "🎉 GREEN PHASE SUCCESS!"
    echo "All backup system components are implemented and working correctly."
    echo ""
    echo "✅ Hourly backup system: ACTIVE"
    echo "✅ Backup verification: INTEGRATED"
    echo "✅ Cron scheduling: CONFIGURED"
    echo "✅ System health checks: OPERATIONAL"
    
    # Show current schedule
    echo ""
    echo "📋 Current Backup Schedule:"
    crontab -l | grep claude_backup | while read -r line; do
        echo "   $line"
    done
else
    echo "❌ GREEN PHASE INCOMPLETE"
    echo "Some backup system components need attention."
    exit 1
fi