#!/usr/bin/env bash
# PreToolUse hook: prevent `*` from breaking GitHub URLs in Slack messages.
# Triggered by SOUL.md COMMIT no-trailing-asteri[REDACTED_OPENAI_KEY]
#
# Behavior: when a tool call is `mcp__slack__conversations_add_message` with a
# text payload containing `https://github.com/...` adjacent to `*`, strip
# the `*` and write the cleaned text back as the response (Claude Code
# PreToolUse hook contract: stdout JSON with updated hookSpecificOutput).
#
# This hook is ROBUST (no $ROOT dependency) and exits 0 cleanly when not applicable.

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

# Only act on Slack add-message calls
if [ "$TOOL_NAME" != "mcp__slack__conversations_add_message" ]; then
  exit 0
fi

TEXT=$(echo "$INPUT" | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('text', '') or '')
except Exception:
    print('')
")

# Check for github URLs with adjacent asterisks
CLEANED=$(echo "$TEXT" | python3 -c "
import sys, re
text = sys.stdin.read()
# Strip `*` immediately before/after any https://github.com/... URL
# while preserving words around it.
text = re.sub(r'\\*+(https://github\\.com/[A-Za-z0-9_./\\-:?=&%#~+]+)', r'\\1', text)
text = re.sub(r'(https://github\\.com/[A-Za-z0-9_./\\-:?=&%#~+]+)\\*+', r'\\1', text)
print(text, end='')
")

if [ "$CLEANED" != "$TEXT" ]; then
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\",\"permissionDecisionReason\":\"stripped trailing * from PR URL per SOUL.md no-trailing-asteri[REDACTED_OPENAI_KEY]\"},\"updated_input\":{\"text\":\"$CLEANED\"}}"
else
  exit 0
fi
