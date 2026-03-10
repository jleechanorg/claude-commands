#!/bin/bash
# Ralph Evidence Recorder — Browser Proof Video
# Generic template — uses agent-browser to navigate and record the webapp.
#
# Ralph's PRD should include a story to customize this script with the
# correct selectors for the specific app being built.
#
# Usage: bash evidence_recorder.sh [--url http://localhost:PORT] [--evidence-dir DIR]
#
# Requires: agent-browser (https://github.com/nichochar/agent-browser)

set -uo pipefail

BASE_URL="http://localhost:${RALPH_APP_PORT:-5555}"
EVIDENCE_DIR="/tmp/ralph-run/evidence"

while [[ $# -gt 0 ]]; do
  case $1 in
    --url)          BASE_URL="$2"; shift 2 ;;
    --evidence-dir) EVIDENCE_DIR="$2"; shift 2 ;;
    *)              shift ;;
  esac
done

SS="$EVIDENCE_DIR/screenshots"
mkdir -p "$SS" "$EVIDENCE_DIR/captions" "$EVIDENCE_DIR/recordings"

echo "🎬 Ralph Browser Proof Recorder"
echo "   URL: $BASE_URL"
echo "   Evidence: $EVIDENCE_DIR"
echo ""

# Check deps
command -v agent-browser >/dev/null 2>&1 || { echo "❌ agent-browser not installed"; exit 1; }
curl -sf4 --connect-timeout 3 "$BASE_URL" >/dev/null 2>&1 || { echo "❌ Server not reachable at $BASE_URL"; exit 1; }

PASSED=0
TOTAL=0
SRT=""
SEC=0
RESULTS=()

mark() {
  TOTAL=$((TOTAL + 1))
  local id="$1" caption="$2" ok="$3"
  timeout 5 agent-browser screenshot "$SS/browser_$(printf '%02d' $TOTAL)_${id}.png" 2>/dev/null || true
  local a=$SEC b=$((SEC + 3)); SEC=$b
  local at=$(printf '%02d:%02d:%02d,000' $((a/3600)) $((a%3600/60)) $((a%60)))
  local bt=$(printf '%02d:%02d:%02d,000' $((b/3600)) $((b%3600/60)) $((b%60)))
  if [ "$ok" = "1" ]; then
    PASSED=$((PASSED + 1))
    echo "  [$TOTAL] ✅ $id: $caption"
    SRT+="${TOTAL}
${at} --> ${bt}
[PASS] $id: $caption

"
    RESULTS+=("| $TOTAL | $id | $caption | ✅ |")
  else
    echo "  [$TOTAL] ❌ $id: $caption"
    SRT+="${TOTAL}
${at} --> ${bt}
[FAIL] $id: $caption

"
    RESULTS+=("| $TOTAL | $id | $caption | ❌ |")
  fi
}

# ─── OPEN + START RECORDING ──────────────────────────────────────────────────

timeout 10 agent-browser open "$BASE_URL" 2>/dev/null || true
sleep 2
timeout 5 agent-browser record start "$EVIDENCE_DIR/app_flow.webm" 2>/dev/null || true
sleep 1

# ─── GENERIC TESTS ───────────────────────────────────────────────────────────
# These are basic smoke tests. Ralph should customize this file in its
# evidence instrumentation story (e.g A4) with app-specific selectors.

# Test 1: Homepage loads
TITLE=$(timeout 5 agent-browser get title 2>/dev/null || echo "")
[ -n "$TITLE" ] && OK=1 || OK=0
mark "HOMEPAGE" "Homepage loads — title: ${TITLE:-empty}" "$OK"
sleep 1

# Test 2: Page has content
COUNT=$(timeout 5 agent-browser get count "body *" 2>/dev/null || echo "0")
[ "$COUNT" -gt 5 ] 2>/dev/null && OK=1 || OK=0
mark "CONTENT" "Page has content — $COUNT elements" "$OK"
sleep 1

# Test 3: Screenshot of full page
timeout 5 agent-browser screenshot "$SS/full_page.png" 2>/dev/null && OK=1 || OK=0
mark "SCREENSHOT" "Full page screenshot captured" "$OK"

# ─── STOP + CLOSE ────────────────────────────────────────────────────────────

timeout 5 agent-browser record stop 2>/dev/null || true
sleep 1
timeout 3 agent-browser close 2>/dev/null || true

# ─── WRITE SRT ────────────────────────────────────────────────────────────────

echo "$SRT" > "$EVIDENCE_DIR/captions/browser_proof.srt"
echo ""
echo "  📝 SRT: $EVIDENCE_DIR/captions/browser_proof.srt"

# ─── WRITE REPORT ────────────────────────────────────────────────────────────

PCT=$((PASSED * 100 / TOTAL))
VID="$EVIDENCE_DIR/app_flow.webm"
cat > "$EVIDENCE_DIR/browser_proof.md" <<REPORT
# Browser Proof Report

**Date:** $(date -u +%Y-%m-%dT%H:%M:%SZ)
**URL:** $BASE_URL
**Result:** $PASSED/$TOTAL ($PCT%)

| # | Test | Caption | Result |
|---|------|---------|--------|
$(printf '%s\n' "${RESULTS[@]}")

**Video:** $([ -f "$VID" ] && echo "$(basename "$VID")" || echo "not captured")
REPORT

echo "  📋 Report: $EVIDENCE_DIR/browser_proof.md"
echo "  📊 Result: $PASSED/$TOTAL ($PCT%)"
[ -f "$VID" ] && echo "  🎬 Video: $VID"

exit $([ "$PASSED" -eq "$TOTAL" ] && echo 0 || echo 1)
