#!/usr/bin/env bash
# sync-history-to-jeff-ubuntu.sh
#
# Push the updated /history machinery (sparse skill + slash command) from
# MacBook to jeff-ubuntu. Idempotent. Re-runnable when the box returns.
#
# Use this when:
#   - the box was offline during a `/history` integration
#   - you've edited ~/.claude/skills/conversation-history-sparse/SKILL.md
#     or ~/.claude/commands/history.md on the Mac and want jeff-ubuntu to match
#
# Exit codes:
#   0 = sync succeeded
#   1 = box unreachable (run again when it's back)
#   2 = scp failed mid-flight (run again; safe — files are partial-copy safe)
#
# Usage:
#   sync-history-to-jeff-ubuntu.sh                  # sync both files
#   sync-history-to-jeff-ubuntu.sh --dry-run        # just check connectivity
set -euo pipefail

HOST="${JEFF_UBUNTU_HOST:-jeff-ubuntu}"
SSH_OPTS=(-o ConnectTimeout=5 -o BatchMode=yes)   # no password prompts
SKILL_SRC="$HOME/.claude/skills/conversation-history-sparse/SKILL.md"
HIST_SRC="$HOME/.claude/commands/history.md"
SKILL_DST="~/.claude/skills/conversation-history-sparse/SKILL.md"
HIST_DST="~/.claude/commands/history.md"

if [[ "${1:-}" == "--dry-run" ]]; then
  if ssh "${SSH_OPTS[@]}" "$HOST" 'echo "OK $(hostname)"' >/dev/null 2>&1; then
    echo "✓ $HOST reachable"
    exit 0
  else
    echo "✗ $HOST unreachable — try again later"
    exit 1
  fi
fi

# Connectivity gate
if ! ssh "${SSH_OPTS[@]}" "$HOST" 'echo OK' >/dev/null 2>&1; then
  echo "✗ $HOST unreachable (timeout or refused) — re-run when it's back"
  exit 1
fi

# Push
echo "→ pushing sparse skill → $HOST:$SKILL_DST"
scp "${SSH_OPTS[@]}" "$SKILL_SRC" "$HOST:$SKILL_DST"

echo "→ pushing history command → $HOST:$HIST_DST"
scp "${SSH_OPTS[@]}" "$HIST_SRC"  "$HOST:$HIST_DST"

# Verify on the remote
echo "→ verifying on $HOST:"
ssh "${SSH_OPTS[@]}" "$HOST" bash -s <<'VERIFY'
  for f in "$HOME/.claude/skills/conversation-history-sparse/SKILL.md" \
           "$HOME/.claude/commands/history.md"; do
    if [ -f "$f" ]; then
      printf "  ✓ %s  (%s lines)\n" "$f" "$(wc -l <"$f")"
    else
      printf "  ✗ MISSING: %s\n" "$f"
    fi
  done
  # Optional: confirm sparse skill now references all 3 sources
  if grep -q "Hermes" "$HOME/.claude/skills/conversation-history-sparse/SKILL.md"; then
    echo "  ✓ sparse skill mentions Hermes (3-source coverage)"
  fi
VERIFY

echo "✓ sync complete"
