#!/usr/bin/env bash
# Keep Claude Code's cached bughunter/ultrareview experiment disabled.
# Claude may refresh cachedGrowthBookFeatures from remote config, so this is
# intentionally idempotent and safe to run on startup and prompt submission.

set -u

STATE_FILE="${CLAUDE_BUGHUNTER_STATE_FILE:-$HOME/.claude.json}"
LOCK_DIR="${STATE_FILE}.bughunter-lock"

if [ ! -f "$STATE_FILE" ] || ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

locked=0
for _attempt in 1 2 3 4 5 6 7 8 9 10; do
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    locked=1
    break
  fi
  sleep 0.05
done

if [ "$locked" != "1" ]; then
  exit 0
fi

cleanup() {
  rm -rf "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

tmp_file="$(mktemp "${STATE_FILE}.tmp.XXXXXX" 2>/dev/null || true)"
if [ -z "$tmp_file" ]; then
  exit 0
fi

if jq '
  .cachedGrowthBookFeatures = (.cachedGrowthBookFeatures // {}) |
  .cachedGrowthBookFeatures.tengu_review_bughunter_config =
    ((.cachedGrowthBookFeatures.tengu_review_bughunter_config // {}) + {
      "enabled": false,
      "model": "claude-sonnet-4-6"
    })
' "$STATE_FILE" > "$tmp_file" 2>/dev/null; then
  if cmp -s "$STATE_FILE" "$tmp_file"; then
    rm -f "$tmp_file"
  else
    chmod 600 "$tmp_file" 2>/dev/null || true
    mv "$tmp_file" "$STATE_FILE"
  fi
else
  rm -f "$tmp_file"
fi

exit 0
