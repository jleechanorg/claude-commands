#!/bin/bash
set -euo pipefail
shopt -s extglob

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_FILE="$SCRIPT_DIR/cron_entry.txt"

if ! command -v crontab >/dev/null 2>&1; then
    echo "crontab command not found; install cron before running this script" >&2
    exit 1
fi

if [[ ! -f "$CRON_FILE" ]]; then
    echo "Cron template not found at $CRON_FILE" >&2
    exit 1
fi

TEMP_CRON=$(mktemp)
trap 'rm -f "$TEMP_CRON"' EXIT

if ! crontab -l >"$TEMP_CRON" 2>/dev/null; then
    : >"$TEMP_CRON"
fi

added=0
pending_comments=""
while IFS= read -r line || [[ -n "$line" ]]; do
    trimmed_leading="${line##+([[:space:]])}"
    if [[ -z "${line//[[:space:]]/}" ]]; then
        pending_comments=""
        continue
    fi

    if [[ -n "$trimmed_leading" && "${trimmed_leading:0:1}" == "#" ]]; then
        if [[ -z "$pending_comments" ]]; then
            pending_comments="$line"
        else
            pending_comments+=$'\n'"$line"
        fi
        continue
    fi

    if grep -Fx -- "$line" "$TEMP_CRON" >/dev/null; then
        pending_comments=""
        continue
    fi

    if [[ -n "$pending_comments" ]]; then
        printf '%s\n' "$pending_comments" >>"$TEMP_CRON"
        pending_comments=""
    fi

    printf '%s\n' "$line" >>"$TEMP_CRON"
    added=1

done <"$CRON_FILE"

if [[ $added -eq 1 ]]; then
    crontab "$TEMP_CRON"
    echo "Installed missing cron entries from $CRON_FILE"
else
    echo "Cron entries already present; no changes made"
fi
