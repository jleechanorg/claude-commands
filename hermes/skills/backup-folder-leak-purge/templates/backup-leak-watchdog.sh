#!/usr/bin/env bash
# backup-leak-watchdog.sh — TEMPLATE for a watchdog that detects re-emergence
# of a backup-push cron path. Install at <path> + wrap in a launchd plist
# (StartInterval 900 = 15 min). Posts to Slack on anomaly, 6h cooldown.
#
# Two modes (toggle with MODE env var in the plist):
#   MODE=full-disable  (default) — checks that disabled labels are unloaded,
#                                 disabled scripts stay chmod 000, and
#                                 DISABLED_PLISTS stay .disabled-suffixed.
#                                 Use this if the user wants the cron killed
#                                 completely.
#   MODE=push-only-disable      — checks that ALLOW_GIT_BACKUP_PUSH stays 0
#                                 in the active plist (cron is allowed to keep
#                                 running locally; only the push must stay off).
#                                 Use this if the user wants local backups
#                                 preserved but no push to public repos.
#
# Configure by setting these vars in the plist's EnvironmentVariables dict or
# at the top of the script:
#   MODE                        — "full-disable" | "push-only-disable"
#   HERMES_SLACK_BOT_TOKEN      — required for Slack alerts
#   HERMES_OPS_SLACK_CHANNEL    — default: #all-$USER-ai
#   CRON_LABEL                  — e.g. "org.$USER.user-scope-backup"
#   CRON_PLIST_PATH             — absolute path to active plist
#   WATCH_REPO                  — GitHub repo to scan for forbidden paths
#   FORBIDDEN_PATH_PREFIXES     — regex alternation; default "^backup/"
#   COOLDOWN_SECONDS            — default 21600 (6h)
#
# Provenance: 2026-07-15 — v1 forced "label must be unloaded" which false-fired
# after we switched to the targeted fix (cron kept running, ALLOW_GIT_BACKUP_PUSH=0).
# v2 adds MODE=push-only-disable so the watchdog matches whichever fix shape was applied.

set -euo pipefail

LABEL="${LABEL:-ai.hermes.backup-leak-watchdog}"
MODE="${MODE:-full-disable}"  # or "push-only-disable"

CRON_LABEL="${CRON_LABEL:-org.$USER.user-scope-backup}"
CRON_PLIST_PATH="${CRON_PLIST_PATH:-$HOME/Library/LaunchAgents/${CRON_LABEL}.plist}"

WATCH_REPO="${WATCH_REPO:-jleechanorg/claude-commands}"
WATCH_BRANCH="${WATCH_BRANCH:-main}"
FORBIDDEN_PATH_PREFIXES="${FORBIDDEN_PATH_PREFIXES:-^backup/}"
HERMES_OPS_SLACK_CHANNEL="${HERMES_OPS_SLACK_CHANNEL:-#all-$USER-ai}"
COOLDOWN_SECONDS="${COOLDOWN_SECONDS:-21600}"

STATE_DIR="${STATE_DIR:-$HOME/Library/Application Support/$LABEL}"
LOG="${LOG:-$HOME/Library/Logs/${LABEL}.log}"
mkdir -p "$STATE_DIR"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] watchdog tick (mode=$MODE)" >> "$LOG"

post_slack() {
    local msg="$1"
    if [[ -n "${HERMES_SLACK_BOT_TOKEN:-}" ]]; then
        local payload
        payload=$(python3 -c 'import json,sys; print(json.dumps({"channel": "'"$HERMES_OPS_SLACK_CHANNEL"'", "text": sys.argv[1]}))' "$msg")
        curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
            -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
            -H "Content-Type: application/json; charset=utf-8" \
            -d "$payload" >/dev/null 2>&1 || log "WARN: slack post failed (token missing or scope)"
    fi
    log "ALERT: $msg"
}

cooldown_ok() {
    local key="$1"
    local stamp_file="$STATE_DIR/${key}.last_alert"
    if [[ -f "$stamp_file" ]]; then
        local last now
        last=$(cat "$stamp_file" 2>/dev/null || echo 0)
        now=$(date +%s)
        if (( now - last < COOLDOWN_SECONDS )); then
            return 1
        fi
    fi
    date +%s > "$stamp_file"
    return 0
}

anomalies=()

# ─── Mode 1: full-disable — cron must stay unloaded, scripts chmod 000 ────────
if [[ "$MODE" == "full-disable" ]]; then
    # Check 1a: launchd labels stay unloaded
    for label in ${CRON_LABEL}; do
        if launchctl list 2>/dev/null | grep -q "$label"; then
            anomalies+=("🛑 launchd job $label is REGISTERED (should be disabled in MODE=full-disable)")
        fi
    done

    # Check 1b: backup scripts stay chmod 000
    for script in ${DISABLED_SCRIPTS:-}; do
        if [[ -f "$script" ]]; then
            perms=$(stat -f %Lp "$script" 2>/dev/null || echo "?")
            if [[ "$perms" != "0" ]]; then
                anomalies+=("⚠️  $script is executable (perms=$perms). MODE=full-disable requires chmod 000")
            fi
        fi
    done

    # Check 1c: plists must stay .disabled-suffixed
    for plist in ${DISABLED_PLISTS:-}; do
        if [[ -f "$plist" ]] && [[ ! "$plist" =~ \.disabled- ]]; then
            anomalies+=("⚠️  $plist is enabled (not .disabled-suffixed)")
        fi
    done

# ─── Mode 2: push-only-disable — cron OK to run, but push env must stay 0 ────
elif [[ "$MODE" == "push-only-disable" ]]; then
    if [[ -f "$CRON_PLIST_PATH" ]]; then
        push_value=$(plutil -extract ALLOW_GIT_BACKUP_PUSH raw "$CRON_PLIST_PATH" 2>/dev/null || echo "absent")
        if [[ "$push_value" == "1" ]]; then
            anomalies+=("🚨 $CRON_PLIST_PATH has ALLOW_GIT_BACKUP_PUSH=1 — cron will push to origin on next tick. Set to 0 to restore safe behavior.")
        fi
    fi
fi

# ─── Always-on Check: origin/$WATCH_BRANCH must have 0 forbidden paths ───────
forbidden_count=$(curl -fsS \
    "https://api.github.com/repos/$WATCH_REPO/git/trees/$WATCH_BRANCH?recursive=1" 2>/dev/null \
    | python3 -c "
import json, sys, re
try:
    d = json.load(sys.stdin)
    patterns = re.split(r'\|', '''$FORBIDDEN_PATH_PREFIXES''')
    count = sum(1 for t in d.get('tree', [])
                if any(re.search(p, t['path']) for p in patterns))
    print(count)
except Exception:
    print(-1)
")
if [[ "$forbidden_count" -gt 0 ]]; then
    anomalies+=("🛑 $WATCH_REPO @$WATCH_BRANCH has $forbidden_count paths matching $FORBIDDEN_PATH_PREFIXES")
fi

# Cooldown-gated alerts
for msg in "${anomalies[@]}"; do
    key=$(echo "$msg" | head -c 32 | tr ' /' '__')
    if cooldown_ok "$key"; then
        post_slack "🔴 backup-leak watchdog: $msg"
    fi
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] tick complete: ${#anomalies[@]} anomalies" >> "$LOG"
