#!/usr/bin/env bash
# dispatch-real-smoke.sh — Dispatch a REAL-mode MCP Smoke Tests run for a PR.
#
# Verified working recipe (PR #8467, 2026-07-20). Use this when:
#   - GATE-8 (Smoke Gate Wait) fails with "timed out waiting for a REAL-mode
#     mcp-smoke-tests pass for SHA <sha> — the default smoke runs in MOCK mode
#     and does not satisfy the gate".
#   - The PR has passed all other Green Gate conditions (CI green, no
#     conflicts, comments resolved, evidence link present).
#
# Why this exists:
#   - `/smoke` PR comments route through comment-router.yml which dispatches
#     via `gh workflow run ... -f inputs[pr_number]=N` but does NOT pass
#     `test_mode=real`. The workflow's `test_mode` input defaults to `mock`.
#     So `/smoke real` STILL lands in mock mode.
#   - `gh workflow run mcp-smoke-tests.yml ...` fails with
#     "fatal: not a git repository" because the workflow's `ubuntu-latest`
#     runner has no checkout step.
#   - Only the REST API dispatch (POST .../dispatches) works because it
#     doesn't require .git context AND accepts all inputs.
#
# Usage:
#   ./dispatch-real-smoke.sh <PR_NUMBER> [<REPO_OWNER/REPO>]
#
# Defaults: REPO_OWNER/REPO = $GITHUB_REPOSITORY
#
# After the script reports "queued", wait ~3-6 min for the run to complete,
# then re-run the failed Green Gate:
#   gh run rerun <green-gate-run-id> --repo $GITHUB_REPOSITORY --failed

set -euo pipefail

PR_NUMBER="${1:-}"
REPO="${2:-$GITHUB_REPOSITORY}"

if [[ -z "$PR_NUMBER" ]]; then
  echo "Usage: $0 <PR_NUMBER> [<REPO_OWNER/REPO>]" >&2
  echo "Example: $0 8467" >&2
  exit 64
fi

TOKEN="$(gh auth status --show-token | awk '/Token:/{print $2}')"
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: could not extract gh auth token (run 'gh auth login' first)" >&2
  exit 77
fi

# Validate PR exists
PR_JSON="$(gh api "repos/${REPO}/pulls/${PR_NUMBER}" --jq '{state: .state, head_sha: .head.sha, head_ref: .head.ref}')"
echo "PR #${PR_NUMBER} on ${REPO}:"
echo "${PR_JSON}" | sed 's/^/  /'

# Dispatch via REST API (NOT gh workflow run — see header comment)
PAYLOAD="$(jq -nc --arg pr "$PR_NUMBER" \
  '{ref: "main", inputs: {pr_number: $pr, test_mode: "real"}}')"

HTTP_CODE="$(curl -sS -o /tmp/smoke-dispatch-response.json -w '%{http_code}' \
  -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "https://api.github.com/repos/${REPO}/actions/workflows/mcp-smoke-tests.yml/dispatches")"

if [[ "$HTTP_CODE" == "204" ]]; then
  echo "✅ MCP Smoke Tests dispatched in REAL mode (HTTP 204)."
  echo "   Monitor: gh api \"repos/${REPO}/actions/runs?per_page=5\" | jq '.workflow_runs[] | select(.name == \"MCP Smoke Tests\") | {status, conclusion, updated_at}'"
  echo "   When status=completed and conclusion=success:"
  echo "     gh run rerun <green-gate-run-id> --repo ${REPO} --failed"
  exit 0
else
  echo "❌ Dispatch failed (HTTP ${HTTP_CODE}):" >&2
  cat /tmp/smoke-dispatch-response.json >&2
  exit 1
fi
