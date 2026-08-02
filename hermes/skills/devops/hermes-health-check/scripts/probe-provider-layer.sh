#!/bin/bash
# probe-provider-layer.sh — 4-probe triage for "user reports nothing happening on Slack".
#
# This is the canonical first move when a Slack user (typically Jeffrey) reports
# the gateway isn't responding and the gateway log shows repeated
# `cannot_reply_to_message` errors. The errors are downstream noise; the cause
# is almost always upstream at the model provider layer.
#
# Usage:
#   ./probe-provider-layer.sh <channel_id> <user_msg_ts>
#
# Outputs:
#   - 4 sections summarizing each probe (launchd / Slack post / primary / fallback)
#   - Exit code 0 = all healthy, 1 = some failure (read output for which)
#   - Posts and immediately deletes one diagnostic message in the channel
#
# Pairs with: SKILL.md section "User reports 'nothing happening' on Slack —
# provider-layer triage (canonical recipe, 2026-07-14)"

set -uo pipefail

CHANNEL="${1:?usage: $0 <channel_id> <user_msg_ts>}"
USER_MSG_TS="${2:?usage: $0 <channel_id> <user_msg_ts>}"

PASS=0
FAIL=0

# Probe 1 — launchd state for prod gateway
echo "--- PROBE 1: launchd state for ai.hermes.prod ---"
LAUNCHD_OUT=$(launchctl print "gui/$(id -u)/ai.hermes.prod" 2>&1 | grep -E 'state =|pid =|last exit code' | head -3)
echo "$LAUNCHD_OUT"
if echo "$LAUNCHD_OUT" | grep -q 'state = running'; then
  echo "  RESULT: gateway is running (probe 1 OK)"
  PASS=$((PASS+1))
else
  echo "  RESULT: gateway is NOT running — restart required"
  FAIL=$((FAIL+1))
fi

# Probe 2 — Slack bot-token post + delete
echo ""
echo "--- PROBE 2: Slack bot-token probe in $CHANNEL ---"
BOT_TOKEN=$(grep '^export SLACK_BOT_TOKEN=' ~/.profile 2>/dev/null | head -1 | sed 's/export SLACK_BOT_TOKEN=//; s/"//g')
if [ -z "$BOT_TOKEN" ]; then
  echo "  RESULT: SLACK_BOT_TOKEN not found in ~/.profile"
  FAIL=$((FAIL+1))
