#!/bin/bash
# Wrapper: invokes .claude/metadata-updater.sh if it exists and is executable.
# Used by both PreToolUse and PostToolUse Bash hooks in settings.json.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ROOT=$(git rev-parse --show-toplevel)
    [ -x "$ROOT/.claude/metadata-updater.sh" ] && exec "$ROOT/.claude/metadata-updater.sh"
fi
exit 0
