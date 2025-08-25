#!/bin/bash

# RED Phase Test Script for Backup System
# Purpose: Tests should FAIL initially before backup functionality is implemented
# This drives development by identifying what needs to be built

set -euo pipefail

echo "=== RED PHASE TDD: Backup System Verification ==="
echo "These tests should FAIL initially, driving implementation"
echo ""

# Source assertion helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/backup_test_assertions.sh"

# RED Phase Test 1: Check for backup cron job - SHOULD FAIL
echo "RED Phase Test 1: Backup cron job should NOT exist yet..."
assert_cron_job_missing "0 \* \* \* \* .*backup"

# RED Phase Test 2: Check for backup health integration - SHOULD FAIL  
echo "RED Phase Test 2: Backup health check should NOT be integrated yet..."
assert_false "grep -q 'verify_backup_system' ../../claude_mcp.sh" "Backup health check not integrated (expected failure)"

# RED Phase Test 3: Check for ~/.local/bin installation - SHOULD FAIL
echo "RED Phase Test 3: ~/.local/bin backup installation should NOT exist yet..."
assert_file_missing "$HOME/.local/bin/backup_health_check.sh"

# RED Phase Test 4: Check for BACKUP_DIR environment - SHOULD FAIL
echo "RED Phase Test 4: BACKUP_DIR environment variable should NOT be set yet..."
assert_env_var_unset "BACKUP_DIR"

# RED Phase Test 5: Check for complete backup system integration - SHOULD FAIL
echo "RED Phase Test 5: Complete backup system should NOT be functional yet..."
backup_system_functional() {
    # This function should return false (1) in RED phase
    crontab -l 2>/dev/null | grep -q "backup" && \
    [[ -f "$HOME/.local/bin/backup_health_check.sh" ]] && \
    grep -q "verify_backup_system" ../../claude_mcp.sh && \
    [[ -n "${BACKUP_DIR:-}" ]]
}

assert_false "backup_system_functional" "Complete backup system not functional (expected failure)"

print_test_summary
exit_code=$?

echo ""
if [[ $exit_code -ne 0 ]]; then
    echo "🔴 RED PHASE SUCCESS!"
    echo "Tests failed as expected. Ready to implement GREEN phase."
    echo ""
    echo "Next Steps:"
    echo "1. Set up hourly backup cron job"
    echo "2. Integrate backup health check into claude_mcp.sh"  
    echo "3. Install backup system to ~/.local/bin/"
    echo "4. Configure BACKUP_DIR environment variable"
    exit 0
else
    echo "❌ RED PHASE FAILED!"
    echo "Tests passed when they should fail - implementation already exists"
    echo "This violates TDD methodology (RED → GREEN → REFACTOR)"
    exit 1
fi