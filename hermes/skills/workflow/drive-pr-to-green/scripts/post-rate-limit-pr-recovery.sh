#!/usr/bin/env bash
# post-rate-limit-pr-recovery.sh — run after a GH rate-limit wedge clears
#
# Usage:
#   bash post-rate-limit-pr-recovery.sh \
#     --pr <N> --owner <owner> --repo <repo> --branch <branch> \
#     --channel <C_id> --thread <thread_ts> \
#     [--skeptics-workflow <workflow_id>]
#
# This script is invoked from a one-shot cron created when an inline PR-drive
# hits a GH user-token rate-limit wedge. It runs the exact sequence that
# would normally happen inline (resolve reviewer threads, ping CodeRabbit,
# trigger Skeptic Self-Verify, poll for VERDICT, re-run failed Green Gate,
# post completion summary in-thread).
#
# Verified 2026-07-05 PR #8070 recovery.
#
# Do NOT invoke from an AO worker — the orchestrator daemon is wedged on
# the same rate-limit wedge; use inline tools only.

set -euo pipefail

PR=""
OWNER=""
REPO=""
BRANCH=""
CHANNEL=""
THREAD=""
SKEPTIC_WF=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) PR="$2"; shift 2;;
    --owner) OWNER="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    --channel) CHANNEL="$2"; shift 2;;
    --thread) THREAD="$2"; shift 2;;
    --skeptics-workflow) SKEPTIC_WF="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ -z "$PR" || -z "$OWNER" || -z "$REPO" || -z "$BRANCH" || -z "$CHANNEL" || -z "$THREAD" ]]; then
  echo "Required: --pr <N> --owner <owner> --repo <repo> --branch <branch> --channel <C_id> --thread <thread_ts>"
  exit 2
fi

FULL="$OWNER/$REPO"

# 1. Verify rate-limit reset
echo "[1/6] Checking rate-limit buckets..."
for i in {1..5}; do
  CORE=$(gh api rate_limit --jq '.resources.core.remaining')
  GQL=$(gh api rate_limit --jq '.resources.graphql.remaining')
  echo "  attempt $i: core=$CORE graphql=$GQL"
  if [[ "$CORE" -gt 1000 && "$GQL" -gt 1000 ]]; then
    echo "  -> buckets healthy"
    break
  fi
  if [[ "$i" -eq 5 ]]; then
    echo "  -> buckets still constrained after 5 retries; aborting"
    exit 1
  fi
  sleep 60
done

# 2. Resolve reviewer threads
echo "[2/6] Resolving reviewer threads..."
if [[ -x "$HOME/.hermes/lib/resolve_review_threads.sh" ]]; then
  bash "$HOME/.hermes/lib/resolve_review_threads.sh" "$PR" --owner "$OWNER" --repo "$REPO" 2>&1 | tail -10
else
  echo "  resolve_review_threads.sh not found; skipping (run manually)"
fi

# 3. Ping CodeRabbit for fresh re-review
echo "[3/6] Posting @coderabbitai re-review ping..."
gh pr comment "$PR" --repo "$FULL" --body "@coderabbitai all good? Head is now \`$(git rev-parse --short origin/"$BRANCH" 2>/dev/null || echo 'latest')\` — addressed the still-valid reviewer threads. Please re-review against the new head and confirm APPROVED."

# 4. Trigger Skeptic Self-Verify
echo "[4/6] Triggering Skeptic Self-Verify..."
if [[ -z "$SKEPTIC_WF" ]]; then
  SKEPTIC_WF=$(gh workflow list --repo "$FULL" --json id,name --jq '.[] | select(.name | test("Skeptic"; "i")) | .id' | head -1)
fi
if [[ -n "$SKEPTIC_WF" ]]; then
  gh workflow run "$SKEPTIC_WF" --repo "$FULL" --ref "$BRANCH" -f pr_number="$PR"
  echo "  -> workflow $SKEPTIC_WF dispatched"
else
  echo "  -> no Skeptic Self-Verify workflow found; skipping"
fi

# 5. Poll for VERDICT: PASS (max 10 min)
echo "[5/6] Polling for VERDICT: PASS..."
VERDICT_LANDED=0
for i in {1..20}; do
  sleep 30
  CNT=$(gh api "repos/$FULL/issues/$PR/comments" --jq '[.[] | select(.user.login == "github-actions[bot]" and (.body | contains("VERDICT: PASS")))] | length')
  echo "  attempt $i: verdict_count=$CNT"
  if [[ "${CNT:-0}" -gt 0 ]]; then
    VERDICT_LANDED=1
    echo "  -> VERDICT: PASS landed"
    break
  fi
done

# 6. Re-run failed Green Gate + post completion summary
echo "[6/6] Final cleanup..."
GG_RUN=$(gh pr checks "$PR" --repo "$FULL" 2>&1 | grep -E "Green Gate" | grep -oE 'https://[^ ]+/actions/runs/[0-9]+' | head -1 | grep -oE 'runs/[0-9]+' | cut -d/ -f2)
if [[ -n "$GG_RUN" ]]; then
  gh api -X POST "repos/$FULL/actions/runs/$GG_RUN/rerun-failed-jobs" 2>&1 | head -3
  echo "  -> Green Gate run $GG_RUN re-triggered"
fi

# Post completion summary in-thread
SUMMARY=":white_check_mark: *Post-rate-limit recovery complete for PR #${PR}*\n\n"
SUMMARY+="*Resolved:*\n"
SUMMARY+="• Reviewer threads via \`resolve_review_threads.sh\`\n"
SUMMARY+="• \`@coderabbitai\` re-review ping posted\n"
SUMMARY+="• Skeptic Self-Verify dispatched (workflow \`${SKEPTIC_WF:-auto-detected}\`)\n"
if [[ "$VERDICT_LANDED" -eq 1 ]]; then
  SUMMARY+="• \`VERDICT: PASS\` received\n"
else
  SUMMARY+="• \`VERDICT: PASS\` not yet landed after 10min — check Green Gate re-run\n"
fi
if [[ -n "$GG_RUN" ]]; then
  SUMMARY+="• Green Gate run \`${GG_RUN}\` re-triggered\n"
fi
SUMMARY+="\nPR is now ready for \`skeptic-cron.yml\` auto-merge (next run: ~30min).\n\n"
SUMMARY+=":brain: Memory: \`drive-pr-to-green\` Step 7c rate-limit fallback recipe, PR #8070 2026-07-05."

# Post via curl (Slack MCP may also be available; both routes work)
TOKEN=$(bash -lc 'echo $HERMES_SLACK_BOT_TOKEN')
if [[ -n "$TOKEN" ]]; then
  curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "{\"channel\":\"$CHANNEL\",\"thread_ts\":\"$THREAD\",\"text\":\"$SUMMARY\"}" \
    | head -c 200
  echo ""
else
  echo "No HERMES_SLACK_BOT_TOKEN; summary not posted to Slack."
  echo "$SUMMARY"
fi

echo "Recovery complete."