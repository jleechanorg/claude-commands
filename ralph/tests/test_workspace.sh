#!/bin/bash
# TDD Tests for ralph/lib/workspace.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/workspace.sh"

PASS=0; FAIL=0; TOTAL=0

assert_eq() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc"; echo "     expected: $expected"; echo "     actual:   $actual"
  fi
}

assert_contains() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" text="$2" pattern="$3"
  if echo "$text" | grep -q "$pattern" 2>/dev/null; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — pattern '$pattern' not found"
  fi
}

assert_not_contains() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" text="$2" pattern="$3"
  if ! echo "$text" | grep -q "$pattern" 2>/dev/null; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — pattern '$pattern' was found (should not be)"
  fi
}

# ─── Setup ────────────────────────────────────────────────────────────────────

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "═══ test_workspace.sh ═══"

# ─── Test: resolve_workspace defaults to repo root ───────────────────────────

echo ""; echo "--- resolve_workspace ---"

result=$(resolve_workspace "" "/fake/repo/root")
assert_eq "default workspace is repo root" "/fake/repo/root" "$result"

result=$(resolve_workspace "/tmp/custom-ws" "/fake/repo/root")
assert_eq "custom workspace is used" "/tmp/custom-ws" "$result"

# ─── Test: build_prompt resolves paths ────────────────────────────────────────

echo ""; echo "--- build_prompt ---"

# Create mock CLAUDE.md
cat > "$TMPDIR/CLAUDE.md" <<'MD'
Read `prd.json` for stories.
Write progress to `progress.txt`.
MD

PRD="$TMPDIR/prd.json"
PROG="$TMPDIR/progress.txt"
echo '{}' > "$PRD"
echo 'test' > "$PROG"

prompt=$(build_prompt "$TMPDIR/CLAUDE.md" "$PRD" "$PROG" "/tmp/my-workspace")

assert_contains "prompt has absolute prd path" "$prompt" "$PRD"
assert_contains "prompt has absolute progress path" "$prompt" "$PROG"
assert_contains "prompt has workspace header" "$prompt" "/tmp/my-workspace"
assert_not_contains "prompt has no relative prd.json" "$prompt" '`prd.json`'

# ─── Test: build_prompt without custom workspace ─────────────────────────────

echo ""; echo "--- build_prompt without workspace ---"

# When workspace == repo root, no workspace header
prompt2=$(build_prompt "$TMPDIR/CLAUDE.md" "$PRD" "$PROG" "")
assert_not_contains "no workspace header when empty" "$prompt2" "Workspace:"

# ─── Test: prepare_runner unsets CLAUDECODE ───────────────────────────────────

echo ""; echo "--- prepare_runner ---"

runner_file="$TMPDIR/runner.sh"
prepare_runner "$runner_file" "/tmp/ws" "claude" "$TMPDIR/prompt.md" "$TMPDIR/log.txt" "$TMPDIR/transcript.txt"

TOTAL=$((TOTAL + 1))
if [ -f "$runner_file" ]; then
  PASS=$((PASS + 1)); echo "  ✅ runner file created"
else
  FAIL=$((FAIL + 1)); echo "  ❌ runner file not created"
fi

assert_contains "runner unsets CLAUDECODE" "$(cat "$runner_file")" "unset CLAUDECODE"
assert_contains "runner cd to workspace" "$(cat "$runner_file")" "/tmp/ws"
assert_contains "runner pipes to tool" "$(cat "$runner_file")" "claude"
assert_contains "runner tees to log" "$(cat "$runner_file")" "$TMPDIR/log.txt"
assert_contains "runner tees to transcript" "$(cat "$runner_file")" "$TMPDIR/transcript.txt"

# ─── Test: runner is executable ──────────────────────────────────────────────

TOTAL=$((TOTAL + 1))
if [ -x "$runner_file" ]; then
  PASS=$((PASS + 1)); echo "  ✅ runner is executable"
else
  FAIL=$((FAIL + 1)); echo "  ❌ runner not executable"
fi

# ─── Results ──────────────────────────────────────────────────────────────────

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
