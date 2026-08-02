#!/usr/bin/env bash
# test_watchdog_exit4_on_handoff_fail.sh — contract test for the watchdog probe-mismatch bug fix
#
# Verifies that cloud-build-bastion-watchdog.sh v1.2.0+ correctly detects the
# structural gap where banner users (cloud-bastion@, enroll@) return OK but
# handoff users (git@, $USER@, cloud-build@) return Permission denied (publickey).
# The v1.1.0 watchdog exited 0 in this state ("watchdog-lying-about-success").
# The v1.2.0+ watchdog MUST exit 4.
#
# Provenance: bug verified 2026-07-20 on Slack thread C09GRLXF9GR/p1784582518.247009.
# This test was added in the same commit that fixed the bug.

set -uo pipefail

WATCHDOG="${WATCHDOG:-$HOME/.hermes/scripts/cloud-build-bastion-watchdog.sh}"
TEST_NAME="watchdog-exit4-on-handoff-fail"
PASS=0
FAIL=0

note() { printf '  %s\n' "$*"; }
ok()   { printf '  ✅ %s\n' "$*"; PASS=$((PASS+1)); }
bad()  { printf '  ❌ %s\n' "$*"; FAIL=$((FAIL+1)); }

printf '%s\n' "=== $TEST_NAME ==="

# Test 1: watchdog script exists
if [[ -f "$WATCHDOG" ]]; then
  ok "watchdog script exists: $WATCHDOG"
else
  bad "watchdog script missing: $WATCHDOG"
  printf '%s\n' "PASS=$PASS FAIL=$FAIL"
  exit 1
fi

# Test 2: watchdog script is executable
if [[ -x "$WATCHDOG" ]]; then
  ok "watchdog is executable"
else
  bad "watchdog is not executable"
fi

# Test 3: handoff-user probe block exists in the script (the bug fix)
if grep -q 'HANDOFF_USERS=( "git@\$HOST" "$USER@\$HOST" "cloud-build@\$HOST" )' "$WATCHDOG"; then
  ok "handoff-user probe block present (the v1.2.0 fix)"
else
  bad "handoff-user probe block missing — bug fix not applied"
fi

# Test 4: exit code 4 logic is present
if grep -q 'BASTION_OK && ENROLL_OK && !HANDOFF_OK' "$WATCHDOG"; then
  ok "exit=4 verdict logic present"
else
  bad "exit=4 verdict logic missing — bug fix incomplete"
fi

# Test 5: exit=4 documented in header comments
if grep -q 'exit=4' "$WATCHDOG"; then
  ok "exit=4 documented in header comments"
else
  bad "exit=4 not documented in header"
fi

# Test 6: live-run exits 4 when handoff users fail (current state of this Mac)
LOG="$(mktemp)"
bash "$WATCHDOG" >"$LOG" 2>&1
ACTUAL_EXIT=$?
if (( ACTUAL_EXIT == 4 )); then
  ok "live run correctly exits 4 (handoff-fail-with-banner-ok)"
  note "log excerpt:"
  note "$(grep -E 'handoff user|verdict' "$LOG" | head -8 | sed 's/^/    /')"
elif (( ACTUAL_EXIT == 1 )); then
  bad "live run exits 1 (auth-fail) — banner users should still pass on this Mac"
  note "expected exit=4 (banner users OK + handoff users fail)"
  note "$(cat "$LOG" | tail -15 | sed 's/^/    /')"
elif (( ACTUAL_EXIT == 0 )); then
  bad "live run exits 0 — WATCHDOG IS STILL LYING. Bug fix did not take effect."
  note "$(cat "$LOG" | tail -15 | sed 's/^/    /')"
else
  bad "live run exits $ACTUAL_EXIT (unexpected)"
  note "$(cat "$LOG" | tail -15 | sed 's/^/    /')"
fi
rm -f "$LOG"

# Test 7: cloud-bastion@ probe still works (no regression on banner path)
BASTION_BANNER="$(ssh -i ~/.ssh/cloud-build/id_ed25519 -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes -o UserKnownHostsFile=~/.ssh/cloud-build/known_hosts \
  -o ConnectTimeout=5 -o BatchMode=yes -T 'cloud-bastion@cloud.superpowers.build' 2>&1 || true)"
if [[ "$BASTION_BANNER" == *"interactive shell is not permitted"* ]] || \
   [[ "$BASTION_BANNER" == *"only git fetch/push/archive is permitted"* ]]; then
  ok "cloud-bastion banner still works (no regression on banner path)"
else
  bad "cloud-bastion banner broken: $BASTION_BANNER"
fi

# Summary
printf '\n=== %s — PASS=%d FAIL=%d ===\n' "$TEST_NAME" "$PASS" "$FAIL"
if (( FAIL > 0 )); then
  exit 1
fi
exit 0
