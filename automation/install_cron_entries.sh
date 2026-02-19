#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Allow CRON_FILE to be overridden via environment variable
CRON_FILE="${CRON_FILE:-$SCRIPT_DIR/crontab.template}"
BACKUP_DIR="$HOME/.cron_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MANAGED_START="# === Automation entries (managed by install_cron_entries.sh) ==="
MANAGED_END="# === End automation entries ==="

expand_home_vars() {
    local value="$1"
    value="${value//\$HOME/$HOME}"
    value="${value//\$\{HOME\}/$HOME}"
    echo "$value"
}

cron_job_core_signature() {
    local cron_line="$1"
    echo "$cron_line" | awk '
        NF >= 6 {
            schedule = $1 OFS $2 OFS $3 OFS $4 OFS $5
            cmd = ""
            for (i = 6; i <= NF; i++) {
                token = $i
                if (token ~ /^(>|>>|1>|1>>|2>|2>>|&>|&>>|2>&1|1>&2)$/) {
                    break
                }
                gsub(/^"/, "", token)
                gsub(/"$/, "", token)
                cmd = cmd (cmd == "" ? "" : OFS) token
            }
            if (cmd != "") {
                print schedule "|" cmd
            }
        }
    '
}

if ! command -v crontab >/dev/null 2>&1; then
    echo "crontab command not found; install cron before running this script" >&2
    exit 1
fi

if [[ ! -f "$CRON_FILE" ]]; then
    echo "Cron template not found at $CRON_FILE" >&2
    exit 1
fi

# Backup existing crontab before making changes
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/crontab_$TIMESTAMP.backup"
(
    umask 077
    crontab -l > "$BACKUP_FILE" 2>/dev/null || true
)
if [[ -f "$BACKUP_FILE" ]]; then
    chmod 600 "$BACKUP_FILE" 2>/dev/null || true
fi
echo "Backed up current crontab to $BACKUP_FILE"

echo "=== Installing automation cron entries ==="

TEMP_CRON=$(mktemp)
trap 'rm -f "$TEMP_CRON"' EXIT

# Build core command signatures from template jobs for safe duplicate removal.
# Signature excludes output redirection, so log-path-only variations are treated as duplicates.
TEMPLATE_CORE_SIGNATURES=$(while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^# ]] && continue
    [[ "$line" =~ ^PATH= ]] && continue
    expanded_line="$(expand_home_vars "$line")"
    cron_job_core_signature "$expanded_line"
done < "$CRON_FILE")

# Get existing crontab - preserve ALL entries except automation ones
in_managed_block=0
found_start_marker=false
# Track content after MANAGED_START in case block is unclosed (to preserve user entries).
# Collect inside-block line signatures so we can safely skip duplicates when preserving unclosed content.
unclosed_block_content=""
unclosed_block_signatures=""
{
    while IFS= read -r line; do
        # Preserve empty lines from existing crontab
        if [[ -z "${line//[[:space:]]/}" ]]; then
            echo ""
            continue
        fi

        # Remove old managed block contents entirely.
        if [[ "$line" == "$MANAGED_START" ]]; then
            in_managed_block=1
            found_start_marker=true
            continue
        fi
        if [[ "$line" == "$MANAGED_END" ]]; then
            in_managed_block=0
            # Only output preserved entries if this is a truly unclosed block (found_start_marker was set but we never properly closed)
            # The in_unclosed_block buffer is only for safety preservation, not for normal operation
            continue
        fi
        if [[ "$in_managed_block" -eq 1 ]]; then
            # Collect lines in case block is unclosed - these could be user entries
            unclosed_block_content+="$line"$'\n'
            signature="$(cron_job_core_signature "$(expand_home_vars "$line")")"
            if [[ -n "$signature" ]]; then
                unclosed_block_signatures+="$signature"$'\n'
            fi
            continue
        fi

        # Remove only entries marked with CRON-JOB-ID (these are managed entries)
        if [[ "$line" =~ \[CRON-JOB-ID:[[:space:]]*([a-z][a-z0-9-]*)\] ]]; then
            continue
        fi
        # Safely remove exact template-equivalent legacy lines.
        # This avoids duplicates while preserving custom variants outside managed block.
        line_signature="$(cron_job_core_signature "$(expand_home_vars "$line")")"
        if [[ -n "$line_signature" ]] && echo "$TEMPLATE_CORE_SIGNATURES" | grep -Fxq "$line_signature"; then
            continue
        fi

        # Keep everything else (env vars, PATH, comments, custom entries)
        echo "$line"
    done < <(crontab -l 2>/dev/null || true)

    # Safety: if MANAGED_START was found but no MANAGED_END, preserve user entries after it
    if [[ "$found_start_marker" == "true" ]] && [[ "$in_managed_block" -eq 1 ]]; then
        echo "WARNING: Unclosed managed block detected in existing crontab, preserving user entries" >&2
        # Output preserved user entries that were after MANAGED_START, excluding exact template duplicates.
        while IFS= read -r preserved_line || [[ -n "$preserved_line" ]]; do
            if [[ -z "${preserved_line//[[:space:]]/}" ]]; then
                echo ""
                continue
            fi
            preserved_signature="$(cron_job_core_signature "$(expand_home_vars "$preserved_line")")"
            if [[ -n "$preserved_signature" ]] && echo "$TEMPLATE_CORE_SIGNATURES" | grep -Fxq "$preserved_signature"; then
                continue
            fi
            echo "$preserved_line"
        done <<<"$unclosed_block_content"
    fi
} > "$TEMP_CRON"

# Add blank line separator
echo "" >> "$TEMP_CRON"

# Add automation entries from template (with job IDs for future updates)
echo "$MANAGED_START" >> "$TEMP_CRON"

# Always set managed PATH from template inside managed block.
template_path=$(grep -m1 '^PATH=' "$CRON_FILE" || true)
if [[ -n "$template_path" ]]; then
    echo "$(expand_home_vars "$template_path")" >> "$TEMP_CRON"
    echo "" >> "$TEMP_CRON"
fi

while IFS= read -r line || [[ -n "$line" ]]; do
    # Preserve empty lines from template
    if [[ -z "${line//[[:space:]]/}" ]]; then
        echo "" >> "$TEMP_CRON"
        continue
    fi

    # PATH is installed once above.
    [[ "$line" =~ ^PATH= ]] && continue

    # Preserve comments and entries from template to keep metadata in crontab.
    echo "$line" >> "$TEMP_CRON"
    if [[ "$line" =~ \[CRON-JOB-ID:[[:space:]]*([a-z][a-z0-9-]*)\] ]]; then
        echo "Updated: ${BASH_REMATCH[1]}"
    fi
done < "$CRON_FILE"

echo "$MANAGED_END" >> "$TEMP_CRON"

# Install wrapper script to ~/.local/bin if it exists in the repo
WRAPPER_SRC="$SCRIPT_DIR/jleechanorg-pr-monitor-wrapper.sh"
WRAPPER_DST="$HOME/.local/bin/jleechanorg-pr-monitor-wrapper.sh"
if [ -f "$WRAPPER_SRC" ]; then
    mkdir -p "$HOME/.local/bin"
    cp "$WRAPPER_SRC" "$WRAPPER_DST"
    chmod +x "$WRAPPER_DST"
    echo "=== Installed wrapper script to $WRAPPER_DST ==="
fi

# Warn if .automation_env is missing
if [ ! -f "$HOME/.automation_env" ]; then
    echo "=== WARNING: ~/.automation_env not found ==="
    echo "Create ~/.automation_env with MINIMAX_API_KEY and ANTHROPIC_BASE_URL for automation to work"
    echo "Example:"
    echo '  echo "export MINIMAX_API_KEY=\$MINIMAX_API_KEY" > ~/.automation_env'
    echo '  echo "export ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic" >> ~/.automation_env'
    echo ""
fi

# Apply the crontab
crontab "$TEMP_CRON"
echo ""
echo "=== Crontab updated successfully ==="
echo ""
echo "Managed automation block (sensitive env assignments redacted):"
crontab -l 2>/dev/null | awk -v managed_start="$MANAGED_START" -v managed_end="$MANAGED_END" '
    $0 == managed_start { in_managed_block=1; print; next }
    $0 == managed_end { print; in_managed_block=0; next }
    in_managed_block {
        if ($0 ~ /^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=/) {
            print "[redacted env assignment]"
            next
        }
        print
    }
'
