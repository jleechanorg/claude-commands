#!/usr/bin/env bash
# backup-fleet-audit.sh — One-shot audit of all backup/sync/snapshot surfaces
# That could push personal home-dir content to a public GitHub repo.
# Run this AFTER fixing any backup/ leak to find sibling landmines.
# Companion to skill: home-config-backup-audit
#
# Usage:
#   bash backup-fleet-audit.sh [OUTPUT_MD_PATH]
# Default output: ~/.hermes/logs/backup-fleet-audit-$(date +%Y%m%d-%H%M%S).md
#
# Outputs a Markdown report with:
#   - Loaded launchd jobs (filtered) + their scripts
#   - System crontab entries (filtered)
#   - Dormant plists in ~/Library/LaunchAgents/
#   - Scripts with both git push AND backup/home/snapshot patterns
#   - Per-script push destination + privacy classification

set -uo pipefail
OUT="${1:-$HOME/.hermes/logs/backup-fleet-audit-$(date +%Y%m%d-%H%M%S).md}"
mkdir -p "$(dirname "$OUT")"
exec > >(tee "$OUT") 2>&1

echo "# Backup-fleet audit"
echo
echo "**Date:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "**Host:** $(hostname -s)"
echo

# ─── Surface 1: Loaded launchd jobs ──────────────────────────────────────────
echo "## Surface 1: Loaded launchd jobs (backup/home/snapshot/sync)"
echo
echo '```'
launchctl list 2>/dev/null | grep -iE "backup|home-config|user-scope|conversation-backup|di[REDACTED_OPENAI_KEY]|cron-backup|qdrant-backup|snapshot|home\.sh|openclaw-backup" | head -40
echo '```'
echo

# ─── Surface 2: System crontab ───────────────────────────────────────────────
echo "## Surface 2: User crontab"
echo
echo '```'
crontab -l 2>/dev/null | grep -iE "backup|home-config|snapshot|/bin/bash.*home|rsync|tar" | head -20
echo '```'
echo

# ─── Surface 3: Dormant / disabled plists ────────────────────────────────────
echo "## Surface 3: Plists in ~/Library/LaunchAgents/ (loaded + dormant)"
echo
echo '```'
ls -la ~/Library/LaunchAgents/ 2>/dev/null | grep -iE "backup|home-config|user-scope|snapshot|conversation-backup|qdrant-backup" | head -20
echo '```'
echo

# ─── Surface 4: Scripts with backup-push logic ──────────────────────────────
echo "## Surface 4: Scripts with BOTH git push AND backup/home/snapshot patterns"
echo
echo "_(excluding known per-repo wrappers: push.sh / sync_branch.sh / integrate.sh / commit-pending.sh / auto-push-to-main.sh / consolidate-* / ao-go-repo-recovery.sh)_"
echo
echo '```'
CANDIDATES=$(grep -l "git push" \
    ~/scripts/*.sh \
    ~/.hermes/scripts/*.sh \
    ~/projects_other/*/scripts/*.sh \
    2>/dev/null | \
    grep -vE "push\.sh$|sync_branch\.sh$|integrate\.sh$|commit-pending.*\.sh$|auto-push-to-main\.sh$|consolidate-.*\.sh$|ao-go-repo-recovery\.sh$|/ao[$\s]|aow|/bd$" | \
    sort -u)
for f in $CANDIDATES; do
    if grep -qE "backup/|/backup|home-config|user_scope|~/|\$\{HOME\}|\$\HOME" "$f" 2>/dev/null; then
        echo "=== $f ==="
        grep -nE "git push|hub api|gh repo|backup/|home-config|user_scope|ALLOW_GIT_BACKUP" "$f" | head -8
        echo
    fi
done
echo '```'
echo

# ─── Surface 5: Push destination + privacy ───────────────────────────────────
echo "## Surface 5: Per-script push destination + privacy classification"
echo
echo "For each script above, find REPO_ROOT and classify its remote."
echo
printf "%-65s %-25s %s\n" "Script" "REPO_ROOT" "Remote (private/public)"
echo "-----------------------------------------------------------------------------------------"
for f in $CANDIDATES; do
    if grep -qE "backup/|/backup|home-config|user_scope" "$f" 2>/dev/null; then
        # Extract REPO_ROOT = $SCRIPT_DIR/.. (most common pattern)
        REPO=$(grep -m1 "REPO_ROOT=" "$f" 2>/dev/null | sed 's/.*REPO_ROOT=//' | sed 's/[ "]*$//')
        if [[ -z "$REPO" ]] || [[ "$REPO" == *"HOME"* ]]; then
            # Try $SCRIPT_DIR/..
            SCRIPT_DIR=$(dirname "$f")
            REPO="$SCRIPT_DIR/.."
        fi
        REPO_ABS=$(cd "$REPO" 2>/dev/null && pwd)
        if [[ -z "$REPO_ABS" ]] || [[ ! -d "$REPO_ABS/.git" ]]; then
            printf "%-65s %-25s %s\n" "$(basename "$f")" "NOT-A-REPO" "—"
            continue
        fi
        REMOTE=$(git -C "$REPO_ABS" remote get-url origin 2>/dev/null || echo "(none)")
        if [[ -z "$REMOTE" ]] || [[ "$REMOTE" == "(none)" ]]; then
            CLASS="local-only"
        elif [[ "$REMOTE" == *github.com/jleechanorg/* ]] || [[ "$REMOTE" == *github.com/Agnt-F/* ]]; then
            CLASS="JLEECHANORG-PUBLIC"
        else
            CLASS="review-needed"
        fi
        printf "%-65s %-25s %s [%s]\n" "$(basename "$f")" "$(basename "$REPO_ABS")" "$REMOTE" "$CLASS"
    fi
done
echo
echo "_Verify privacy classification by visiting each remote URL on github.com/web. Default JLEECHANORG org = public._"
echo

# ─── Surface 6: Recurring pipeline callers ───────────────────────────────────
echo "## Surface 6: Scripts that CALL backup scripts (recurring-pipeline risk)"
echo
echo '```'
grep -lE "backup-home|backup-hermes|backup-openclaw|backup-smartclaw|disk_magician" \
    $HOME/scripts/*.sh \
    $HOME/.worktrees/*/scripts/*.sh \
    $HOME/projects_other/*/scripts/*.sh \
    2>/dev/null | head -20
echo '```'
echo

# ─── Final summary ───────────────────────────────────────────────────────────
echo "## Summary"
echo
echo "- **Loaded backup jobs:** $(launchctl list 2>/dev/null | grep -ciE "backup|home-config|user-scope|snapshot")"
echo "- **Dormant plists:** $(ls ~/Library/LaunchAgents/ 2>/dev/null | grep -ciE "backup|home-config|user-scope|snapshot")"
echo "- **Backup-push scripts:** $(echo "$CANDIDATES" | grep -cE '.')"
echo "- **Public-destination scripts:** $(for f in $CANDIDATES; do grep -qE "backup/" "$f" 2>/dev/null && grep -qE "~/|HOME|user_scope" "$f" 2>/dev/null && grep -q "git push" "$f" 2>/dev/null && (grep -q 'origin main\|origin "$branch"\|HEAD:refs' "$f" 2>/dev/null) && echo "$f"; done | wc -l)"
echo

echo "Audit complete. Review the report and act on any JLEECHANORG-PUBLIC rows."
