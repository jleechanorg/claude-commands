#!/bin/bash

# Usage: ./cherrypick_pr.sh <PR_NUMBER> [remote]
# A robust script to cherry-pick all commits from a GitHub pull request.
set -e

PR_NUM="$1"
REMOTE="${2:-origin}"
PR_BRANCH="pr-$PR_NUM"

if [ -z "$PR_NUM" ]; then
  echo "Usage: $0 <PR_NUMBER> [remote]"
  exit 1
fi

# Fetch the pull request commits into a temporary local branch
echo "Fetching commits from PR #$PR_NUM..."
git fetch $REMOTE pull/$PR_NUM/head:$PR_BRANCH

# Get the list of commit hashes from the PR branch in chronological order
# We compare the PR branch to the commit where it diverged from the current branch
MERGE_BASE=$(git merge-base HEAD $PR_BRANCH)
COMMITS=( $(git rev-list --reverse $MERGE_BASE..$PR_BRANCH) )
NUM_COMMITS=${#COMMITS[@]}

if [ $NUM_COMMITS -eq 0 ]; then
  echo "No new commits found in PR #$PR_NUM to cherry-pick."
else
  echo "Found $NUM_COMMITS commit(s) to cherry-pick from PR #$PR_NUM."

  # Loop through and cherry-pick each commit individually
  for COMMIT in "${COMMITS[@]}"; do
    echo "Cherry-picking commit: ${COMMIT:0:12}..."
    git cherry-pick $COMMIT
  done
fi

# Clean up the temporary branch
echo "Cleaning up temporary branch $PR_BRANCH..."
git branch -D $PR_BRANCH

echo "Done! All commits from PR #$PR_NUM have been successfully cherry-picked."
