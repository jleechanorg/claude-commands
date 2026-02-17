#!/bin/bash
# Regression tests for install_cron_entries.sh
# Tests edge cases found during code review

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT
TEST_BIN_DIR="$TEST_DIR/bin"
FAKE_CRONTAB_FILE="$TEST_DIR/fake_system_crontab.txt"
CRONTAB_CALL_LOG="$TEST_DIR/crontab_calls.log"
export HOME="$TEST_DIR/home"
mkdir -p "$TEST_BIN_DIR"
mkdir -p "$HOME"

cat >"$TEST_BIN_DIR/crontab" <<'EOF'
#!/bin/bash
set -euo pipefail

fake_file="${FAKE_CRONTAB_FILE:?FAKE_CRONTAB_FILE must be set}"
call_log="${CRONTAB_CALL_LOG:?CRONTAB_CALL_LOG must be set}"
arg="${1:-}"
echo "crontab $*" >>"$call_log"

case "$arg" in
    -l)
        if [[ -f "$fake_file" ]]; then
            cat "$fake_file"
            exit 0
        fi
        echo "no crontab for user" >&2
        exit 1
        ;;
    -r)
        rm -f "$fake_file"
        exit 0
        ;;
    "")
        cat >"$fake_file"
        exit 0
        ;;
    -)
        cat >"$fake_file"
        exit 0
        ;;
    *)
        cat "$arg" >"$fake_file"
        exit 0
        ;;
esac
EOF

chmod +x "$TEST_BIN_DIR/crontab"
export FAKE_CRONTAB_FILE
export CRONTAB_CALL_LOG
export PATH="$TEST_BIN_DIR:$PATH"

if [[ "$(command -v crontab)" != "$TEST_BIN_DIR/crontab" ]]; then
    echo "FAIL: fake crontab shim is not active" >&2
    exit 1
fi

# Create mock crontab.template
cat > "$TEST_DIR/crontab.template" <<'EOF'
PATH=$HOME/.local/bin:$HOME/.pyenv/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin

# [CRON-JOB-ID: pr-monitor] Run PR monitoring every 2 hours
0 */2 * * * jleechanorg-pr-monitor --max-prs 10

# [CRON-JOB-ID: fix-comment] Run fix-comment workflow every hour at :45
45 * * * * jleechanorg-pr-monitor --fix-comment --cli-agent minimax,gemini,cursor --max-prs 3

# [CRON-JOB-ID: comment-validation] Run comment validation every 30 minutes
*/30 * * * * jleechanorg-pr-monitor --comment-validation --max-prs 10

# [CRON-JOB-ID: codex-update] Run Codex automation every hour at :15
15 * * * * jleechanorg-pr-monitor --codex-update --codex-task-limit 10

# [CRON-JOB-ID: codex-api] Run Codex API automation every hour at :30
30 * * * * jleechanorg-pr-monitor --codex-api --codex-apply-and-push --codex-task-limit 10

# [CRON-JOB-ID: fixpr] Run orchestrated PR fixes every 30 minutes
*/30 * * * * jleechanorg-pr-monitor --fixpr --max-prs 10 --cli-agent minimax,gemini,cursor

# Backup Claude conversations every 4 hours
# [CRON-JOB-ID: backup] Backup entries don't typically have IDs but we need one for tracking
0 */4 * * * "$HOME/.local/bin/claude_backup_cron.sh" "$HOME/Library/CloudStorage/Dropbox"
EOF

MANAGED_START="# === Automation entries (managed by install_cron_entries.sh) ==="
MANAGED_END="# === End automation entries ==="

# Helper function to run the script with mock crontab
run_script_with_mock() {
    local existing_crontab="$1"
    echo "$existing_crontab" | crontab -
    # Debug: show what we set up
    echo "=== SETUP CRONTAB ==="
    crontab -l
    echo "=== RUNNING SCRIPT ==="
    # Run script and capture TEMP_CRON location from output
    CRON_FILE="$TEST_DIR/crontab.template" "$SCRIPT_DIR/install_cron_entries.sh" 2>&1
    # Show what's actually in the crontab
    echo "=== FINAL CRONTAB ==="
    crontab -l
    echo "=== END ==="
}

