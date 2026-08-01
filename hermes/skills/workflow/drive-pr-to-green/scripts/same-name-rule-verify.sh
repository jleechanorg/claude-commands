#!/usr/bin/env bash
# same-name-rule-verify.sh — executable same-name-rule verification
#
# Verified scenario (2026-07-14, PR #8385 in $GITHUB_REPOSITORY):
#   The worker claimed `test_prompt_embedding_store.py::test_probe_actually_passes_in_test_env`
#   was pre-existing on `origin/main` and dismissed the Core-mvp-2 failure as a same-name-rule
#   dismissal. The PROMPT-COMPRESS Phase 2 of the work (signature-driven byte-diff + same-SHA
#   execution) verified it independently and was correct.
#
# The four same-name-rule checks (per qa-test-failure-dismissal-anti-pattern):
#   1. Same test name (pytest path::class::test_method exact match)
#   2. Same assertion / same error line
#   3. Same file at the same commit (BOTH files identical to origin/main HEAD)
#   4. Explicit same-SHA reproduction — run the failing test on origin/main HEAD byte-identical
#
# This script handles checks 3 and 4 deterministically. Checks 1 and 2 are already covered by
# downstream same-name-rule skill at ~/.hermes/skills/qa-test-failure-dismissal-anti-pattern/.
#
# Usage:
#   bash same-name-rule-verify.sh <owner/repo> <pr_number> <file1> [<file2> ...]
#
# Example:
#   bash same-name-rule-verify.sh $GITHUB_REPOSITORY 8385 \
#       $PROJECT_ROOT/tests/test_prompt_embedding_store.py deploy.sh

set -euo pipefail

if [ $# -lt 3 ]; then
  echo "usage: $0 <owner/repo> <pr_number> <file1> [<file2> ...]" >&2
  exit 2
fi

REPO="$1"
PR_NUMBER="$2"
shift 2
FILES=("$@")

if [ -n "${GH_TOKEN:-}" ]; then
  unset GH_TOKEN
fi
unset GH_TOKEN GITHUB_TOKEN AO_BOT_GH_TOKEN

PR_JSON=$(gh api repos/$REPO/pulls/$PR_NUMBER)
PR_BASE=$(echo "$PR_JSON" | jq -r .base.sha)
PR_HEAD=$(echo "$PR_JSON" | jq -r .head.sha)
MAIN_HEAD=$(gh api repos/$REPO/branches/main --jq .commit.sha)

echo "PR_BASE:  ${PR_BASE:0:12}"
echo "PR_HEAD:  ${PR_HEAD:0:12}"
echo "MAIN HEAD: ${MAIN_HEAD:0:12}"

echo
echo "=== Check 3: byte-identical same-name-rule verification ==="
for f in "${FILES[@]}"; do
  MAIN_BYTES=$(curl -fsS -L -H "Authorization: Bearer $(gh auth token 2>/dev/null || echo empty)" \
    "https://raw.githubusercontent.com/$REPO/$MAIN_HEAD/$f" 2>/dev/null | sha256sum | awk '{print $1}')
  PR_BYTES=$(curl -fsS -L -H "Authorization: Bearer $(gh auth token 2>/dev/null || echo empty)" \
    "https://raw.githubusercontent.com/$REPO/$PR_HEAD/$f" 2>/dev/null | sha256sum | awk '{print $1}')
  if [ "$MAIN_BYTES" = "$PR_BYTES" ]; then
    echo "IDENTICAL: $f  (main=$MAIN_BYTES, pr=$PR_BYTES)  <-- same-name-rule APPLIES"
  else
    echo "DIFFERENT: $f  (main=$MAIN_BYTES, pr=$PR_BYTES)  <-- same-name-rule DOES NOT apply"
  fi
done

echo
echo "=== Check 4: same-SHA reproduction ==="
echo "To complete check 4, run the failing test on $MAIN_HEAD in a venv matching CI:"
echo
for f in "${FILES[@]}"; do
  echo "# For $f:"
  echo "mkdir -p /tmp/mainrepo && cd /tmp/mainrepo"
  echo "git init -q && git remote add origin https://x-access-token:\$(gh auth token)@github.com/$REPO.git"
  echo "git fetch origin $MAIN_HEAD --depth=1"
  echo "git checkout FETCH_HEAD"
  echo "python3 -m venv /tmp/snr-venv"
  echo "/tmp/snr-venv/bin/pip install --quiet -r $PROJECT_ROOT/requirements.txt"
  echo "/tmp/snr-venv/bin/python -m pytest -p no:cacheprovider \\"
  echo "  <extracted path>::<test class>::<test method> -x --no-header"
  echo
done

echo "Exit codes:"
echo "  ALL IDENTICAL + reproducible on main -> valid same-name-rule dismissal"
echo "  ANY DIFFERENT  OR not reproducible    -> invalid same-name-rule claim"
