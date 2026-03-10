#!/bin/bash
# TDD Tests for ralph/lib/evidence.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/evidence.sh"

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

assert_dir_exists() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" path="$2"
  if [ -d "$path" ]; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — dir not found: $path"
  fi
}

assert_contains() {
  TOTAL=$((TOTAL + 1))
  local desc="$1" file="$2" pattern="$3"
  if grep -q "$pattern" "$file" 2>/dev/null; then
    PASS=$((PASS + 1)); echo "  ✅ $desc"
  else
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — pattern '$pattern' not in $file"
  fi
}

# ─── Setup ────────────────────────────────────────────────────────────────────

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "═══ test_evidence.sh ═══"

# ─── Test: evidence_init creates directories ─────────────────────────────────

echo ""; echo "--- evidence_init ---"
EVIDENCE_DIR="$TMPDIR/evidence"

evidence_init "$EVIDENCE_DIR" >/dev/null 2>&1

assert_dir_exists "creates evidence root" "$EVIDENCE_DIR"
assert_dir_exists "creates screenshots dir" "$EVIDENCE_DIR/screenshots"
assert_dir_exists "creates recordings dir" "$EVIDENCE_DIR/recordings"
assert_dir_exists "creates captions dir" "$EVIDENCE_DIR/captions"

# ─── Test: evidence_captions generates SRT ────────────────────────────────────

echo ""; echo "--- evidence_captions ---"

# Create mock prd.json
cat > "$TMPDIR/prd.json" <<'JSON'
{"userStories":[
  {"id":"R1","title":"First story","passes":true},
  {"id":"R2","title":"Second story","passes":false}
]}
JSON

evidence_captions 1 "$TMPDIR/prd.json" "$EVIDENCE_DIR" >/dev/null 2>&1

assert_file_exists "creates SRT file" "$EVIDENCE_DIR/captions/iteration_1.srt"
assert_file_exists "creates markdown file" "$EVIDENCE_DIR/captions/iteration_1.md"
assert_contains "SRT has iteration number" "$EVIDENCE_DIR/captions/iteration_1.srt" "Iteration 1"
assert_contains "SRT has PASS tag" "$EVIDENCE_DIR/captions/iteration_1.srt" "PASS"
assert_contains "SRT has TODO tag" "$EVIDENCE_DIR/captions/iteration_1.srt" "TODO"
assert_contains "markdown has score" "$EVIDENCE_DIR/captions/iteration_1.md" "1/2"

# ─── Test: evidence_finalize creates summary ──────────────────────────────────

echo ""; echo "--- evidence_finalize ---"

METRICS_FILE="$TMPDIR/metrics.json"
echo '{"duration_human":"5m 30s"}' > "$METRICS_FILE"

# Create some fake evidence files
touch "$EVIDENCE_DIR/screenshots/test.png"
touch "$EVIDENCE_DIR/recordings/test.txt"
touch "$EVIDENCE_DIR/captions/test.srt"

evidence_finalize "$TMPDIR/prd.json" "$METRICS_FILE" "$EVIDENCE_DIR" >/dev/null 2>&1

assert_file_exists "creates evidence_summary.md" "$EVIDENCE_DIR/evidence_summary.md"
assert_contains "summary has result" "$EVIDENCE_DIR/evidence_summary.md" "1/2"
assert_contains "summary has screenshots" "$EVIDENCE_DIR/evidence_summary.md" "test.png"
assert_contains "summary has recordings" "$EVIDENCE_DIR/evidence_summary.md" "test.txt"

# ─── Results ──────────────────────────────────────────────────────────────────

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