extract_final_crontab() {
    awk '
        /^=== FINAL CRONTAB ===$/ { in_final=1; next }
        /^=== END ===$/ { in_final=0 }
        in_final { print }
    '
}

# Test 1: Full path command names should be deduplicated
test_full_path_command_deduplication() {
    echo "Test 1: Full path command names should be deduplicated"
    # Ensure clean state
    crontab -r
    # Legacy entry with full path (same schedule as template) - should be removed
    local existing_crontab=$(cat <<'CRON'
PATH=/usr/local/bin

# Legacy entry with full path - should be removed (matches template schedule 0 */4)
0 */4 * * * "$HOME/.local/bin/claude_backup_cron.sh" "$HOME/Library/CloudStorage/Dropbox"

# Other user entries
0 8 * * * /usr/bin/curl https://example.com/health
CRON
)
    local result=$(run_script_with_mock "$existing_crontab")
    local final_crontab
    final_crontab="$(echo "$result" | extract_final_crontab)"

    # Should NOT have duplicate backup entries
    local backup_count=$(echo "$final_crontab" | grep -c "claude_backup_cron.sh" || true)
    if [[ "$backup_count" -eq 1 ]]; then
        echo "  PASS: Only one backup entry found"
    else
        echo "  FAIL: Expected 1 backup entry, found $backup_count"
        echo "$result" | grep "claude_backup_cron.sh"
        return 1
    fi
}

# Test 2: Quoted commands should be deduplicated
test_quoted_command_deduplication() {
    echo "Test 2: Quoted commands should be deduplicated"
    crontab -r
    # Legacy quoted entry - should be removed (same schedule as template 0 */2)
    local existing_crontab=$(cat <<'CRON'
PATH=/usr/local/bin

# Legacy quoted entry - should be removed
0 */2 * * * "jleechanorg-pr-monitor" --max-prs 10
CRON
)
    local result=$(run_script_with_mock "$existing_crontab")
    local final_crontab
    final_crontab="$(echo "$result" | extract_final_crontab)"

    # Should have only one equivalent pr-monitor entry (quoted or unquoted)
    local pr_monitor_count
    pr_monitor_count=$(echo "$final_crontab" | grep -Ec '^0 \*/2 \* \* \* "?jleechanorg-pr-monitor"? --max-prs 10$' || true)
    if [[ "$pr_monitor_count" -eq 1 ]]; then
        echo "  PASS: Only one pr-monitor entry found"
    else
        echo "  FAIL: Expected 1 pr-monitor entry, found $pr_monitor_count"
        echo "$result" | grep "jleechanorg-pr-monitor"
        return 1
    fi
}

# Test 3: Unclosed MANAGED_START should preserve user entries after it
test_unclosed_managed_block_preserves_entries() {
    echo "Test 3: Unclosed MANAGED_START should preserve user entries"
    crontab -r
    local existing_crontab=$(cat <<'CRON'
PATH=/usr/local/bin

# === Automation entries (managed by install_cron_entries.sh)
# NOTE: Missing MANAGED_END - this is an unclosed block
0 */2 * * * jleechanorg-pr-monitor --max-prs 10

# User entry that should be preserved
30 2 * * * my-custom-backup-script

# Another user entry
0 0 * * * dailyCleanup
CRON
)
    local output=$(run_script_with_mock "$existing_crontab" 2>&1)
    local result
    result="$(echo "$output" | extract_final_crontab)"

    # Should preserve user entries after unclosed block
    if echo "$result" | grep -q "my-custom-backup-script"; then
        echo "  PASS: User entry preserved after unclosed block"
    else
        echo "  FAIL: User entry was lost after unclosed block"
        echo "$result"
        return 1
    fi
}

