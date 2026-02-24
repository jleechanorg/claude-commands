#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_HOME="${CANONICAL_HOME:-}"

canonical_home() {
    local user candidate_home

    user="${SUDO_USER:-${LOGNAME:-${USER:-$(id -un 2>/dev/null || true)}}}"

    if [[ -n "$CANONICAL_HOME" ]]; then
        echo "$CANONICAL_HOME"
        return 0
    fi

    if [[ -n "$user" ]] && command -v dscl >/dev/null 2>&1; then
        candidate_home="$(dscl . -read "/Users/$user" NFSHomeDirectory 2>/dev/null | awk '/NFSHomeDirectory/ {print $2}' | tail -n1)"
        if [[ -n "$candidate_home" && -d "$candidate_home" ]]; then
            echo "$candidate_home"
            return 0
        fi
    fi

    if [[ -n "$user" ]] && command -v getent >/dev/null 2>&1; then
        candidate_home="$(getent passwd "$user" 2>/dev/null | awk -F: '{print $6}')"
        if [[ -n "$candidate_home" && -d "$candidate_home" ]]; then
            echo "$candidate_home"
            return 0
        fi
    fi

    echo "$HOME"
}

CANONICAL_HOME="$(canonical_home)"

resolve_jleechanorg_pr_monitor() {
    local candidate

    candidate="$(type -P jleechanorg-pr-monitor 2>/dev/null || true)"
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        echo "$candidate"
        return 0
    fi

    for candidate in \
        "$CANONICAL_HOME/.local/bin/jleechanorg-pr-monitor" \
        "/opt/homebrew/bin/jleechanorg-pr-monitor" \
        "/usr/local/bin/jleechanorg-pr-monitor" \
        "/usr/bin/jleechanorg-pr-monitor" \
        "/bin/jleechanorg-pr-monitor"; do
        if [[ -x "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done

    echo "jleechanorg-pr-monitor"
}

inject_resolved_monitor() {
    local line="$1"

    if [[ "$MONITOR_BINARY_PATH" == "jleechanorg-pr-monitor" ]]; then
        echo "$line"
        return 0
    fi

    echo "$line" | sed -E "s@(^|[[:space:]])\"?(jleechanorg-pr-monitor)\"?([[:space:]]|$)@\1$MONITOR_BINARY_PATH\3@g"
}

# Allow CRON_FILE to be overridden via environment variable
CRON_FILE="${CRON_FILE:-$SCRIPT_DIR/crontab.template}"
MONITOR_BINARY_PATH="$(resolve_jleechanorg_pr_monitor)"
if [[ "$MONITOR_BINARY_PATH" == "jleechanorg-pr-monitor" ]]; then
    echo "WARNING: could not resolve jleechanorg-pr-monitor to an absolute path; installed jobs will keep bare command name"
else
    echo "Resolved jleechanorg-pr-monitor to: $MONITOR_BINARY_PATH"
fi

BASHRC_PATH="${BASHRC_PATH:-$CANONICAL_HOME/.bashrc}"
CRON_BASH_ENV_PATH="${CRON_BASH_ENV_PATH:-$CANONICAL_HOME/.codex/cron_bash_env.sh}"
BACKUP_DIR="$CANONICAL_HOME/.cron_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_EVERY_MINUTE="${CRON_RUN_EVERY_MINUTE:-0}"
MANAGED_START="# === Automation entries (managed by install_cron_entries.sh) ==="
MANAGED_END="# === End automation entries ==="

expand_home_vars() {
    local value="$1"
    value="${value//\$HOME/$CANONICAL_HOME}"
    value="${value//\$\{HOME\}/$CANONICAL_HOME}"
    echo "$value"
}

ensure_cron_bash_env() {
    local target="$1"
    local target_dir

    target_dir="$(dirname "$target")"
    mkdir -p "$target_dir"

    cat > "$target" <<EOF
#!/bin/bash
# Managed by install_cron_entries.sh (non-interactive cron bootstrap)
if [ -f "$BASHRC_PATH" ]; then
    source "$BASHRC_PATH"
fi

if [ -f "\$HOME/.nvm/nvm.sh" ]; then
    # shellcheck disable=SC1091
    source "\$HOME/.nvm/nvm.sh"
fi
EOF
    chmod 600 "$target"
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
                n = split(token, path_parts, "/")
                if (n > 0 && path_parts[n] == "jleechanorg-pr-monitor") {
                    token = "jleechanorg-pr-monitor"
                }
                cmd = cmd (cmd == "" ? "" : OFS) token
            }
            if (cmd != "") {
                print schedule "|" cmd
            }
        }
    '
}

