#!/bin/bash
# PreCompact guard — blocks premature auto-compaction for interactive sessions
# Exit 0 = allow compaction
# Exit 2 = block compaction
#
# AO workers need compaction (they run long, hit real limits).
# Interactive sessions get blocked (150K threshold is too aggressive for 1M).

LOG_FILE="$HOME/.claude/compaction-guard.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Detect AO worker: AO_SESSION or AO_WORKER env vars are set by ao spawn
if [ -n "$AO_SESSION" ] || [ -n "$AO_WORKER" ] || [ -n "$CLAUDE_HEADLESS" ]; then
  echo "$TIMESTAMP ALLOWED compaction (AO worker / headless)" >> "$LOG_FILE"
  exit 0
fi

# Interactive session — block auto-compaction
echo "$TIMESTAMP BLOCKED auto-compaction (interactive guard)" >> "$LOG_FILE"
exit 2
