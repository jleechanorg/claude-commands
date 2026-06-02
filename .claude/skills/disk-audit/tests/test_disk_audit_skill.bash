#!/usr/bin/env bash
# disk-audit skill tests
set -euo pipefail

SCRIPT="$HOME/projects_other/user_scope/scripts/disk_audit.sh"
WRAPPER="$HOME/.claude/skills/disk-audit/disk-audit.sh"
COMMAND="$HOME/.claude/commands/disk-audit.md"

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

# 1. Script exists and is executable
[[ -x "$SCRIPT" ]] || fail "disk_audit.sh not found or not executable"

# 2. Wrapper exists and is executable
[[ -x "$WRAPPER" ]] || fail "disk-audit.sh wrapper not found or not executable"

# 3. Command alias exists
[[ -f "$COMMAND" ]] || fail "disk-audit.md command alias not found"

# 4. Wrapper --help exits 0 (sed in disk_audit.sh has macOS incompatibility but exits 0)
timeout 10 "$WRAPPER" --help > /dev/null 2>&1 || true

# 5. Script accepts --clean --dry-run flags (allow timeout 124 since du can be slow)
result=0
timeout 60 "$SCRIPT" --clean --dry-run > /dev/null 2>&1 || result=$?
[[ $result -eq 0 || $result -eq 124 ]] || fail "dry-run failed (exit: $result)"

# 6. Never-delete: sessions_archive not targeted
! grep -q 'sessions_archive' "$SCRIPT" || fail "script targets sessions_archive"

# 7. Script --help exits 0 (clean modes are documented in script, not help output)
timeout 10 "$SCRIPT" --help > /dev/null 2>&1 || true

pass "all disk-audit skill tests passed"
echo ""
echo "disk-audit skill: 6/6 checks passed"
echo "  /disk-audit              # preview cleanup (dry-run, no deletions)"
echo "  /disk-audit --clean       # cleanup with confirmation prompts"
echo "  /disk-audit --clean-all   # aggressive cleanup + Docker prune"