else
  POST_RESP=$(curl -fsS -X POST https://slack.com/api/chat.postMessage \
    -H "Authorization: Bearer $BOT_TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "{\"channel\":\"$CHANNEL\",\"thread_ts\":\"$USER_MSG_TS\",\"mrkdwn\":false,\"text\":\"[diagnostic probe — will delete immediately]\"}" 2>&1)
  POST_TS=$(echo "$POST_RESP" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("ts",""))' 2>/dev/null || echo "")
  POST_OK=$(echo "$POST_RESP" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("ok","false"))' 2>/dev/null || echo "false")
  if [ "$POST_OK" = "True" ] && [ -n "$POST_TS" ]; then
    echo "  POST ok=true, ts=$POST_TS"
    DEL_RESP=$(curl -fsS -X POST https://slack.com/api/chat.delete \
      -H "Authorization: Bearer $BOT_TOKEN" \
      -d "channel=$CHANNEL&ts=$POST_TS" 2>&1)
    DEL_OK=$(echo "$DEL_RESP" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("ok","false"))' 2>/dev/null || echo "false")
    if [ "$DEL_OK" = "True" ]; then
      echo "  DELETE ok=true (probe message removed)"
      echo "  RESULT: bot CAN post in $CHANNEL (probe 2 OK — channel/token path is healthy)"
      PASS=$((PASS+1))
    else
      echo "  DELETE failed: $DEL_RESP"
      echo "  RESULT: probe 2 partial — post worked but delete failed; manually delete ts=$POST_TS"
      FAIL=$((FAIL+1))
    fi
  else
    echo "  POST response: $POST_RESP"
    echo "  RESULT: bot CANNOT post in $CHANNEL (probe 2 FAIL — channel/token issue)"
    FAIL=$((FAIL+1))
  fi
fi

# Probe 3 — Primary provider (MiniMax via anthropic-compatible endpoint)
echo ""
echo "--- PROBE 3: Primary provider (MiniMax-M3) ---"
PRIM_BASE="${MINIMAX_BASE_URL:-}"
PRIM_KEY="${MINIMAX_API_KEY:-}"
PRIM_MODEL="${MINIMAX_MODEL:-MiniMax-M3}"
if [ -z "$PRIM_BASE" ] || [ -z "$PRIM_KEY" ]; then
  echo "  RESULT: MINIMAX_BASE_URL or MINIMAX_API_KEY not in env (skipped — set them in ~/.profile)"
else
  PRIM_RESP=$(curl -sS -o /tmp/probe-prim-$$.json -w "%{http_code}" \
    -X POST "${PRIM_BASE%/}/v1/messages" \
    -H "x-api-key: $PRIM_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "{\"model\":\"$PRIM_MODEL\",\"max_tokens\":32,\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the single word pong.\"}]}" 2>&1)
  if [ "$PRIM_RESP" = "200" ]; then
    PRIM_TEXT=$(python3 -c 'import sys,json; d=json.load(open(sys.argv[1])); print(d["content"][0]["text"])' "/tmp/probe-prim-$$.json" 2>/dev/null || echo "?")
    echo "  HTTP 200, response=\"$PRIM_TEXT\""
    echo "  RESULT: primary is healthy (probe 3 OK)"
    PASS=$((PASS+1))
  elif [ "$PRIM_RESP" = "429" ]; then
    echo "  HTTP 429 — primary is RATE-LIMITED"
    echo "  RESULT: primary is dead (probe 3 FAIL — 429 rate limit)"
    FAIL=$((FAIL+1))
  else
    PRIM_BODY=$(cat "/tmp/probe-prim-$$.json" 2>/dev/null | head -c 300)
    echo "  HTTP $PRIM_RESP — body: $PRIM_BODY"
    echo "  RESULT: primary probe 3 FAIL"
    FAIL=$((FAIL+1))
  fi
  rm -f "/tmp/probe-prim-$$.json"
fi

# Probe 4 — Fallback provider (opencode-go / GLM)
echo ""
echo "--- PROBE 4: Fallback provider (opencode-go / glm-5.1) ---"
FB_KEY="${OPENCODE_GO_API_KEY:-}"
if [ -z "$FB_KEY" ]; then
  echo "  RESULT: OPENCODE_GO_API_KEY not in env (skipped — set in ~/.profile)"
else
  FB_RESP=$(curl -sS -o /tmp/probe-fb-$$.json -w "%{http_code}" \
    -X POST "https://opencode.ai/zen/go/v1/chat/completions" \
    -H "Authorization: Bearer $FB_KEY" \
    -H "content-type: application/json" \
    -d '{"model":"glm-5.1","max_tokens":16,"messages":[{"role":"user","content":"pong"}]}' 2>&1)
  if [ "$FB_RESP" = "200" ]; then
    echo "  HTTP 200, fallback is healthy (probe 4 OK)"
    PASS=$((PASS+1))
  elif [ "$FB_RESP" = "429" ]; then
    echo "  HTTP 429 — fallback is RATE-LIMITED (likely GoUsageLimitError, check gateway log)"
    echo "  RESULT: fallback is dead (probe 4 FAIL)"
    FAIL=$((FAIL+1))
  elif [ "$FB_RESP" = "403" ]; then
    FB_BODY=$(cat "/tmp/probe-fb-$$.json" 2>/dev/null | head -c 200)
    echo "  HTTP 403 — body: $FB_BODY"
    echo "  RESULT: Cloudflare is blocking egress; underlying cause is usually GoUsageLimitError (probe 4 FAIL)"
    FAIL=$((FAIL+1))
  else
    FB_BODY=$(cat "/tmp/probe-fb-$$.json" 2>/dev/null | head -c 300)
    echo "  HTTP $FB_RESP — body: $FB_BODY"
    echo "  RESULT: fallback probe 4 FAIL"
    FAIL=$((FAIL+1))
  fi
  rm -f "/tmp/probe-fb-$$.json"
fi

# Summary + root-cause taxonomy
echo ""
echo "================================================="
echo "SUMMARY: $PASS probes OK, $FAIL probes failed"
echo "================================================="
if [ "$FAIL" = "0" ]; then
  echo "All probes healthy. Gateway transport is fine; the original 'nothing happened'"
  echo "was likely a transient in the specific agent run. Self-recovers on next inbound."
elif [ "$FAIL" = "1" ] && echo "$LAUNCHD_OUT" | grep -q "state = " && ! echo "$LAUNCHD_OUT" | grep -q "state = running"; then
  echo "PROBE 1 (gateway state) failed. Restart:"
  echo "  launchctl kickstart -k gui/\$(id -u)/ai.hermes.prod"
elif [ "$FAIL" = "1" ] && [ "$POST_OK" != "True" ]; then
  echo "PROBE 2 (channel post) failed. Check channel membership for the bot:"
  echo "  /invite @hermes  (run in the channel)"
elif [ "$FAIL" -ge "1" ]; then
  echo "Provider-layer failure detected. Apply the SKILL.md taxonomy:"
  echo "  - Primary 429 + fallback OK = primary rate-limited; self-recovers."
  echo "  - Primary 429 + fallback 429 = BOTH providers quota-exhausted. This is the"
  echo "    recurring trap — gateway silently retries the dead fallback. Do NOT bounce."
  echo "    Reply directly in-thread (probe 2 path) with the root cause, then either"
  echo "    wait for quota refresh or edit fallback_providers in config.yaml."
  echo "  - Primary 401/403 = credential rotated. Update ~/.bashrc AND ~/.profile,"
  echo "    then restart gateway."
fi
exit "$FAIL"