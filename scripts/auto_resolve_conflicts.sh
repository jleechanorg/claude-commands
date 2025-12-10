#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <pr-number>" >&2
  exit 1
fi

PR_NUMBER="$1"
REPO="${GITHUB_REPOSITORY:-$(git remote get-url origin 2>/dev/null || echo "") }"
if [ -z "$REPO" ]; then
  echo "❌ Unable to determine repository (set GITHUB_REPOSITORY or configure git remote 'origin')." >&2
  exit 1
fi

# Fetch PR metadata
if ! PR_JSON=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json headRefName,baseRefName --jq '{head:.headRefName,base:.baseRefName}'); then
  echo "❌ Failed to read PR #$PR_NUMBER metadata via gh." >&2
  exit 1
fi
HEAD_BRANCH=$(echo "$PR_JSON" | jq -r '.head')
BASE_BRANCH=$(echo "$PR_JSON" | jq -r '.base')

if [ -z "$HEAD_BRANCH" ] || [ -z "$BASE_BRANCH" ]; then
  echo "❌ Missing head/base branch information for PR #$PR_NUMBER." >&2
  exit 1
fi

echo "🔄 Resolving PR #$PR_NUMBER (head: $HEAD_BRANCH, base: $BASE_BRANCH)"

git fetch origin "$BASE_BRANCH" "$HEAD_BRANCH" "pull/$PR_NUMBER/head:pr-$PR_NUMBER" --prune

WORK_BRANCH="auto-resolve/pr-$PR_NUMBER"
BASE_REF="origin/$BASE_BRANCH"
HEAD_REF="pr-$PR_NUMBER"

git checkout -B "$WORK_BRANCH" "$BASE_REF"

if git merge --no-ff --no-edit "$HEAD_REF"; then
  echo "✅ Merge succeeded locally; pushing update"
  git push origin "$WORK_BRANCH" --force-with-lease
  echo "Auto-resolution complete"
  exit 0
fi

echo "⚠️ Merge conflicts detected; aborting merge"
git merge --abort || true
exit 1
