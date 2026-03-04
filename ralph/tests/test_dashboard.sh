#!/bin/bash
# TDD Tests for ralph/lib/dashboard.py — Dashboard server
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD_PY="$SCRIPT_DIR/lib/dashboard.py"

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

assert_file_exists() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" path="$2"
  if [ -f "$path" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — file not found: $path"
  fi
}

# ─── Setup ────────────────────────────────────────────────────────────────────

TMPDIR=$(mktemp -d)
trap 'lsof -ti:19450 2>/dev/null | xargs kill 2>/dev/null; rm -rf "$TMPDIR"' EXIT

# Create mock prd.json
cat > "$TMPDIR/prd.json" <<'JSON'
{"userStories":[
  {"id":"A1","title":"First story","passes":true},
  {"id":"A2","title":"Second story","passes":false}
]}
JSON

# Create mock progress file
echo "# Progress" > "$TMPDIR/progress.txt"

# Create mock dashboard HTML
echo "<html><body>Dashboard</body></html>" > "$TMPDIR/dashboard.html"

echo "═══ test_dashboard.sh ═══"

# ─── Test: dashboard.py exists and is valid Python ───────────────────────────

echo ""; echo "--- dashboard.py basics ---"

assert_file_exists "dashboard.py exists" "$DASHBOARD_PY"

TOTAL=$((TOTAL + 1))
if python3 -c "import py_compile; py_compile.compile('$DASHBOARD_PY', doraise=True)" 2>/dev/null; then
  PASS=$((PASS + 1)); echo "  ✅ dashboard.py compiles"
else
  FAIL=$((FAIL + 1)); echo "  ❌ dashboard.py has syntax errors"
fi

# ─── Test: dashboard responds to /api/status ─────────────────────────────────

echo ""; echo "--- dashboard API ---"

# Start dashboard on test port
PRD_FILE="$TMPDIR/prd.json" \
PROGRESS_FILE="$TMPDIR/progress.txt" \
DASHBOARD_HTML="$TMPDIR/dashboard.html" \
REPO_ROOT="$TMPDIR" \
python3 "$DASHBOARD_PY" --port 19450 &
DASH_PID=$!
sleep 1

# Test /api/status endpoint
TOTAL=$((TOTAL + 1))
status_code=$(curl -sf4 --connect-timeout 3 -o "$TMPDIR/api_response.json" -w "%{http_code}" http://127.0.0.1:19450/api/status 2>/dev/null || echo "000")
if [ "$status_code" = "200" ]; then
  PASS=$((PASS + 1)); echo "  ✅ /api/status returns 200"
else
  FAIL=$((FAIL + 1)); echo "  ❌ /api/status returned: $status_code"
fi

# Test response has required fields
if [ -f "$TMPDIR/api_response.json" ]; then
  api=$(cat "$TMPDIR/api_response.json")
  assert_contains "response has total" "$api" '"total"'
  assert_contains "response has passed" "$api" '"passed"'
  assert_contains "response has stories" "$api" '"stories"'

  total_val=$(python3 -c "import json; print(json.load(open('$TMPDIR/api_response.json'))['total'])" 2>/dev/null || echo "?")
  assert_eq "total is 2" "2" "$total_val"

  passed_val=$(python3 -c "import json; print(json.load(open('$TMPDIR/api_response.json'))['passed'])" 2>/dev/null || echo "?")
  assert_eq "passed is 1" "1" "$passed_val"
fi

# Test / returns dashboard HTML
TOTAL=$((TOTAL + 1))
root_code=$(curl -sf4 --connect-timeout 3 -o /dev/null -w "%{http_code}" http://127.0.0.1:19450/ 2>/dev/null || echo "000")
if [ "$root_code" = "200" ]; then
  PASS=$((PASS + 1)); echo "  ✅ / returns 200 (dashboard HTML)"
else
  FAIL=$((FAIL + 1)); echo "  ❌ / returned: $root_code"
fi

# Clean up
kill $DASH_PID 2>/dev/null

# ─── Results ──────────────────────────────────────────────────────────────────

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
