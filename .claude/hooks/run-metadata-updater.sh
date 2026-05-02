#!/usr/bin/env bash
# Wrapper: invokes scripts/ao-metadata-updater.sh (tracked) or legacy .claude/metadata-updater.sh.
# Used by both PreToolUse and PostToolUse Bash hooks in .claude/settings.json.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ROOT=$(git rev-parse --show-toplevel)
    if [ -x "$ROOT/scripts/ao-metadata-updater.sh" ]; then
        exec "$ROOT/scripts/ao-metadata-updater.sh"
    fi
    [ -x "$ROOT/.claude/metadata-updater.sh" ] && exec "$ROOT/.claude/metadata-updater.sh"
    [ -x "$ROOT/.cursor/metadata-updater.sh" ] && exec "$ROOT/.cursor/metadata-updater.sh"
fi
exit 0