is_standard_cron_schedule() {
    local line="$1"
    local f1 f2 f3 f4 f5 _
    read -r f1 f2 f3 f4 f5 _ <<< "$line"

    [[ -z "$f1" || -z "$f2" || -z "$f3" || -z "$f4" || -z "$f5" ]] && return 1

    local token_re='^[0-9*/,-]+$'
    [[ "$f1" =~ $token_re ]] && [[ "$f2" =~ $token_re ]] && [[ "$f3" =~ $token_re ]] && [[ "$f4" =~ $token_re ]] && [[ "$f5" =~ $token_re ]] && return 0
    return 1
}

to_every_minute_schedule() {
    local line="$1"
    if [[ "$RUN_EVERY_MINUTE" == "1" ]]; then
        if is_standard_cron_schedule "$line"; then
            awk '{$1=$2=$3=$4=$5="*"; print}' <<< "$line"
            return
        fi
    fi
    echo "$line"
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
if [[ "$RUN_EVERY_MINUTE" == "1" ]]; then
    echo "Temporarily rewriting managed schedules to run every minute for test."
fi

TEMP_CRON=$(mktemp)
trap 'rm -f "$TEMP_CRON"' EXIT

# Build core command signatures from template jobs for safe duplicate removal.
# Signature excludes output redirection, so log-path-only variations are treated as duplicates.
TEMPLATE_CORE_SIGNATURES=$(while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^# ]] && continue
    [[ "$line" =~ ^PATH= ]] && continue
    expanded_line="$(expand_home_vars "$line")"
    cron_job_core_signature "$(inject_resolved_monitor "$expanded_line")"
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
            signature="$(cron_job_core_signature "$(inject_resolved_monitor "$(expand_home_vars "$line")")")"
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
        line_signature="$(cron_job_core_signature "$(inject_resolved_monitor "$(expand_home_vars "$line")")")"
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
            preserved_signature="$(cron_job_core_signature "$(inject_resolved_monitor "$(expand_home_vars "$preserved_line")")")"
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

# Ensure cron runs managed jobs under Bash and loads a dedicated bootstrap that sources bashrc
# and initializes NVM without relying on interactive-shell detection.
echo "SHELL=/bin/bash" >> "$TEMP_CRON"
ensure_cron_bash_env "$CRON_BASH_ENV_PATH"
echo "BASH_ENV=$CRON_BASH_ENV_PATH" >> "$TEMP_CRON"

# Always set managed PATH from template inside managed block.
template_path=$(grep -m1 '^PATH=' "$CRON_FILE" || true)
if [[ -n "$template_path" ]]; then
    echo "$(expand_home_vars "$template_path")" >> "$TEMP_CRON"
    echo "" >> "$TEMP_CRON"
fi

if [[ ! -f "$BASHRC_PATH" ]]; then
    echo "=== WARNING: BASHRC not found at $BASHRC_PATH ==="
    echo "Cron-managed commands will fall back to PATH from the template only."
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
    expanded_line="$(expand_home_vars "$line")"
    expanded_line="$(inject_resolved_monitor "$expanded_line")"
    echo "$(to_every_minute_schedule "$expanded_line")" >> "$TEMP_CRON"
    if [[ "$line" =~ \[CRON-JOB-ID:[[:space:]]*([a-z][a-z0-9-]*)\] ]]; then
        echo "Updated: ${BASH_REMATCH[1]}"
    fi
done < "$CRON_FILE"

echo "$MANAGED_END" >> "$TEMP_CRON"

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
