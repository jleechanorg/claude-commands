#!/bin/bash
# audit-launchd-stale-paths.sh
#
# Detect launchd plists in ~/Library/LaunchAgents/ whose ProgramArguments
# reference a stale path (deleted worktree, ephemeral install dir, etc.).
# Run this BEFORE deleting any harness/worktree to detect the fan-out
# silent-127 class early, OR after fixing one job to catch the sibling
# plists that share the same root cause.
#
# Verified 2026-07-22 — caught 5 plists with the same
# `$HOME/.ao/data/worktrees/jleechanclaw-harness/jleechanclaw-harness-9/scripts/`
# path. Fix is one-line `sed` per plist (see hermes-health-check SKILL §
# "Stale worktree path baked into multiple plists").
#
# Usage:
#   bash ~/.hermes/skills/devops/hermes-health-check/scripts/audit-launchd-stale-paths.sh
#
# Exit codes:
#   0 = no stale paths detected (clean)
#   1 = one or more stale paths detected (printed below)
#   2 = script error (e.g. LaunchAgents dir missing)

set -u

LAUNCHD_DIR="$HOME/Library/LaunchAgents"

if [[ ! -d "$LAUNCHD_DIR" ]]; then
    echo "ERROR: $LAUNCHD_DIR not found" >&2
    exit 2
fi

# Patterns that signal "ephemeral, will break when dir deleted":
# - worktrees/ (git worktree installs)
# - /tmp/ (never survive reboot)
# - any $HOME/.* that is NOT .hermes/, .hermes_prod/, or Library/
SAFE_PATTERN='^$HOME/(\.hermes|\.hermes_prod|Library)/'

STALE=0
for f in "$LAUNCHD_DIR"/*.plist; do
    [[ -f "$f" ]] || continue
    # Extract every <string>...</string> inside ProgramArguments. plutil is
    # more robust than grep but greppable for our purposes.
    strings=$(grep -oE '<string>[^<]+</string>' "$f" | sed 's/<\/\?string>//g' || true)
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        # Skip plain commands (/bin/bash, /usr/bin/curl, etc.)
        [[ "$line" == /* ]] || continue
        # Only flag paths under $HOME that don't match the safe pattern
        if [[ "$line" == $HOME/* ]] && \
           ! echo "$line" | grep -qE "$SAFE_PATTERN"; then
            echo "STALE: $f"
            echo "       $line"
            STALE=$((STALE + 1))
        fi
        # Also flag /tmp/ paths in ProgramArguments
        if [[ "$line" == /tmp/* ]]; then
            echo "STALE (tmp): $f"
            echo "       $line"
            STALE=$((STALE + 1))
        fi
        # Also flag worktrees/ anywhere
        if [[ "$line" == *worktrees/* ]]; then
            echo "STALE (worktree): $f"
            echo "       $line"
            STALE=$((STALE + 1))
        fi
    done <<< "$strings"
done

if [[ $STALE -gt 0 ]]; then
    echo ""
    echo "Total stale-path references: $STALE"
    echo ""
    echo "Quick fix template (replace PREFIX with the canonical path):"
    echo '  sed -i.bak "s|<stale prefix>|<canonical prefix>|g" <plist>'
    echo '  launchctl unload <plist> && launchctl load -w <plist>'
    echo ""
    exit 1
fi

echo "OK: no stale paths detected across $(ls "$LAUNCHD_DIR"/*.plist 2>/dev/null | wc -l | tr -d ' ') plists"
exit 0
