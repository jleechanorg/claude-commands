#!/bin/bash
# TDD Tests for ralph/lib/terminal_recorder.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/terminal_recorder.sh"

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
    FAIL=$((FAIL + 1)); echo "  ❌ $desc — not found: $path"
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

TMPDIR=$(mktemp -d)
trap 'tmux kill-session -t test-recorder 2>/dev/null; rm -rf "$TMPDIR"' EXIT

echo "═══ test_terminal_recorder.sh ═══"

# ─── Test: terminal_record_start creates log file ────────────────────────────

echo ""; echo "--- terminal_record_start ---"

# Create a tmux session for testing
tmux new-session -d -s test-recorder -x 120 -y 30 "echo 'Hello from tmux'; sleep 5" 2>/dev/null
sleep 1

LOG_FILE="$TMPDIR/terminal.log"
terminal_record_start "test-recorder" "$LOG_FILE"
sleep 2
terminal_record_stop

assert_file_exists "log file created" "$LOG_FILE"

TOTAL=$((TOTAL + 1))
if [ -s "$LOG_FILE" ]; then
  PASS=$((PASS + 1)); echo "  ✅ log file is non-empty"
else
  FAIL=$((FAIL + 1)); echo "  ❌ log file is empty"
fi

# ─── Test: terminal_snapshot captures pane content ───────────────────────────

echo ""; echo "--- terminal_snapshot ---"

SNAP_FILE="$TMPDIR/snapshot.txt"
# Start a new tmux session with known content
tmux kill-session -t test-recorder 2>/dev/null
tmux new-session -d -s test-recorder -x 120 -y 30 "echo 'Snapshot test content 12345'; sleep 5" 2>/dev/null
sleep 1

terminal_snapshot "test-recorder" "$SNAP_FILE"
assert_file_exists "snapshot created" "$SNAP_FILE"
assert_contains "snapshot has content" "$SNAP_FILE" "12345"

# ─── Test: terminal_to_srt generates captions ────────────────────────────────

echo ""; echo "--- terminal_to_srt ---"

# Create mock log file with timestamps (enough lines for multiple captions)
cat > "$TMPDIR/mock_log.txt" <<'LOG'
[2026-03-01 10:00:00] Starting Ralph iteration 1
[2026-03-01 10:00:05] Building project...
[2026-03-01 10:00:10] Tests passed: 3/3
[2026-03-01 10:00:15] Fixing story A-1
[2026-03-01 10:00:20] Story A-1 complete
[2026-03-01 10:00:25] Ralph completed all tasks!
LOG

SRT_FILE="$TMPDIR/terminal.srt"
terminal_to_srt "$TMPDIR/mock_log.txt" "$SRT_FILE"

assert_file_exists "SRT file created" "$SRT_FILE"
assert_contains "SRT has starting" "$SRT_FILE" "Starting Ralph"

TOTAL=$((TOTAL + 1))
if grep -qF -- "-->" "$SRT_FILE" 2>/dev/null; then
  PASS=$((PASS + 1)); echo "  ✅ SRT has timestamp format"
else
  FAIL=$((FAIL + 1)); echo "  ❌ SRT has timestamp format — --> not found"
fi

# ─── Test: terminal_render_video creates WebM ────────────────────────────────

echo ""; echo "--- terminal_render_video ---"

VIDEO_FILE="$TMPDIR/terminal.webm"
terminal_render_video "$TMPDIR/mock_log.txt" "$VIDEO_FILE" "$SRT_FILE"

assert_file_exists "WebM video created" "$VIDEO_FILE"

TOTAL=$((TOTAL + 1))
size=$(stat -f%z "$VIDEO_FILE" 2>/dev/null || stat --format=%s "$VIDEO_FILE" 2>/dev/null || echo 0)
if [ "$size" -gt 1000 ]; then
  PASS=$((PASS + 1)); echo "  ✅ video has content (${size} bytes)"
else
  FAIL=$((FAIL + 1)); echo "  ❌ video too small: ${size} bytes"
fi

# ─── Results ──────────────────────────────────────────────────────────────────

echo ""
echo "═══ Results: $PASS/$TOTAL passed ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
