#!/bin/bash

# GREEN Phase Test Script for Backup System
# Purpose: Tests should PASS after backup functionality is properly implemented
# This validates the implementation meets requirements

set -euo pipefail

# Source assertion helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/backup_test_assertions.sh"

# Test 1: Verify hourly backup cron job is installed correctly
echo "GREEN Phase: Verifying hourly backup cron job installation..."
assert_cron_job_exists "0 \* \* \* \* .*claude_backup"

# Test 2: Verify backup health integration in claude_mcp.sh
echo "GREEN Phase: Verifying backup health integration..."
assert_backup_health_integrated "../../claude_mcp.sh"

# Test 3: Verify backup script exists and is executable
echo "GREEN Phase: Verifying backup script functionality..."
assert_file_exists "../../scripts/claude_backup.sh"
assert_file_executable "../../scripts/claude_backup.sh"

# Test 4: Verify cron wrapper script exists and uses ~/.bashrc
echo "GREEN Phase: Verifying cron wrapper with ~/.bashrc integration..."
assert_file_exists "../../scripts/claude_backup_cron.sh"
assert_true "grep -q '~/.bashrc' ../../scripts/claude_backup_cron.sh" "Cron wrapper sources ~/.bashrc"

# Test 5: Verify backup system health check works end-to-end
echo "GREEN Phase: Verifying complete backup system integration..."
backup_system_healthy() {
    cd ../..
    source claude_mcp.sh
    verify_backup_system | grep -q "Backup system is healthy"
}

assert_true "backup_system_healthy" "Complete backup system health check passes"

print_test_summary
exit_code=$?

echo ""
if [[ $exit_code -eq 0 ]]; then
    echo "🎉 GREEN PHASE SUCCESS!"
    echo "All backup system components implemented and working correctly."
    echo ""
    echo "✅ Hourly backup system: ACTIVE"
    echo "✅ Backup verification: INTEGRATED"  
    echo "✅ ~/.bashrc environment: CONFIGURED"
    echo "✅ System health checks: OPERATIONAL"
else
    echo "❌ GREEN PHASE FAILED!"
    echo "Some backup system components need attention."
    exit 1
fi