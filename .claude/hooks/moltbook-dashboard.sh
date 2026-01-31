#!/bin/bash
# Moltbook Auto-Posting Dashboard
# Shows current state of automated milestone posting

STATE_FILE="/tmp/moltbook_state_$(whoami).json"

if [ ! -f "$STATE_FILE" ]; then
  echo "📊 Moltbook Auto-Posting Dashboard"
  echo "===================================="
  echo ""
  echo "⚠️ No state file found yet."
  echo "State will be created on first milestone detection."
  exit 0
fi

echo "📊 Moltbook Auto-Posting Dashboard"
echo "===================================="
echo ""

# Last post info
LAST_POST_TIME=$(jq -r '.last_post_time' "$STATE_FILE")
if [ "$LAST_POST_TIME" != "0" ]; then
  LAST_POST_DATE=$(date -r "$LAST_POST_TIME" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "Unknown")
  echo "📤 Last Post: $LAST_POST_DATE"
else
  echo "📤 Last Post: Never"
fi

# Last post URL
LAST_URL=$(jq -r '.last_post_url // "N/A"' "$STATE_FILE")
echo "🔗 Last URL: $LAST_URL"

# Posts today
POSTS_TODAY=$(jq -r '.posts_today' "$STATE_FILE")
echo "📈 Posts Today: $POSTS_TODAY"

# Rate limit status
if [ "$LAST_POST_TIME" != "0" ]; then
  NOW=$(date +%s)
  ELAPSED=$((NOW - LAST_POST_TIME))
  TWO_HOURS=7200

  if [ $ELAPSED -lt $TWO_HOURS ]; then
    WAIT_TIME=$((TWO_HOURS - ELAPSED))
    WAIT_MINUTES=$((WAIT_TIME / 60))
    echo "⏱️ Rate Limit: Active ($WAIT_MINUTES minutes remaining)"
  else
    echo "✅ Rate Limit: Ready to post"
  fi
else
  echo "✅ Rate Limit: Ready to post"
fi

echo ""
echo "📋 Recent Milestones (last 10):"
echo "================================"

MILESTONE_COUNT=$(jq '.milestones_tracked | length' "$STATE_FILE")
if [ "$MILESTONE_COUNT" -eq 0 ]; then
  echo "  No milestones tracked yet."
else
  jq -r '.milestones_tracked[-10:] | reverse | .[] | "  [\(.timestamp | todate | split("T")[0] + " " + split("T")[1] | split(".")[0])] \(.type) - \(.details) (Posted: \(.posted // false | if . then "✅" else "❌" end))\(if .reason then " - \(.reason)" else "" end)\(if .error then " - Error: \(.error)" else "" end)\(if .url then "\n    🔗 \(.url)" else "" end)"' "$STATE_FILE"
fi

echo ""
echo "💡 Commands:"
echo "  View full state: cat $STATE_FILE | jq"
echo "  Clear state: rm $STATE_FILE"
echo "  Test hook: MOLTBOOK_DRY_RUN=true echo '{\"tool_input\":{\"command\":\"gh pr merge 4257\"}}' | ./.claude/hooks/moltbook-milestone.sh"
