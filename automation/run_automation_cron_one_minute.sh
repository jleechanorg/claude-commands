#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install_cron_entries.sh"
RUN_MINUTES="${1:-1}"
BACKUP_DIR="$HOME/.cron_backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/crontab_${TIMESTAMP}_one_minute_test.backup"
CRONTAB_SNAPSHOT="$(mktemp)"

if [[ ! "$RUN_MINUTES" =~ ^[0-9]+$ ]] || [[ "$RUN_MINUTES" -lt 1 ]]; then
    echo "Usage: $0 [minutes]" >&2
    echo "  minutes must be an integer >= 1" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

CRONTAB_PRESENT=0
if ! crontab -l >"$CRONTAB_SNAPSHOT" 2>&1; then
    if ! grep -qi "no crontab for" "$CRONTAB_SNAPSHOT"; then
        cat "$CRONTAB_SNAPSHOT" >&2
        rm -f "$CRONTAB_SNAPSHOT"
        echo "Failed to read current crontab" >&2
        exit 1
    fi
    CRONTAB_PRESENT=0
    rm -f "$CRONTAB_SNAPSHOT"
else
    mv "$CRONTAB_SNAPSHOT" "$BACKUP_FILE"
    CRONTAB_PRESENT=1
fi

if [[ "$CRONTAB_PRESENT" -eq 0 ]]; then
    echo "# No existing crontab" > "$BACKUP_FILE"
fi

restore_crontab() {
    rm -f "$CRONTAB_SNAPSHOT"
    echo
    echo "Restoring original crontab from $BACKUP_FILE"
    if [[ "$CRONTAB_PRESENT" -eq 1 ]]; then
        if [[ -s "$BACKUP_FILE" ]]; then
            crontab "$BACKUP_FILE"
        else
            crontab -r || true
        fi
    else
        crontab -r || true
    fi
}
trap restore_crontab EXIT

chmod 600 "$BACKUP_FILE" 2>/dev/null || true
echo "Backed up current crontab to $BACKUP_FILE"
echo "Installing one-minute test schedule for managed automation jobs..."
CRON_RUN_EVERY_MINUTE=1 "$INSTALL_SCRIPT"

SECONDS_TO_WAIT=$(( (60 - 10#$(date +%S)) + (RUN_MINUTES * 60) ))
if (( SECONDS_TO_WAIT < 70 )); then
    SECONDS_TO_WAIT=70
fi
echo "Waiting $SECONDS_TO_WAIT seconds for jobs to run..."
sleep "$SECONDS_TO_WAIT"
echo "Test window complete. Restoring original crontab."