# Test 4: Mixed user and managed entries should coexist
test_mixed_user_and_managed_entries() {
    echo "Test 4: Mixed user and managed entries should coexist"
    crontab -r
    local existing_crontab=$(cat <<'CRON'
PATH=/usr/local/bin

# User's personal crontab entry
0 8 * * * /usr/bin/curl https://example.com/health

# === Automation entries (managed by install_cron_entries.sh) ===
PATH=$HOME/.local/bin
0 */2 * * * jleechanorg-pr-monitor --max-prs 10
# === End automation entries ===

# Another user entry after managed block
0 18 * * * evening-task
CRON
)
    local result=$(run_script_with_mock "$existing_crontab")
    local final_crontab
    final_crontab="$(echo "$result" | extract_final_crontab)"

    # Should preserve both user entries
    if echo "$final_crontab" | grep -q "curl https://example.com/health" && \
       echo "$final_crontab" | grep -q "evening-task"; then
        echo "  PASS: Both user entries preserved"
    else
        echo "  FAIL: User entries were lost"
        echo "$result"
        return 1
    fi

    # Should not duplicate the 0 */2 pr-monitor job.
    local pm_count
    pm_count=$(echo "$final_crontab" | grep -Ec '^0 \*/2 \* \* \* "?jleechanorg-pr-monitor"? --max-prs 10$' || true)
    if [[ "$pm_count" -eq 1 ]]; then
        echo "  PASS: No duplicate 0 */2 pr-monitor entry"
    else
        echo "  FAIL: Expected 1 0 */2 pr-monitor entry, found $pm_count"
        return 1
    fi
}

# Test 5: Clean install should work
test_clean_install() {
    echo "Test 5: Clean install should work"
    crontab -r
    local existing_crontab=$(cat <<'CRON'
# Empty crontab - clean install
CRON
)
    local result=$(run_script_with_mock "$existing_crontab")
    local final_crontab
    final_crontab="$(echo "$result" | extract_final_crontab)"

    # Should have all managed entries
    local pr_monitor_count=$(echo "$final_crontab" | grep -c "jleechanorg-pr-monitor" || true)
    if [[ "$pr_monitor_count" -ge 6 ]]; then
        echo "  PASS: All managed entries installed ($pr_monitor_count found)"
    else
        echo "  FAIL: Expected at least 6 managed entries, found $pr_monitor_count"
        echo "$result"
        return 1
    fi
}

# Test 6: README quick-start should reference published package names
test_readme_uses_published_package_names() {
    echo "Test 6: README quick-start should use jleechanorg-orchestration package name"
    if grep -Eq '^pip install jleechanorg-orchestration jleechanorg-pr-automation$' "$SCRIPT_DIR/README.md"; then
        echo "  PASS: README uses published package names"
    else
        echo "  FAIL: README quick-start does not use expected package install command"
        return 1
    fi
}

# Test 7: Installer must operate through fake crontab only (non-real crontab unit test)
test_non_real_crontab_harness_is_used() {
    echo "Test 7: Installer uses fake crontab harness only"
    : >"$CRONTAB_CALL_LOG"

    local existing_crontab
    existing_crontab=$(cat <<'CRON'
PATH=/usr/local/bin
0 8 * * * /usr/bin/true
CRON
)
    run_script_with_mock "$existing_crontab" >/dev/null

    if ! grep -q '^crontab -l$' "$CRONTAB_CALL_LOG"; then
        echo "  FAIL: Expected fake crontab -l calls were not observed"
        return 1
    fi
    if ! grep -q '^crontab .*tmp' "$CRONTAB_CALL_LOG"; then
        echo "  FAIL: Expected fake crontab apply call with temp file not observed"
        return 1
    fi

    echo "  PASS: Installer interactions were captured by fake crontab shim"
}

# Run all tests
echo "=== Running install_cron_entries.sh regression tests ==="
echo ""

# Ensure clean fake crontab state before tests
crontab -r

test_full_path_command_deduplication
test_quoted_command_deduplication
test_unclosed_managed_block_preserves_entries
test_mixed_user_and_managed_entries
test_clean_install
test_readme_uses_published_package_names
test_non_real_crontab_harness_is_used

echo ""
echo "=== All tests passed ==="
