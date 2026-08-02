#!/usr/bin/env bash
# verify-no-personal-leaks.sh
#
# Re-runnable pre-push gate for sanitized public-example files.
# Runs a battery of greps against a target file looking for personal
# references that should NOT appear in a public-facing example. Exits
# 0 only when zero matches are found across all patterns.
#
# Usage:
#   ./verify-no-personal-leaks.sh <file-to-check>
#
# Customize the LEAK_PATTERNS array for your environment. The defaults
# below catch the common Jeffrey/Hermes/MacBook-specific leaks; replace
# or extend them with your own identifiers before publishing elsewhere.
#
# This is the personal-reference counterpart to outbound-secret-redaction-gate's
# credential scanner. Both should run before any push to a public repo.

set -u
set -o pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <file-to-check>" >&2
  exit 2
fi

TARGET="$1"

if [ ! -f "$TARGET" ]; then
  echo "ERROR: $TARGET does not exist or is not a regular file" >&2
  exit 2
fi

# Customize this list for your environment. Each entry is one extended
# regex; case-insensitive matching is applied via grep -iE.
LEAK_PATTERNS=(
  # Personal identifiers
  '$USER'
  'jeffrey'

  # GitHub orgs / repos that imply private infra
  'jleechanorg'
  'hermes-agent'

  # Internal tool / CLI names
  'agento'
  '\bao spawn\b'
  'vpython'
  'mcp_mail'
  '\bclaudem\b'
  '\bclaudeg\b'
  '\bclaudek\b'

  # Slack / Discord channel / user IDs (10-char alnum starting with C/U)
  '[CU][0-9A-Z]{8,}'

  # launchd / beads / jsonl infrastructure
  'launchd'
  'beads'
  '\.jsonl'

  # Path leaks to user-scope config dirs
  '~/\.claude/'
  '~/\.hermes/'
  '~/\.codex/'
  '~/\.ao/'
  '~/projects/'
  '~/repos/'

  # Memory / feedback file references
  'feedback_[0-9]{4}-[0-9]{2}-[0-9]{2}'
  'MEMORY\.md'
)

PLACEHOLDER_PATTERN='<[A-Z_0-9]+>'

TOTAL_FAILURES=0
TOTAL_PLACEHOLDERS=0

echo "==> Verifying $TARGET for personal-reference leaks"
echo

for pattern in "${LEAK_PATTERNS[@]}"; do
  matches=$(grep -niE "$pattern" "$TARGET" 2>/dev/null || true)
  if [ -n "$matches" ]; then
    count=$(echo "$matches" | wc -l | tr -d ' ')
    echo "  FAIL  /$pattern/  ($count match(es))"
    echo "$matches" | sed 's/^/         /'
    echo
    TOTAL_FAILURES=$((TOTAL_FAILURES + count))
  fi
done

placeholder_count=$(grep -cE "$PLACEHOLDER_PATTERN" "$TARGET" 2>/dev/null || echo 0)
TOTAL_PLACEHOLDERS=$placeholder_count

echo "==> Placeholder count: $TOTAL_PLACEHOLDERS"
echo

if [ "$TOTAL_FAILURES" -eq 0 ]; then
  echo "✅ PASS: $TARGET has zero personal-reference leaks."
  echo "   $TOTAL_PLACEHOLDERS placeholder(s) found (expected for structure+placeholder flavor)."
  exit 0
else
  echo "❌ FAIL: $TARGET has $TOTAL_FAILURES personal-reference leak(s) across ${#LEAK_PATTERNS[@]} patterns."
  echo "   Fix the file before pushing to a public repo."
  exit 1
fi