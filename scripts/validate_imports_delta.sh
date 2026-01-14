#!/bin/bash

# validate_imports_delta.sh - Helper function for delta import validation
# Extracts import validation logic from .github/workflows/test.yml
# Usage: ./scripts/validate_imports_delta.sh
# Called from CI workflow for PR delta validation

set -e

echo "🔍 Running DELTA IMPORT validation checks..."
echo "Checking only files changed in this PR for inline imports and try/except patterns..."

# Debug git state
echo "Current branch: $(git branch --show-current)"
echo "Current commit: $(git rev-parse HEAD)"

# Skip validation for bulk linting PRs (allow legitimate conditional imports)
CURRENT_BRANCH=$(git branch --show-current)

# In CI, branch name might be in environment variables
if [[ -z "$CURRENT_BRANCH" ]]; then
  CURRENT_BRANCH="${GITHUB_HEAD_REF:-${GITHUB_REF_NAME:-}}"
fi

echo "Detected branch: $CURRENT_BRANCH"

if [[ "$CURRENT_BRANCH" == "bulk-lint-fixes" ]] || [[ "$CURRENT_BRANCH" == *"lint"* ]] || [[ "$CURRENT_BRANCH" == *"ruff"* ]]; then
  echo "✅ SKIP: Bulk linting PR - conditional imports are expected and allowed"
  echo "This PR is specifically for applying bulk linting fixes which may include"
  echo "legitimate conditional import patterns for optional dependencies."
  echo "Branch: $CURRENT_BRANCH"
  exit 0
fi

# Ensure base branch is fetched with full history (needed for merge-base)
git fetch --no-tags --prune origin +refs/heads/main:refs/remotes/origin/main 2>/dev/null || true
echo "Available refs: $(git branch -a | grep main)"

# Use merge-base diff for all scenarios (more reliable)
DIFF_SPEC="origin/main...HEAD"
echo "Using merge-base diff spec: $DIFF_SPEC"

# Run validation and capture output for CI artifacts
python3 scripts/validate_imports.py --diff-only "$DIFF_SPEC" 2>&1 | tee scripts/validate_imports.log
VALIDATION_STATUS=${PIPESTATUS[0]}

if [ $VALIDATION_STATUS -eq 0 ]; then
  echo "✅ Delta import validation: All checks passed"
  exit 0
else
  echo "❌ Delta import validation: Found violations in changed files"
  echo ""
  echo "Import violations must be fixed before merging:"
  echo "  IMP001: No try/except around imports - imports should be at module level"
  echo "  IMP002: No inline imports - imports must be at top of file"
  echo ""
  echo "Only files changed in this PR need to be fixed (delta validation)."
  echo "Please move all imports to the top of their respective files."
  exit $VALIDATION_STATUS
fi
