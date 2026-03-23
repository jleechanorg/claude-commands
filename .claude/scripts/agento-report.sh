#!/bin/bash
# agento-report.sh — summarize AO status and post to Slack #ai-slack-test
set -uo pipefail

SLACK_CHANNEL="${SLACK_TEST_CHANNEL:-C0AKALZ4CKW}"
LOG="/tmp/agento-report.log"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

# ── 1. Get active sessions with PRs ────────────────────────────────────────
AO_OUT=$(ao status 2>/dev/null)

# Extract sessions that have a real PR number (not "-")
ACTIVE_PRS=$(echo "$AO_OUT" | awk '
/^  [a-z]+-[0-9]+/ {
  session=$1; branch=$2; pr=$3; ci=$4; rev=$5; activity=$7; age=$8
  if (pr != "-" && pr != "") {
    print session " " pr " " ci " " rev " " activity " " age
  }
}')

# Count totals
TOTAL_SESSIONS=$(echo "$AO_OUT" | grep -c "exited\|active\|running" 2>/dev/null || echo "?")
ACTIVE_COUNT=$(echo "$AO_OUT" | grep -v "exited" | grep -cE "^  [a-z]+-[0-9]+" 2>/dev/null || echo "0")
EXITED_COUNT=$(echo "$AO_OUT" | grep -c "exited" 2>/dev/null || echo "?")
PR_COUNT=$(echo "$ACTIVE_PRS" | grep -c "." 2>/dev/null || echo "0")

# ── 2. Check green status for PRs with known numbers ───────────────────────
GREEN_PRS=()
NOT_GREEN_PRS=()

# Get open PRs from jleechanclaw
JC_PRS=$(gh api "repos/jleechanorg/jleechanclaw/pulls?state=open&per_page=20" 2>/dev/null \
    | jq -r '.[] | "\(.number) \(.head.ref) \(.mergeable // "null") \(.mergeable_state // "null")"' 2>/dev/null || echo "")

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    num=$(echo "$line" | awk '{print $1}')
    branch=$(echo "$line" | awk '{print $2}')
    mergeable=$(echo "$line" | awk '{print $3}')
    merge_state=$(echo "$line" | awk '{print $4}')

    # Quick green check (simplified — no Bugbot/evidence here for speed)
    REVIEWS=$(gh api "repos/jleechanorg/jleechanclaw/pulls/$num/reviews" 2>/dev/null || echo "[]")
    cr_approved=$(echo "$REVIEWS" | jq -r '[.[] | select(.user.login == "coderabbitai[bot]" and .state == "APPROVED")] | length' 2>/dev/null || echo "0")

    if [[ "$mergeable" == "true" && "$merge_state" != "dirty" && "$merge_state" != "unstable" && "$cr_approved" -ge 1 ]]; then
        GREEN_PRS+=("#$num $branch")
    else
        NOT_GREEN_PRS+=("#$num $branch [mergeable=$mergeable state=$merge_state cr=$cr_approved]")
    fi
done <<< "$JC_PRS"

GREEN_COUNT=${#GREEN_PRS[@]}
NOT_GREEN_COUNT=${#NOT_GREEN_PRS[@]}

# ── 3. Format Slack message ─────────────────────────────────────────────────
GREEN_LIST=""
for pr in "${GREEN_PRS[@]+"${GREEN_PRS[@]}"}"; do
    GREEN_LIST+="  ✅ $pr\n"
done
[[ -z "$GREEN_LIST" ]] && GREEN_LIST="  (none)\n"

NOT_GREEN_LIST=""
for pr in "${NOT_GREEN_PRS[@]+"${NOT_GREEN_PRS[@]}"}"; do
    NOT_GREEN_LIST+="  ⚠️ $pr\n"
done
[[ -z "$NOT_GREEN_LIST" ]] && NOT_GREEN_LIST="  (none)\n"

# Last poller run
LAST_POLL=$(tail -3 /tmp/ao-pr-poller.log 2>/dev/null | head -1 || echo "no log")

MSG="*Agento Status Report* — $(date '+%Y-%m-%d %H:%M PST')

*AO Sessions:* ${ACTIVE_COUNT} active / ${EXITED_COUNT} exited

*jleechanclaw PRs — Green (${GREEN_COUNT}):*
$(printf "$GREEN_LIST")
*jleechanclaw PRs — Not Green (${NOT_GREEN_COUNT}):*
$(printf "$NOT_GREEN_LIST")
*Last poller run:* \`${LAST_POLL}\`"

log "Posting report to Slack $SLACK_CHANNEL"
log "Green: $GREEN_COUNT  Not-green: $NOT_GREEN_COUNT"

# ── 4. Post to Slack via MCP is not available here; use bot token ───────────
source ~/.openclaw/set-slack-env.sh 2>/dev/null || true
BOT_TOKEN="${OPENCLAW_SLACK_BOT_TOKEN:-}"

if [[ -n "$BOT_TOKEN" ]]; then
    RESULT=$(curl -s -X POST "https://slack.com/api/chat.postMessage" \
        -H "Authorization: Bearer $BOT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"channel\": \"$SLACK_CHANNEL\", \"text\": $(echo "$MSG" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}")
    OK=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("ok","false"))' 2>/dev/null)
    if [[ "$OK" == "True" ]]; then
        log "✓ Posted to Slack"
    else
        log "✗ Slack post failed: $RESULT"
    fi
else
    log "No OPENCLAW_SLACK_BOT_TOKEN — printing report only"
fi

# Always echo the report
echo ""
echo "=== AGENTO REPORT ==="
printf "$MSG\n"
