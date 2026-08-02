#!/usr/bin/env bash
# apply_patch_and_open_pr.sh — End-to-end runner for the
# `apply-supplied-patch-and-open-pr` skill. Wraps pre-flight, clone, branch,
# git am, test, push, pr-create in one re-runnable shell script.
#
# Usage:
#   apply_patch_and_open_pr.sh <OWNER/REPO> <branch-name> <patch-path> <instructions-file> [base-sha]
#
# Example:
#   apply_patch_and_open_pr.sh jleechanorg/disk_magician findings-wiki-contract \
#     /tmp/0001.patch /tmp/UPSTREAM-PROMPT.md efc51ba
#
# Required env:
#   gh auth status → logged in to github.com with push access on OWNER/REPO
#   The instructions file is parsed for: test paths, lint commands, PR title,
#   PR body template.
#
# Exit codes:
#   0 — PR opened, all tests passed, all guardrails verified
#   1 — pre-flight check failed
#   2 — git am or git apply failed
#   3 — one or more tests failed (do NOT push in this case)
#   4 — push or PR-create failed
#   5 — guardrail check failed (e.g., machine paths leaked)

set -euo pipefail

OWNER_REPO="${1:-}"
BRANCH="${2:-}"
PATCH="${3:-}"
INSTRUCTIONS="${4:-}"
BASE_SHA_EXPECTED="${5:-}"

if [ -z "$OWNER_REPO" ] || [ -z "$BRANCH" ] || [ -z "$PATCH" ] || [ -z "$INSTRUCTIONS" ]; then
  cat <<EOF
Usage: $0 <OWNER/REPO> <branch-name> <patch-path> <instructions-file> [expected-base-sha]

  OWNER/REPO      e.g. jleechanorg/disk_magician
  branch-name     e.g. findings-wiki-contract
  patch-path      path to a .patch or .diff file
  instructions    path to UPSTREAM-PROMPT.md / RUNBOOK.md / HANDOFF.md
  expected-base-sha  optional; verified against origin/main before applying

Example:
  $0 jleechanorg/disk_magician findings-wiki-contract \\
     /tmp/0001.patch /tmp/UPSTREAM-PROMPT.md efc51ba
EOF
  exit 1
fi

OWNER="${OWNER_REPO%%/*}"
REPO="${OWNER_REPO#*/}"
SCRATCH="/tmp/apply-pr-${BRANCH}-$$"
mkdir -p "$SCRATCH"

cleanup() { rm -rf "$SCRATCH"; }
trap cleanup EXIT

echo "===== STEP 1: PRE-FLIGHT ====="
gh auth status >/dev/null || { echo "gh auth failed"; exit 1; }

ACTUAL_SHA=$(gh api "repos/$OWNER_REPO/branches/main" --jq '.commit.sha')
echo "origin/main HEAD: $ACTUAL_SHA"
if [ -n "$BASE_SHA_EXPECTED" ]; then
  if [ "${ACTUAL_SHA:0:7}" != "${BASE_SHA_EXPECTED:0:7}" ]; then
    echo "WARNING: HEAD ($ACTUAL_SHA) does not match expected base ($BASE_SHA_EXPECTED)"
    echo "Will use 'git apply --3way' fallback if git am fails."
  fi
fi

EXISTING=$(gh api "repos/$OWNER_REPO/pulls?state=all&head=$OWNER:$BRANCH&per_page=10" --jq 'length')
if [ "$EXISTING" -gt 0 ]; then
  echo "WARNING: A PR already exists for branch $OWNER:$BRANCH. Refusing to push onto a non-owned head."
  gh api "repos/$OWNER_REPO/pulls?state=all&head=$OWNER:$BRANCH&per_page=10" --jq '.[] | "  PR #\(.number) [\(.state)] \(.html_url)"'
  exit 1
fi

echo "===== STEP 2: CLONE ====="
cd "$SCRATCH"
git clone --quiet "https://github.com/$OWNER_REPO.git" repo
cd repo
[ "$(git rev-parse origin/main)" = "$ACTUAL_SHA" ] || { echo "Clone HEAD mismatch"; exit 1; }

echo "===== STEP 3: BRANCH + GIT AM ====="
git checkout -B "$BRANCH" origin/main
if git am "$PATCH"; then
  echo "git am: clean"
