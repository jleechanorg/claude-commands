#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"QUESTION\" [MAX_OPINIONS]" >&2
  exit 1
fi

QUESTION="$1"
MAX_OPINIONS="${2:-3}"

if ! [[ "$MAX_OPINIONS" =~ ^[0-9]+$ ]] || [ "$MAX_OPINIONS" -le 0 ]; then
  echo "Error: MAX_OPINIONS must be a positive integer." >&2
  exit 1
fi

# Locate auth-cli.mjs (check ~/.claude/scripts first, then project scripts)
AUTH_CLI="$HOME/.claude/scripts/auth-cli.mjs"
if [ ! -f "$AUTH_CLI" ]; then
  # Fallback to project root scripts directory
  AUTH_CLI="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/.claude/scripts/auth-cli.mjs"
fi

if [ ! -f "$AUTH_CLI" ]; then
  echo "❌ Error: auth-cli.mjs not found. Expected at ~/.claude/scripts/auth-cli.mjs" >&2
  echo "   Run /localexportcommands to install authentication CLI" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUEST_FILE=""
RESPONSE_FILE=""
PARSED_FILE=""

cleanup() {
  if [ "${KEEP_TEMP_FILES:-0}" = "1" ]; then
    return
  fi

  [ -n "$REQUEST_FILE" ] && rm -f "$REQUEST_FILE"
  [ -n "$RESPONSE_FILE" ] && rm -f "$RESPONSE_FILE"
  [ -n "$PARSED_FILE" ] && rm -f "$PARSED_FILE"
}

trap cleanup EXIT

for cmd in http jq python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command '$cmd' is not available in PATH." >&2
    exit 1
  fi
done

REQUEST_FILE="$(mktemp /tmp/secondo_request.XXXXXX.json)"
RESPONSE_FILE="$(mktemp /tmp/secondo_response.XXXXXX.json)"
PARSED_FILE="$(mktemp /tmp/secondo_parsed.XXXXXX.json)"

echo "→ Building request payload at $REQUEST_FILE"
jq -n \
  --arg question "$QUESTION" \
  --argjson maxOpinions "$MAX_OPINIONS" \
  '{
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "agent.second_opinion",
      arguments: {
        question: $question,
        maxOpinions: $maxOpinions
      }
    },
    id: 1
  }' > "$REQUEST_FILE"

echo "→ Retrieving authentication token (auto-refreshes if expired)"
if ! TOKEN=$(node "$AUTH_CLI" token 2>&1); then
  echo "❌ Error: Failed to get authentication token." >&2
  echo "$TOKEN" >&2
  echo "" >&2
  echo "   Please authenticate with:" >&2
  echo "   node $AUTH_CLI login" >&2
  exit 1
fi

if [ -z "$TOKEN" ]; then
  echo "❌ Error: Empty token returned from auth-cli.mjs" >&2
  exit 1
fi

echo "→ Sending request via HTTPie (timeout 180s)"
if ! http --check-status POST https://ai-universe-backend-final.onrender.com/mcp \
  "Accept:application/json, text/event-stream" \
  "Authorization:Bearer $TOKEN" \
  < "$REQUEST_FILE" \
  --timeout=180 \
  --print=b > "$RESPONSE_FILE"; then
  echo "Error: HTTP request failed. Inspect $RESPONSE_FILE for the raw response." >&2
  exit 1
fi

echo "→ Extracting embedded JSON to $PARSED_FILE"
if ! jq -er '.result.content[0].text' "$RESPONSE_FILE" > "$PARSED_FILE"; then
  echo "Error: Response missing .result.content[0].text. Raw response saved to $RESPONSE_FILE." >&2
  exit 1
fi

echo "→ Summary"
python3 "$SCRIPT_DIR/parse_second_opinion.py" "$PARSED_FILE"

echo
if [ "${KEEP_TEMP_FILES:-0}" = "1" ]; then
  cat <<MSG
Raw files saved (KEEP_TEMP_FILES=1):
  Request : $REQUEST_FILE
  Response: $RESPONSE_FILE
  Parsed  : $PARSED_FILE
MSG
else
  cat <<MSG
Temporary files cleaned up. Re-run with KEEP_TEMP_FILES=1 to retain copies.
Last paths used:
  Request : $REQUEST_FILE
  Response: $RESPONSE_FILE
  Parsed  : $PARSED_FILE
MSG
fi
