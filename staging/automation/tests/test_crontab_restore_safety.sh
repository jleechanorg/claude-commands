#!/bin/bash
# Unit tests for install_cron_entries.sh - crontab restore safety
# Tests that user entries are never lost during script runs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$(mktemp -d)"
TEST_BIN_DIR="$TEST_DIR/bin"
FAKE_CRONTAB_FILE="$TEST_DIR/fake_system_crontab.txt"
export HOME="$TEST_DIR/home"
mkdir -p "$TEST_BIN_DIR"
mkdir -p "$HOME"
trap 'rm -rf "$TEST_DIR"' EXIT

cat >"$TEST_BIN_DIR/crontab" <<'EOF'
#!/bin/bash
set -euo pipefail

fake_file="${FAKE_CRONTAB_FILE:?FAKE_CRONTAB_FILE must be set}"
arg="${1:-}"

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
export PATH="$TEST_BIN_DIR:$PATH"

if [[ "$(command -v crontab)" != "$TEST_BIN_DIR/crontab" ]]; then
    echo "FAIL: fake crontab shim is not active" >&2
    exit 1
fi

echo "=== install_cron_entries.sh Safety Tests ==="

# Test 1: User entries outside managed block must be preserved
test_user_entries_preserved() {
    echo ""
    echo "Test 1: User entries outside managed block must be preserved"
    crontab -r

    TEST_TEMPLATE=$(mktemp "$TEST_DIR/template.XXXXXX")
    cat > "$TEST_TEMPLATE" <<'EOF'
PATH=$HOME/.local/bin
# [CRON-JOB-ID: pr-monitor] Run PR monitoring
0 */2 * * * jleechanorg-pr-monitor --max-prs 10
EOF

    USER_CRON='GITHUB_TOKEN=ghp_xxx
PATH=$HOME/.local/bin:/usr/bin
0 */2 * * * jleechanorg-pr-monitor --max-prs 5 >> /custom/path/log.log 2>&1
0 9 * * * /usr/bin/curl https://example.com/health
*/15 * * * * ~/actions-runner/monitor.sh
# === Automation entries (managed by install_cron_entries.sh) ===
PATH=$HOME/.local/bin
0 */2 * * * jleechanorg-pr-monitor --max-prs 10
# === End automation entries ===
0 12 * * * daily-task'

    echo "$USER_CRON" | crontab -
    CRON_FILE="$TEST_TEMPLATE" "$SCRIPT_DIR/install_cron_entries.sh"
    RESULT=$(crontab -l)

    local passed=1
    if echo "$RESULT" | grep -q "GITHUB_TOKEN=ghp_xxx"; then echo "  PASS: GITHUB_TOKEN preserved"; else echo "  FAIL: GITHUB_TOKEN LOST"; passed=0; fi
    if echo "$RESULT" | grep -q "curl https://example.com/health"; then echo "  PASS: User cron preserved"; else echo "  FAIL: User cron LOST"; passed=0; fi
    if echo "$RESULT" | grep -q "/custom/path/log.log"; then echo "  PASS: Custom args preserved"; else echo "  FAIL: Custom args LOST"; passed=0; fi
    if echo "$RESULT" | grep -q "actions-runner/monitor.sh"; then echo "  PASS: Post-block preserved"; else echo "  FAIL: Post-block LOST"; passed=0; fi

    rm -f "$TEST_TEMPLATE"
    [[ "$passed" -eq 1 ]]
}

# Test 2: Managed block should be replaced
test_managed_block_replaced() {
    echo ""
    echo "Test 2: Managed block should be replaced with template"
    crontab -r

    TEST_TEMPLATE=$(mktemp "$TEST_DIR/template.XXXXXX")
    cat > "$TEST_TEMPLATE" <<'EOF'
PATH=$HOME/.local/bin
# [CRON-JOB-ID: pr-monitor] New version
0 */2 * * * jleechanorg-pr-monitor --max-prs 99
EOF

    USER_CRON='PATH=/usr/bin
# === Automation entries (managed by install_cron_entries.sh) ===
PATH=$OLD/path
0 */2 * * * jleechanorg-pr-monitor --max-prs 10
# === End automation entries ==='

    echo "$USER_CRON" | crontab -
    CRON_FILE="$TEST_TEMPLATE" "$SCRIPT_DIR/install_cron_entries.sh"
    RESULT=$(crontab -l)

    rm -f "$TEST_TEMPLATE"
    if echo "$RESULT" | grep -q "max-prs 99"; then
        echo "  PASS: Managed block replaced"
        return 0
    else
        echo "  FAIL: Managed block NOT replaced"
        return 1
    fi
}

# Test 3: Unclosed managed block should NOT lose user entries
test_unclosed_block_safety() {
    echo ""
    echo "Test 3: Unclosed managed block should NOT lose user entries"
    crontab -r

    TEST_TEMPLATE=$(mktemp "$TEST_DIR/template.XXXXXX")
    cat > "$TEST_TEMPLATE" <<'EOF'
PATH=$HOME/.local/bin
0 */2 * * * jleechanorg-pr-monitor --max-prs 10
EOF

    USER_CRON='PATH=/usr/bin
0 9 * * * user-before
# === Automation entries (managed by install_cron_entries.sh)
0 */2 * * * old-command
0 12 * * * user-after'

    echo "$USER_CRON" | crontab -
    CRON_FILE="$TEST_TEMPLATE" "$SCRIPT_DIR/install_cron_entries.sh"
    RESULT=$(crontab -l)

    local passed=1
    if echo "$RESULT" | grep -q "user-before"; then echo "  PASS: Pre-block preserved"; else echo "  FAIL: Pre-block LOST"; passed=0; fi
    if echo "$RESULT" | grep -q "user-after"; then echo "  PASS: Post-block preserved"; else echo "  FAIL: Post-block LOST"; passed=0; fi

    rm -f "$TEST_TEMPLATE"
    [[ "$passed" -eq 1 ]]
}

# Run tests
test_user_entries_preserved
test_managed_block_replaced
test_unclosed_block_safety

echo ""
echo "=== All tests completed ==="
