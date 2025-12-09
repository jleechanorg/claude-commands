#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"QUESTION\" [MAX_OPINIONS]" >&2
  exit 1
fi

QUESTION="$1"
MAX_OPINIONS="${2:-3}"

MCP_URL="${SECOND_OPINION_MCP_URL:-https://ai-universe-backend-dev-114133832173.us-central1.run.app/mcp}"

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
BUILD_SCRIPT="$SCRIPT_DIR/build_second_opinion_request.py"
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

if [ ! -f "$BUILD_SCRIPT" ]; then
  echo "Error: request builder not found at $BUILD_SCRIPT" >&2
  exit 1
fi

REQUEST_FILE="$(mktemp /tmp/secondo_request.XXXXXX.json)"
RESPONSE_FILE="$(mktemp /tmp/secondo_response.XXXXXX.json)"
PARSED_FILE="$(mktemp /tmp/secondo_parsed.XXXXXX.json)"

BASE_REF=""
BASE_CANDIDATES=()
if [ -n "${SECOND_OPINION_BASE_REF:-}" ]; then
  BASE_CANDIDATES+=("$SECOND_OPINION_BASE_REF")
fi
BASE_CANDIDATES+=("origin/main" "main" "master")

for candidate in "${BASE_CANDIDATES[@]}"; do
  if git rev-parse --verify "${candidate}^{commit}" >/dev/null 2>&1; then
    BASE_REF="$candidate"
    break
  fi
done

if [ -z "$BASE_REF" ]; then
  if git rev-parse --verify "HEAD^" >/dev/null 2>&1; then
    BASE_REF="HEAD^"
    echo "⚠️  Warning: Could not resolve base branch, using HEAD^ for diff context." >&2
  else
    BASE_REF="HEAD"
    echo "⚠️  Warning: Could not resolve comparison point; using HEAD (no diff)." >&2
  fi
fi

echo "→ Building request payload with git context (base: $BASE_REF)"
if ! python3 "$BUILD_SCRIPT" "$REQUEST_FILE" "$QUESTION" "$MAX_OPINIONS" "$BASE_REF"; then
  echo "Error: Failed to build MCP request payload." >&2
  exit 1
fi

echo "→ Retrieving authentication token (auto-refreshes if expired)"
# Use AI Universe Firebase project credentials (not default worldarchitecture-ai)
# These can be overridden via environment variables
export FIREBASE_PROJECT_ID="${AI_UNIVERSE_FIREBASE_PROJECT_ID:-ai-universe-b3551}"
export FIREBASE_AUTH_DOMAIN="${AI_UNIVERSE_FIREBASE_AUTH_DOMAIN:-ai-universe-b3551.firebaseapp.com}"
export FIREBASE_API_KEY="${AI_UNIVERSE_FIREBASE_API_KEY}"

if ! TOKEN=$(node "$AUTH_CLI" token 2>&1); then
  echo "❌ Error: Failed to get authentication token." >&2
  echo "$TOKEN" >&2
  echo "" >&2
  echo "   Please authenticate with:" >&2
  echo "   FIREBASE_PROJECT_ID=ai-universe-b3551 \\" >&2
  echo "   FIREBASE_AUTH_DOMAIN=ai-universe-b3551.firebaseapp.com \\" >&2
  echo "   FIREBASE_API_KEY=\$AI_UNIVERSE_FIREBASE_API_KEY \\" >&2
  echo "   node $AUTH_CLI login" >&2
  exit 1
fi

if [ -z "$TOKEN" ]; then
  echo "❌ Error: Empty token returned from auth-cli.mjs" >&2
  exit 1
fi

echo "→ Sending request via HTTPie (timeout 180s)"
if ! http --check-status POST "$MCP_URL" \
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
