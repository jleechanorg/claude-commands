#!/bin/bash
# TDD Tests for ralph.sh command paths and run cleanup semantics
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0
TOTAL=0

assert_eq() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1))
    echo "  ❌ $desc"
    echo "     expected: $expected"
    echo "     actual:   $actual"
  fi
}

assert_contains() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" text="$2" pattern="$3"
  if echo "$text" | grep -qF "$pattern"; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — pattern '$pattern' not found"
  fi
}

assert_file_exists() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" path="$2"
  if [ -f "$path" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — file not found: $path"
  fi
}

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
RUNTIME_FIXTURE="$TMPDIR/ralph"

mkdir -p "$RUNTIME_FIXTURE"
cp -R "$SCRIPT_DIR/." "$RUNTIME_FIXTURE/"

mkdir -p "$RUNTIME_FIXTURE/bin"

cat > "$RUNTIME_FIXTURE/bin/claude" <<'SH'
#!/bin/bash
echo "Simulated claude failure"
exit 1
SH
chmod +x "$RUNTIME_FIXTURE/bin/claude"

cat > "$RUNTIME_FIXTURE/bin/open" <<'SH'
#!/bin/bash
echo "open stub called"
exit 0
SH
chmod +x "$RUNTIME_FIXTURE/bin/open"

cat > "$RUNTIME_FIXTURE/bin/xdg-open" <<'SH'
#!/bin/bash
echo "xdg-open stub called"
exit 0
SH
chmod +x "$RUNTIME_FIXTURE/bin/xdg-open"

cat > "$RUNTIME_FIXTURE/bin/tmux" <<'SH'
#!/bin/bash
if [ "$1" = "capture-pane" ]; then
  echo "tmux capture frame"
  exit 0
fi
exit 0
SH
chmod +x "$RUNTIME_FIXTURE/bin/tmux"

cat > "$RUNTIME_FIXTURE/bin/python3" <<'SH'
#!/bin/bash
if [[ "$*" == *"lib/dashboard.py"* ]]; then
  # Simulate a fast dashboard process for command coverage.
  exit 0
fi
exec "$RALPH_TEST_PYTHON" "$@"
SH
chmod +x "$RUNTIME_FIXTURE/bin/python3"

cat > "$RUNTIME_FIXTURE/prd.json" <<'JSON'
{"userStories":[
  {"id":"R1","title":"First story","passes":false},
  {"id":"R2","title":"Second story","passes":true}
]}
JSON

cat > "$RUNTIME_FIXTURE/progress.txt" <<'PROG'
# Ralph Progress Log
Started: 2026-01-01
---
## Iteration 1
R1: ✅ PASSED
PROG

mkdir -p "$RUNTIME_FIXTURE/workspace"

run_ralph() {
  local out_file="$TMPDIR/run_ralph.out"
  PATH="$RUNTIME_FIXTURE/bin:$PATH" \
  RALPH_TEST_PYTHON="$(command -v python3)" \
  bash "$RUNTIME_FIXTURE/ralph.sh" "$@" >"$out_file" 2>&1
  RUN_STATUS=$?
  RUN_OUTPUT="$(cat "$out_file")"
}

echo "═══ test_ralph.sh ═══"

echo ""
echo "--- cmd_help ---"
run_ralph help
assert_eq "help returns 0" "0" "$RUN_STATUS"
assert_contains "help includes commands header" "$RUN_OUTPUT" "Usage: ./ralph.sh <command> [options]"

echo ""
echo "--- cmd_status ---"
run_ralph status
assert_eq "status returns 0" "0" "$RUN_STATUS"
assert_contains "status shows header" "$RUN_OUTPUT" "🐺 RALPH STATUS MONITOR"
assert_contains "status shows progress line" "$RUN_OUTPUT" "Progress:"

echo ""
echo "--- cmd_dashboard ---"
run_ralph dashboard
assert_eq "dashboard returns 0" "0" "$RUN_STATUS"
assert_contains "dashboard starts" "$RUN_OUTPUT" "🐺 Ralph Dashboard starting"
assert_contains "dashboard stop hint" "$RUN_OUTPUT" "Press Ctrl+C to stop"
run_ralph dashboard --open
assert_eq "dashboard --open returns 0" "0" "$RUN_STATUS"
assert_contains "dashboard --open uses browser opener" "$RUN_OUTPUT" "open stub called"

echo ""
echo "--- cmd_run cleanup on failure ---"
rm -rf /tmp/ralph-run
rm -f "$RUNTIME_FIXTURE/metrics.json"
run_ralph run 1 --tool claude --workspace "$RUNTIME_FIXTURE/workspace"
assert_eq "failing run returns non-zero" "1" "$RUN_STATUS"
assert_contains "failing run reports tool failure" "$RUN_OUTPUT" "Error: claude failed on iteration 1"
assert_file_exists "run creates metrics file" "$RUNTIME_FIXTURE/metrics.json"
assert_file_exists "run finalizes evidence summary" "/tmp/ralph-run/evidence/evidence_summary.md"
RUN_OUTCOME=$(python3 -c "import json; print(json.load(open('$RUNTIME_FIXTURE/metrics.json')).get('outcome',''))")
assert_eq "run records agent_error outcome" "agent_error" "$RUN_OUTCOME"
assert_file_exists "run captures terminal log" "/tmp/ralph-run/evidence/captions/terminal.srt"

echo ""
echo "--- cmd_run minimax requires api key ---"
cat > "$RUNTIME_FIXTURE/prd.json" <<'JSON'
{"userStories":[
  {"id":"R1","title":"First story","passes":false},
  {"id":"R2","title":"Second story","passes":true}
]}
JSON
run_ralph run 1 --tool minimax --workspace "$RUNTIME_FIXTURE/workspace"
assert_eq "minimax without key returns config error" "2" "$RUN_STATUS"
assert_contains "minimax without key prints required message" "$RUN_OUTPUT" "Error: MINIMAX_API_KEY is required for --tool minimax"


echo ""
echo "--- cmd_run exits early when PRD already complete ---"
cat > "$RUNTIME_FIXTURE/prd.json" <<'JSON'
{"userStories":[
  {"id":"R1","title":"First story","passes":true},
  {"id":"R2","title":"Second story","passes":true}
]}
JSON
run_ralph run 1 --tool claude --workspace "$RUNTIME_FIXTURE/workspace"
assert_eq "completed PRD run returns 0" "0" "$RUN_STATUS"
assert_contains "completed PRD reports no-op completion" "$RUN_OUTPUT" "All stories in PRD already pass. Nothing to run."

run_ralph run 1 --tool minimax --workspace "$RUNTIME_FIXTURE/workspace"
assert_eq "completed PRD minimax run returns 0 without key" "0" "$RUN_STATUS"
assert_contains "completed PRD minimax reports no-op completion" "$RUN_OUTPUT" "All stories in PRD already pass. Nothing to run."

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
