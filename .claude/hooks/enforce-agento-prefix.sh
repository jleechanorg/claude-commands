#!/usr/bin/env bash
# enforce-agento-prefix.sh — PreToolUse hook to block gh pr create without [agento] prefix (bd-pfx)
# Agents create PRs without [agento] prefix ~28% of the time, causing miscounting of autonomous work.
# This hook blocks at the tool level — agentRules alone are insufficient.

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

# Only check commands that contain gh pr create
if ! echo "$TOOL_INPUT" | grep -qE 'gh\s+pr\s+create'; then
  exit 0
fi

# Extract title using a helper Python script for reliable parsing
TITLE=$(echo "$TOOL_INPUT" | python3 "$(dirname "$0")/enforce-agento-prefix-extract.py")

if [ -z "$TITLE" ]; then
  # No --title flag found — might be using stdin or interactive mode, let it through
  exit 0
fi

# Check if title starts with [agento] (case-insensitive)
if echo "$TITLE" | grep -qiE '^\[agento\]'; then
  exit 0
fi

echo "BLOCKED: PR title must start with [agento] prefix."
echo ""
echo "Current title: $TITLE"
echo "Required format: [agento] <rest of title>"
echo ""
echo "Add the [agento] prefix to your --title argument and retry."
echo "See bd-pfx: agents create PRs without prefix ~28% of the time."
exit 1
