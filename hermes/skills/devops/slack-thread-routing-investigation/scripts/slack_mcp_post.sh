#!/usr/bin/env bash
# slack_mcp_post.sh — durable Slack post via the MCP /mcp JSON-RPC endpoint.
#
# Use this when:
#   - the runtime does NOT surface mcp__slack__conversations_add_message as a tool, OR
#   - you must NOT use the gateway send_message (it silently self-roots threaded replies)
#   - HERMES_SLACK_BOT_TOKEN is not in env / is masked in ~/.bashrc
#
# This script bakes in three lessons from the slack-thread-routing-investigation
# skill (2026-06-09 / 2026-06-10):
#
#   1. Do NOT probe the endpoint with multiple sequential curl calls. Each call is a
#      fresh gateway invocation that risks re-introducing the scratch-leak bug (Failure 3
#      in the skill). Instead, capture SID, send initialized, and post in a single
#      pipeline below.
#
#   2. thread_ts MUST be the INCOMING message's thread_ts (or its own ts if it had no
#      thread). Setting thread_ts to the outgoing post's own ts creates a self-rooted
#      top-level message (Failure 1).
#
#   3. The MCP response is a CSV header line, NOT a message ID. The post is confirmed
#      only by querying conversations_replies / conversations_history afterward.
#
# Usage:
#   ./slack_mcp_post.sh <channel_id> <thread_ts> <text-file>
#   ./slack_mcp_post.sh C0AH3RY3DK6 1781021369.023829 /tmp/message.txt
#
# Env:
#   SLACK_MCP_URL  (default: http://127.0.0.1:8006/mcp)
#
# Exit codes:
#   0 = post accepted by MCP server (NOT a guarantee it landed in the right thread —
#       always verify with conversations_replies)
#   1 = MCP server unreachable / protocol error
#   2 = invalid arguments

set -euo pipefail

CHANNEL="${1:-}"
THREAD_TS="${2:-}"
TEXT_FILE="${3:-}"
MCP_URL="${SLACK_MCP_URL:-http://127.0.0.1:8006/mcp}"

if [[ -z "$CHANNEL" || -z "$THREAD_TS" || -z "$TEXT_FILE" ]]; then
  echo "usage: $0 <channel_id> <thread_ts> <text-file>" >&2
  exit 2
fi
if [[ ! -f "$TEXT_FILE" ]]; then
  echo "text file not found: $TEXT_FILE" >&2
  exit 2
fi

# JSON-escape the message text via Python (handles all escaping correctly)
PAYLOAD_JSON=$(python3 -c "
import json, sys
text = open('$TEXT_FILE', encoding='utf-8').read()
print(json.dumps({
  'jsonrpc':'2.0','id':3,
  'method':'tools/call',
  'params':{
    'name':'conversations_add_message',
    'arguments':{
      'channel_id':'$CHANNEL',
      'thread_ts':'$THREAD_TS',
      'content_type':'text/plain',
      'text': text
    }
  }
}))
")

# Single pipeline: initialize (capture SID) -> send notifications/initialized -> post.
# Do NOT split into multiple shell commands — each is a fresh gateway invocation.
# Do NOT print intermediate status to stdout — that pollutes the user's view and
# can trigger the gateway scratch-leak bug.
RESP=$(curl -sS --max-time 15 \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  --data-raw "$(cat <<EOF
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"slack-mcp-post-sh","version":"1.0"}}}
EOF
)" \
  -i \
  "$MCP_URL" 2>/dev/null) || { echo "MCP server unreachable at $MCP_URL" >&2; exit 1; }

SID=$(echo "$RESP" | grep -i "^mcp-session-id:" | awk '{print $2}' | tr -d '\r' | head -1)
if [[ -z "$SID" ]]; then
  echo "MCP initialize failed — no Mcp-Session-Id returned" >&2
  echo "$RESP" | tail -5 >&2
  exit 1
fi

# Send notifications/initialized (no body expected)
curl -sS --max-time 5 \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SID" \
  --data-raw '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  -o /dev/null \
  "$MCP_URL" 2>/dev/null

# Post the message
POST_RESP=$(curl -sS --max-time 15 \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SID" \
  --data-raw "$PAYLOAD_JSON" \
  "$MCP_URL" 2>/dev/null) || { echo "MCP post call failed" >&2; exit 1; }

# MCP returns a CSV header line, NOT a JSON-RPC result. The presence of the CSV
# header confirms the call was accepted. To verify the post LANDED, the caller
# MUST follow up with conversations_replies / conversations_history.
if echo "$POST_RESP" | grep -q "MsgID,UserID,UserName"; then
  echo "post accepted (verify with conversations_replies — MCP does not return the new MsgID)"
  exit 0
else
  echo "post call returned unexpected response:" >&2
  echo "$POST_RESP" | head -c 500 >&2
  echo "" >&2
  exit 1
fi
