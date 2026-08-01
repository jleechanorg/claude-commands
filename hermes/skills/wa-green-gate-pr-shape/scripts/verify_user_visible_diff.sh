#!/usr/bin/env bash
# verify_user_visible_diff.sh — Detect the "backend-only field-add with no frontend
# consumer" PR-shape class (your-project.com specific).
#
# Symptom: PR title/issue promises a UX change ("surface quota counters",
# "[frontend] ..."). Diff is all backend (no $PROJECT_ROOT/frontend_v1/ files). User
# loading the deployed preview before vs after the PR sees identical pixels.
#
# Verified 2026-07-15 against PR #7953. The PR body said "the frontend can
# render a soft-warn countdown banner" — but no JS in the deployed bundle
# actually read the new fields on the success path.
#
# Usage:
#   ./verify_user_visible_diff.sh <PR_NUMBER>
#
# Exit codes:
#   0 = backend-only diff, no frontend consumer for the new fields (RED FLAG)
#   1 = frontend files touched OR frontend bundle has hits outside error path (OK)
#   2 = usage / network error

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <PR_NUMBER>" >&2
  exit 2
fi

PR="$1"
REPO="$GITHUB_REPOSITORY"

echo "=== PR #${PR} — frontend-consumer check ==="

# 1. List files in the diff
echo
echo "--- Files in diff ---"
FILES=$(gh pr view "${PR}" --repo "${REPO}" --json files --jq '.files[].path')
echo "${FILES}"

FRONTEND_HITS=$(echo "${FILES}" | grep -c '^$PROJECT_ROOT/frontend_v1/' || true)
BACKEND_HITS=$(echo "${FILES}" | grep -c '^$PROJECT_ROOT/' || true)
echo
echo "Frontend files: ${FRONTEND_HITS} | Backend files: ${BACKEND_HITS}"

if [[ "${FRONTEND_HITS}" -gt 0 ]]; then
  echo
  echo "✅ Frontend files touched — skipping bundle grep (likely OK)."
  exit 1
fi

# 2. Pull the deployed PR preview URL from any "Deployment Complete" bot comment
echo
echo "--- Resolving PR preview URL from gh-actions bot comments ---"
PREVIEW=$(gh pr view "${PR}" --repo "${REPO}" --json comments --jq \
  '.comments[] | select(.body | test("Deployment Complete"; "i")) | .body' \
  | grep -oE 'mvp-site-app-[a-z0-9-]+' | sort -u | tail -1 || true)

if [[ -z "${PREVIEW}" ]]; then
  echo "❌ Could not resolve a preview URL from PR comments. Aborting." >&2
  exit 2
fi

PREVIEW_URL="https://${PREVIEW}-i6xf2p72ka-uc.a.run.app"
echo "Preview URL: ${PREVIEW_URL}"

# 3. Pull the main JS bundles
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
curl -fsSL "${PREVIEW_URL}/frontend_v1/app.js" -o "${TMP}/app.js" || { echo "❌ app.js fetch failed" >&2; exit 2; }
curl -fsSL "${PREVIEW_URL}/frontend_v1/api.js" -o "${TMP}/api.js" || { echo "❌ api.js fetch failed" >&2; exit 2; }

echo
echo "--- Bundle sizes ---"
wc -c "${TMP}/app.js" "${TMP}/api.js"

# 4. Grep for the new field names. We extract field names from the PR body
#    (look for new keys in code blocks) and the PR diff. For a generic check,
#    grep for the most common quota / rate-limit field names.
echo
echo "--- Field-name hits in deployed JS bundle ---"

# Field candidates: anything that looks like a snake_case key added by the PR.
# Pull from PR title + body for context.
PR_TITLE=$(gh pr view "${PR}" --repo "${REPO}" --json title --jq '.title')
PR_BODY=$(gh pr view "${PR}" --repo "${REPO}" --json body --jq '.body // ""')
COMBINED="${PR_TITLE} ${PR_BODY}"

# Heuristic field names: look for words containing "remaining", "reset_time",
# "quota", "limit" combined with snake_case underscore pattern.
CANDIDATES=$(echo "${COMBINED}" | grep -oE '\b[a-z]+_[a-z_]+\b' | grep -E 'remaining|reset|quota|limit|count' | sort -u | head -20 || true)

if [[ -z "${CANDIDATES}" ]]; then
  echo "No obvious field-name candidates in PR title/body. Falling back to defaults:"
  CANDIDATES="daily_remaining hourly_remaining reset_time_daily reset_time_hourly quota_remaining"
fi

echo "Candidates: ${CANDIDATES}"
echo

BUNDLE="${TMP}/app.js ${TMP}/api.js"
TOTAL=0
ERROR_PATH_ONLY=0
for f in ${CANDIDATES}; do
  HITS=$(grep -c "${f}" ${BUNDLE} || true)
  ERR_HITS=$(grep -B2 -A2 "${f}" ${BUNDLE} | grep -c 'jsonError\|error\.' || true)
  echo "  ${f}: ${HITS} total | ${ERR_HITS} in error-path context"
  TOTAL=$((TOTAL + HITS))
  # If all hits are inside jsonError/429 handling, this field has no success-path consumer
  if [[ "${HITS}" -gt 0 && "${ERR_HITS}" -eq "${HITS}" ]]; then
    ERROR_PATH_ONLY=$((ERROR_PATH_ONLY + 1))
  fi
done

echo
echo "=== Verdict ==="
echo "Total hits across candidates: ${TOTAL}"
echo "Fields used only in error path (no success-path consumer): ${ERROR_PATH_ONLY}"

if [[ "${ERROR_PATH_ONLY}" -gt 0 ]]; then
  echo
  echo "❌ RED FLAG — at least one PR-added field has NO success-path frontend consumer."
  echo "   User-visible diff: NONE on the success path. Field exists only in the"
  echo "   pre-existing 429 error-path handling."
  echo
  echo "Recommended action:"
  echo "  1. Split the PR into backend field-add + frontend consumer PRs, OR"
  echo "  2. Rewrite the PR body to be honest about backend-only scope, OR"
  echo "  3. Open a bead tracking the missing frontend work."
  exit 0
fi

echo "✅ No RED FLAG — fields are either absent (backend-only, no contract yet)"
echo "   OR have frontend consumers outside the error path."
exit 1