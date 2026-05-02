#!/usr/bin/env bash
# pre-commit-git-identity.sh
# Verifies git author identity matches expected jleechan2015 identity.
# Hook type: PreToolUse (PreToolUseHook blocks tool execution)
# If this script exits non-zero, the commit is blocked.

set -e

expected_name="jleechan2015"
expected_email="jleechan2015@users.noreply.github.com"

# Get actual identity — prefer --local (worktree/repo-level) over --global
actual_name=$(git config --get user.name 2>/dev/null || echo "")
actual_email=$(git config --get user.email 2>/dev/null || echo "")

if [[ "$actual_name" != "$expected_name" ]] || [[ "$actual_email" != "$expected_email" ]]; then
  echo "=== Git Identity Mismatch ===" >&2
  echo "Expected: $expected_name <$expected_email>" >&2
  echo "Actual:   $actual_name <$actual_email>" >&2
  echo "" >&2
  echo "Fix: git config --local user.name \"$expected_name\" \\" >&2
  echo "      \&\& git config --local user.email \"$expected_email\"" >&2
  echo "" >&2
  echo "Note: --local overrides --global in worktrees." >&2
  echo "       Worktrees have their own git config at .git/worktrees/<name>/config" >&2
  exit 1
fi
