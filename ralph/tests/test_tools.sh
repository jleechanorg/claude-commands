#!/bin/bash
# TDD Tests for ralph/lib/tools.sh — CLI tool adapters
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/tools.sh"

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
  if echo "$text" | grep -qF -- "$pattern" 2>/dev/null; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — pattern '$pattern' not found in: $text"
  fi
}

echo "═══ test_tools.sh ═══"

# ─── Test: resolve_tool_cmd returns correct commands ─────────────────────────

echo ""; echo "--- resolve_tool_cmd ---"

cmd=$(resolve_tool_cmd "claude")
assert_contains "claude uses --dangerously-skip-permissions" "$cmd" "dangerously-skip-permissions"
assert_contains "claude uses -p flag" "$cmd" " -p"

cmd=$(resolve_tool_cmd "minimax")
assert_contains "minimax uses claude binary" "$cmd" "claude"
assert_contains "minimax uses --print mode" "$cmd" "--print"

cmd=$(resolve_tool_cmd "codex")
assert_contains "codex uses exec --full-auto" "$cmd" "exec --full-auto"

cmd=$(resolve_tool_cmd "amp")
TOTAL=$((TOTAL + 1))
if echo "$cmd" | grep -qF -- "-x"; then
  PASS=$((PASS + 1)); echo "  ✅ amp uses -x flag"
else
  FAIL=$((FAIL + 1)); echo "  ❌ amp uses -x flag — not found in: $cmd"
fi

# ─── Test: unknown tool returns error ────────────────────────────────────────

echo ""; echo "--- unknown tool ---"

result=$(resolve_tool_cmd "unknown_tool" 2>&1) && status=0 || status=$?
assert_eq "unknown tool returns non-zero" "1" "$status"

# ─── Test: list_supported_tools ──────────────────────────────────────────────

echo ""; echo "--- list_supported_tools ---"

tools=$(list_supported_tools)
assert_contains "lists claude" "$tools" "claude"
assert_contains "lists minimax" "$tools" "minimax"
assert_contains "lists codex" "$tools" "codex"
assert_contains "lists amp" "$tools" "amp"

# ─── Test: tool_needs_stdin ──────────────────────────────────────────────────

echo ""; echo "--- tool_needs_stdin ---"

assert_eq "claude uses stdin" "yes" "$(tool_needs_stdin claude)"
assert_eq "minimax uses stdin" "yes" "$(tool_needs_stdin minimax)"
assert_eq "amp uses stdin" "yes" "$(tool_needs_stdin amp)"
assert_eq "codex uses arg" "no" "$(tool_needs_stdin codex)"

# ─── Results ──────────────────────────────────────────────────────────────────

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
