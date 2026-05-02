#!/usr/bin/env bash
# PreToolUse hook: block unauthorized writes to openclaw.json / openclaw.staging.json
# Reads JSON payload from stdin in Claude Code PreToolUse format.
# Exit 2 = block the tool call.

set -euo pipefail

payload="$(cat)"

tool_name="$(printf '%s' "$payload" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)"

# Only care about Edit and Write tools
case "$tool_name" in
  Edit|Write) ;;
  *) exit 0 ;;
esac

# Extract the target file path (field name differs by tool)
file_path="$(printf '%s' "$payload" | python3 -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('tool_input', {})
# Edit uses 'file_path'; Write uses 'file_path' too
print(inp.get('file_path', ''))
" 2>/dev/null || true)"

# Check if the path targets either config file
case "$file_path" in
  *openclaw.json*|*openclaw.staging.json*)
    echo "BLOCKED: openclaw.json changes require explicit user approval (doctor.sh enforces maxConcurrent=10, timeoutSeconds=600). Ask the user first." >&2
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
