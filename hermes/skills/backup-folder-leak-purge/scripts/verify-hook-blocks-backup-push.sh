#!/usr/bin/env bash
# verify-hook-blocks-backup-push.sh
# 3-test harness for a backup/ pre-push hook. Run BEFORE declaring the hook done.
# Tests:
#   1. forbidden path in main push → MUST exit 1
#   2. clean commit in main push → MUST exit 0
#   3. feature branch push (any commit) → MUST exit 0
#
# Usage: ./verify-hook-blocks-backup-push.sh <path-to-pre-push-hook> <remote-url>
#        (defaults: HOOK=.git/hooks/pre-push, REMOTE=https://github.com/jleechanorg/claude-commands.git)
#
# Bug-ref 2026-07-15: hook was silently broken due to wrong stdin field order.

set -uo pipefail

HOOK="${1:-.git/hooks/pre-push}"
REMOTE="${2:-https://github.com/jleechanorg/claude-commands.git}"
CLEAN_BASE_SHA="${CLEAN_BASE_SHA:-a30c037de034efc1e7f90a6969eac94010cd59fc}"
ZERO_SHA="0000000000000000000000000000000000000000"

if [[ ! -x "$HOOK" ]]; then
    echo "❌ HOOK not executable: $HOOK"
    exit 2
fi

# Create scratch worktree
SCRATCH=$(mktemp -d)
trap 'rm -rf "$SCRATCH"' EXIT
git worktree add --detach "$SCRATCH" "$CLEAN_BASE_SHA" >/dev/null 2>&1
cd "$SCRATCH" || exit 2

# === TEST 1: backup/ in commit, main push ===
echo "TEST 1: backup/ in commit, main push → must exit 1"
mkdir -p backup/Mac
echo "test secret" > backup/Mac/test.txt
git add -f backup/ >/dev/null
git commit -m "test: backup leak" --no-verify >/dev/null
BAD_SHA=$(git rev-parse HEAD)

EXIT_CODE=$(printf "refs/heads/main %s refs/heads/main %s\n" "$BAD_SHA" "$ZERO_SHA" \
    | "$HOOK" origin "$REMOTE" 2>/dev/null; echo $?)
if [[ "$EXIT_CODE" == "1" ]]; then
    echo "  ✅ PASS (exit 1)"
    TEST1_RESULT="pass"
else
    echo "  ❌ FAIL (exit $EXIT_CODE — hook silently passed!)"
    TEST1_RESULT="fail"
fi
echo

# Reset to clean tip
git reset --hard "$CLEAN_BASE_SHA" >/dev/null

# === TEST 2: clean commit, main push ===
echo "TEST 2: clean commit on clean tip, main push → must exit 0"
echo "clean" > clean.txt
git add clean.txt >/dev/null
git commit -m "test: clean" --no-verify >/dev/null
CLEAN_SHA=$(git rev-parse HEAD)

EXIT_CODE=$(printf "refs/heads/main %s refs/heads/main %s\n" "$CLEAN_SHA" "$ZERO_SHA" \
    | "$HOOK" origin "$REMOTE" 2>/dev/null; echo $?)
if [[ "$EXIT_CODE" == "0" ]]; then
    echo "  ✅ PASS (exit 0)"
    TEST2_RESULT="pass"
else
    echo "  ❌ FAIL (exit $EXIT_CODE — hook over-blocked a clean push!)"
    TEST2_RESULT="fail"
fi
echo

# === TEST 3: feature branch push (should pass regardless of content) ===
echo "TEST 3: feature branch push (any commit content) → must exit 0"
git reset --hard "$CLEAN_BASE_SHA" >/dev/null
mkdir -p backup/Mac
echo "test secret" > backup/Mac/test.txt
git add -f backup/ >/dev/null
git commit -m "test: backup leak on feat branch" --no-verify >/dev/null
FEAT_SHA=$(git rev-parse HEAD)

EXIT_CODE=$(printf "refs/heads/feat/x %s refs/heads/feat/x %s\n" "$FEAT_SHA" "$ZERO_SHA" \
    | "$HOOK" origin "$REMOTE" 2>/dev/null; echo $?)
if [[ "$EXIT_CODE" == "0" ]]; then
    echo "  ✅ PASS (exit 0)"
    TEST3_RESULT="pass"
else
    echo "  ❌ FAIL (exit $EXIT_CODE — hook blocked a feature branch push!)"
    TEST3_RESULT="fail"
fi

# Cleanup
cd - >/dev/null
git worktree remove --force "$SCRATCH" 2>/dev/null

echo
echo "================================"
if [[ "$TEST1_RESULT" == "pass" && "$TEST2_RESULT" == "pass" && "$TEST3_RESULT" == "pass" ]]; then
    echo "✅ All 3 tests passed — hook is wired correctly."
    exit 0
else
    echo "❌ Hook is broken. Tests failed: T1=$TEST1_RESULT T2=$TEST2_RESULT T3=$TEST3_RESULT"
    echo "   Likely cause: stdin field-order bug per references/git-hooks-pre-push-stdin-format.md"
    exit 1
fi