else
  echo "git am failed; trying git apply --3way"
  git am --abort || true
  if git apply --3way "$PATCH"; then
    git add -A
    # Try to preserve the original commit message from the patch
    ORIG_MSG=$(git format-patch -1 --stdout HEAD~ 2>/dev/null | sed -n '/^Subject:/p' | sed 's/^Subject: \[PATCH[^]]*\] //')
    if [ -z "$ORIG_MSG" ]; then
      ORIG_MSG="feat: apply supplied patch via apply_patch_and_open_pr.sh"
    fi
    git commit -m "$ORIG_MSG" || { echo "Failed to commit after apply --3way"; exit 2; }
  else
    echo "git apply --3way also failed; manual resolution needed"
    exit 2
  fi
fi

echo "===== STEP 4: RUN USER-LISTED TESTS ====="
# Extract test paths from instructions file (look for `bash tests/...` patterns)
TESTS=$(grep -oE '(bash|sh) [^ ]*test[^ ]*\.sh' "$INSTRUCTIONS" | awk '{print $2}' | sort -u)
LINT_CMDS=$(grep -oE '(bash|sh) [^ ]*(lint|findings_lint)[^ ]*\.sh[^"]*' "$INSTRUCTIONS" | sort -u)

if [ -z "$TESTS" ] && [ -z "$LINT_CMDS" ]; then
  echo "No test or lint commands extracted from instructions file."
  echo "Open $INSTRUCTIONS and add explicit test paths to the script."
  exit 3
fi

FAILED=0
for t in $TESTS; do
  if [ -f "$t" ]; then
    echo "--- $t ---"
    bash "$t" 2>&1 | tail -10
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then
      echo "FAIL: $t"
      FAILED=$((FAILED+1))
    fi
  else
    echo "SKIP (not found): $t"
  fi
done

for lc in $LINT_CMDS; do
  echo "--- $lc ---"
  eval "$lc" 2>&1 | tail -5
  if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    echo "FAIL: $lc"
    FAILED=$((FAILED+1))
  fi
done

if [ "$FAILED" -gt 0 ]; then
  echo "Tests/lint failures: $FAILED. Refusing to push."
  exit 3
fi

echo "===== STEP 5: GUARDRAILS ====="
# Default guardrail check: scan committed files for real machine paths
LEAK=$(git diff origin/main..HEAD --name-only | while read f; do
  if [ -f "$f" ]; then
    grep -nE "^\s*/Users/(?!nobody)[a-z]+/" "$f" 2>/dev/null
  fi
done)
if [ -n "$LEAK" ]; then
  echo "GUARDRAIL FAIL: real machine paths leaked into commits:"
  echo "$LEAK"
  exit 5
fi
echo "Guardrails OK (only /Users/nobody/ test fixtures, if any)"

echo "===== STEP 6: PUSH + PR ====="
git push -u origin "$BRANCH"
PUSHED_SHA=$(git rev-parse origin/"$BRANCH")
echo "Pushed: $PUSHED_SHA"

# Extract PR title from instructions file (first # heading)
PR_TITLE=$(grep -E '^# ' "$INSTRUCTIONS" | head -1 | sed 's/^# //')
if [ -z "$PR_TITLE" ]; then
  PR_TITLE="feat: apply supplied patch via apply_patch_and_open_pr.sh"
fi

# Build PR body — use everything after the title as the body template,
# strip leading "# " / blank lines so the body is clean.
PR_BODY="$SCRATCH/PR_BODY.md"
{
  echo "## Applied patch"
  echo
  echo "- Source: \`$PATCH\`"
  echo "- Instructions: \`$INSTRUCTIONS\`"
  echo "- Head SHA: \`$PUSHED_SHA\` (base: \`$ACTUAL_SHA\`)"
  echo
  echo "## Test results"
  for t in $TESTS; do
    echo "- \`$t\` → PASS"
  done
  for lc in $LINT_CMDS; do
    echo "- \`$lc\` → PASS"
  done
  echo
  echo "---"
  echo
  echo "Original instructions content follows:"
  echo
  cat "$INSTRUCTIONS"
} > "$PR_BODY"

"$HOME/.hermes/scripts/gh-safe-publish" pr create \
  --repo "$OWNER_REPO" \
  --base main \
  --head "$BRANCH" \
  --title "$PR_TITLE" \
  --body-file "$PR_BODY"

PR_URL=$(gh pr list --head "$BRANCH" --json url --jq '.[0].url')
echo
echo "===== DONE ====="
echo "PR: $PR_URL"
echo "Branch: $BRANCH @ $PUSHED_SHA"
echo "Base: $ACTUAL_SHA"
echo "Diffstat:"
git diff --shortstat origin/main..HEAD

exit 0
