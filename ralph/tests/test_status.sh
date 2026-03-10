#!/bin/bash
# TDD Tests for ralph/lib/status.sh — Status monitor display
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/status.sh"

PASS=0; FAIL=0; TOTAL=0

assert_contains() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" text="$2" pattern="$3"
  if echo "$text" | grep -q "$pattern" 2>/dev/null; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — pattern '$pattern' not found"
  fi
}

assert_not_empty() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" text="$2"
  if [ -n "$text" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — output was empty"
  fi
}

# ─── Setup ────────────────────────────────────────────────────────────────────

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Create mock prd.json
cat > "$TMPDIR/prd.json" <<'JSON'
{"userStories":[
  {"id":"A-1","title":"First story","passes":true},
  {"id":"A-2","title":"Second story","passes":false},
  {"id":"B-1","title":"Third story","passes":true}
]}
JSON

# Create mock progress file
cat > "$TMPDIR/progress.txt" <<'PROG'
# Ralph Progress Log
Started: 2026-01-01
---
## Iteration 1
A-1: ✅ PASSED
PROG

# Init a dummy git repo for status
(cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q) 2>/dev/null

echo "═══ test_status.sh ═══"

# ─── Test: format_progress_bar ───────────────────────────────────────────────

echo ""; echo "--- format_progress_bar ---"

bar=$(format_progress_bar 5 10 20)
assert_contains "bar has filled chars" "$bar" "█"
assert_contains "bar has empty chars" "$bar" "░"
assert_contains "bar shows percentage" "$bar" "50%"

bar_zero=$(format_progress_bar 0 10 20)
assert_contains "zero progress all empty" "$bar_zero" "░"

bar_full=$(format_progress_bar 10 10 20)
assert_contains "full progress all filled" "$bar_full" "100%"

# ─── Test: format_story_status ───────────────────────────────────────────────

echo ""; echo "--- format_story_status ---"

output=$(format_story_status "$TMPDIR/prd.json")
assert_not_empty "story status has output" "$output"
assert_contains "shows phase A" "$output" "A-"
assert_contains "shows phase B" "$output" "B-"
assert_contains "shows DONE or WIP" "$output" "DONE\|WIP"

# ─── Test: format_next_story ─────────────────────────────────────────────────

echo ""; echo "--- format_next_story ---"

next=$(format_next_story "$TMPDIR/prd.json")
assert_contains "next story is A-2" "$next" "A-2"
assert_contains "next has title" "$next" "Second story"

# ─── Test: format_progress_tail ──────────────────────────────────────────────

echo ""; echo "--- format_progress_tail ---"

tail_out=$(format_progress_tail "$TMPDIR/progress.txt" 5)
assert_not_empty "progress tail has output" "$tail_out"
assert_contains "tail shows PASSED" "$tail_out" "PASSED"

# ─── Results ──────────────────────────────────────────────────────────────────

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
