#!/bin/bash
# TDD Tests for ralph/lib/metrics.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/metrics.sh"

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

assert_file_exists() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" path="$2"
  if [ -f "$path" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — file not found: $path"
  fi
}

assert_json_field() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" file="$2" field="$3" expected="$4"
  local actual
  actual=$(python3 -c "import json; print(json.load(open('$file'))['$field'])" 2>/dev/null || echo "MISSING")
  if [ "$expected" = "$actual" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc"; echo "     expected: $expected"; echo "     actual:   $actual"
  fi
}

# ─── Setup ────────────────────────────────────────────────────────────────────

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "═══ test_metrics.sh ═══"

# ─── Test: record_metrics creates JSON ────────────────────────────────────────

echo ""; echo "--- record_metrics creates JSON ---"

cat > "$TMPDIR/prd.json" <<'JSON'
{"userStories":[
  {"id":"R1","title":"Story 1","passes":true},
  {"id":"R2","title":"Story 2","passes":true},
  {"id":"R3","title":"Story 3","passes":false}
]}
JSON

METRICS_FILE="$TMPDIR/metrics.json"
PROGRESS_FILE="$TMPDIR/progress.txt"
echo "test" > "$PROGRESS_FILE"
mkdir -p "$TMPDIR/workspace"

RUN_START=$(($(date +%s) - 120))  # 2 minutes ago
record_metrics "complete" "$TMPDIR/prd.json" "$METRICS_FILE" "$TMPDIR/workspace" "$PROGRESS_FILE" "claude" "$RUN_START" >/dev/null 2>&1

assert_file_exists "creates metrics.json" "$METRICS_FILE"
assert_json_field "outcome is complete" "$METRICS_FILE" "outcome" "complete"
assert_json_field "stories_total is 3" "$METRICS_FILE" "stories_total" "3"
assert_json_field "stories_passed is 2" "$METRICS_FILE" "stories_passed" "2"
assert_json_field "tool is claude" "$METRICS_FILE" "tool" "claude"
assert_json_field "workspace correct" "$METRICS_FILE" "workspace" "$TMPDIR/workspace"

# ─── Test: duration calculation ──────────────────────────────────────────────

echo ""; echo "--- duration calculation ---"

dur=$(python3 -c "import json; print(json.load(open('$METRICS_FILE'))['duration_seconds'])" 2>/dev/null)
TOTAL=$((TOTAL + 1))
if [ "$dur" -ge 118 ] 2>/dev/null && [ "$dur" -le 125 ] 2>/dev/null; then
  PASS=$((PASS + 1)); echo "  ✅ duration ~120s (got ${dur}s)"
else
  FAIL=$((FAIL + 1)); echo "  ❌ duration should be ~120s, got: $dur"
fi

# ─── Test: duration_human format ─────────────────────────────────────────────

echo ""; echo "--- duration_human format ---"

human=$(python3 -c "import json; print(json.load(open('$METRICS_FILE'))['duration_human'])" 2>/dev/null)
TOTAL=$((TOTAL + 1))
if echo "$human" | grep -qE "^[0-9]+m [0-9]+s$"; then
  PASS=$((PASS + 1)); echo "  ✅ duration_human format: $human"
else
  FAIL=$((FAIL + 1)); echo "  ❌ duration_human bad format: $human"
fi

# ─── Results ──────────────────────────────────────────────────────────────────

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
