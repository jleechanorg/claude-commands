#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_SCRIPT="$SCRIPT_DIR/openclaw_mctrl_entry.sh"

JOB_NAMES=(
    "pr-monitor"
    "fix-comment"
    "comment-validation"
    "codex-api"
    "fixpr"
)

DRY_RUN=0
PLATFORM_OVERRIDE="${NATIVE_SCHEDULER_PLATFORM:-}"

usage() {
    cat <<'EOF'
Usage: ./install.sh [--dry-run] [--platform macos|linux]

Installs the five PR automation jobs as native scheduled services:
- macOS: launchd LaunchAgents
- Linux: systemd user timers/services

After native installation verifies successfully, matching OpenClaw cron jobs are
disabled by exact job name if the OpenClaw CLI is available.

Options:
  --dry-run            Render files and print actions without mutating schedulers
  --platform <value>   Override runtime detection with macos or linux
  -h, --help           Show this help text
EOF
}

log() {
    printf '%s\n' "$*"
}

warn() {
    printf 'WARNING: %s\n' "$*" >&2
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

xml_escape() {
    local value="$1"
    value="${value//&/&amp;}"
    value="${value//</&lt;}"
    value="${value//>/&gt;}"
    printf '%s' "$value"
}

systemd_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    printf '%s' "$value"
}

join_shell_quoted() {
    local out=""
    local arg
    for arg in "$@"; do
        if [[ -n "$out" ]]; then
            out+=" "
        fi
        out+="$(printf '%q' "$arg")"
    done
    printf '%s' "$out"
}

join_systemd_quoted() {
    local out=""
    local arg
    for arg in "$@"; do
        if [[ -n "$out" ]]; then
            out+=" "
        fi
        out+="\"$(systemd_escape "$arg")\""
    done
    printf '%s' "$out"
}

runtime_state_root() {
    local base_dir="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
    local uid
    uid="$(id -u)"
    base_dir="${base_dir%/}"
    printf '%s/${PROJECT_NAME:-your-project}-automation/uid-%s/mctrl/%s' "$base_dir" "$uid" "$1"
}

detect_platform() {
    if [[ -n "$PLATFORM_OVERRIDE" ]]; then
        case "$PLATFORM_OVERRIDE" in
            macos|linux)
                printf '%s' "$PLATFORM_OVERRIDE"
                return 0
                ;;
            *)
                die "Unsupported --platform value: $PLATFORM_OVERRIDE"
                ;;
        esac
    fi

    case "$(uname -s)" in
        Darwin)
            printf 'macos'
            ;;
        Linux)
            printf 'linux'
            ;;
        *)
            die "Unsupported platform: $(uname -s)"
            ;;
    esac
}

resolve_monitor_binary() {
    local override="${PR_MONITOR_BIN:-}"
    local candidate=""

    if [[ -n "$override" ]]; then
        [[ -x "$override" ]] || die "PR_MONITOR_BIN is set but not executable: $override"
        printf '%s' "$override"
        return 0
    fi

    candidate="$(command -v ${GITHUB_OWNER}-pr-monitor 2>/dev/null || true)"
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        printf '%s' "$candidate"
        return 0
    fi

    for candidate in \
        "$HOME/.local/bin/${GITHUB_OWNER}-pr-monitor" \
        "/opt/homebrew/bin/${GITHUB_OWNER}-pr-monitor" \
        "/usr/local/bin/${GITHUB_OWNER}-pr-monitor" \
        "/usr/bin/${GITHUB_OWNER}-pr-monitor" \
        "/bin/${GITHUB_OWNER}-pr-monitor"; do
        if [[ -x "$candidate" ]]; then
            printf '%s' "$candidate"
            return 0
        fi
    done

    die "Unable to resolve ${GITHUB_OWNER}-pr-monitor. Install it or set PR_MONITOR_BIN=/absolute/path/to/${GITHUB_OWNER}-pr-monitor"
}

set_job_args() {
    local job="$1"
    case "$job" in
        pr-monitor)
            JOB_ARGS=("$MONITOR_BINARY" "--max-prs" "10")
            ;;
        fix-comment)
            JOB_ARGS=("$MONITOR_BINARY" "--fix-comment" "--cli-agent" "minimax" "--max-prs" "3")
            ;;
        comment-validation)
            JOB_ARGS=("$MONITOR_BINARY" "--comment-validation" "--max-prs" "10")
            ;;
        codex-api)
            JOB_ARGS=("$MONITOR_BINARY" "--codex-api" "--codex-apply-and-push" "--codex-task-limit" "10")
            ;;
        fixpr)
            JOB_ARGS=("$MONITOR_BINARY" "--fixpr" "--max-prs" "10" "--cli-agent" "minimax")
            ;;
        *)
            die "Unknown job: $job"
            ;;
    esac
}

set_wrapper_args() {
    local job="$1"
    local exec_command

    set_job_args "$job"
    exec_command="$(join_shell_quoted "${JOB_ARGS[@]}")"
    WRAPPER_ARGS=(
        "$WRAPPER_SCRIPT"
        "--job-id" "$(job_label "$job")"
        "--job-type" "$job"
        "--repo" "${GITHUB_OWNER}/${PROJECT_NAME:-your-project}.com"
        "--exec" "$exec_command"
    )
}

job_label() {
    printf 'ai.${PROJECT_NAME:-your-project}.pr-automation.%s' "$1"
}

job_service_name() {
    printf '${PROJECT_NAME:-your-project}-pr-automation-%s' "$1"
}

job_log_stem() {
    printf '%s' "$1"
}

job_schedule_note() {
    case "$1" in
        pr-monitor)
            printf '0 */2 * * * with bounded 0-300s stagger'
            ;;
        fix-comment)
            printf '45 * * * *'
            ;;
        comment-validation)
            printf '*/30 * * * *'
            ;;
        codex-api)
            printf '30 * * * *'
            ;;
        fixpr)
            printf '*/30 * * * *'
            ;;
        *)
            die "Unknown job: $1"
            ;;
    esac
}

render_launchd_start_calendar_interval() {
    local job="$1"
    case "$job" in
        pr-monitor)
            cat <<'EOF'
    <array>
      <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>4</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>14</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>16</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>20</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Hour</key>
        <integer>22</integer>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
    </array>
EOF
            ;;
        fix-comment)
            cat <<'EOF'
    <dict>
      <key>Minute</key>
      <integer>45</integer>
    </dict>
EOF
            ;;
        comment-validation|fixpr)
            cat <<'EOF'
    <array>
      <dict>
        <key>Minute</key>
        <integer>0</integer>
      </dict>
      <dict>
        <key>Minute</key>
        <integer>30</integer>
      </dict>
    </array>
EOF
            ;;
        codex-api)
            cat <<'EOF'
    <dict>
      <key>Minute</key>
      <integer>30</integer>
    </dict>
EOF
            ;;
        *)
            die "Unknown launchd schedule job: $job"
            ;;
    esac
}

render_launchd_program_arguments() {
    local job="$1"
    local arg

    set_wrapper_args "$job"

    cat <<'EOF'
    <array>
EOF
    for arg in "${WRAPPER_ARGS[@]}"; do
        printf '      <string>%s</string>\n' "$(xml_escape "$arg")"
    done
    cat <<'EOF'
    </array>
EOF
}

render_launchd_environment_variables() {
    local job="$1"
    local evidence_root lock_file metrics_file health_file
    evidence_root="$(runtime_state_root "$job")"
    lock_file="$evidence_root/.mctrl.lock"
    metrics_file="$evidence_root/metrics.json"
    health_file="$evidence_root/health.json"

    cat <<EOF
    <dict>
      <key>PATH</key>
      <string>$(xml_escape "$PATH")</string>
      <key>MCTRL_TRIGGER_SOURCE</key>
      <string>catch_up</string>
      <key>MCTRL_WORKFLOW_LANE</key>
      <string>$(xml_escape "$job")</string>
      <key>MCTRL_EVIDENCE_ROOT</key>
      <string>$(xml_escape "$evidence_root")</string>
      <key>MCTRL_LOCK_FILE</key>
      <string>$(xml_escape "$lock_file")</string>
      <key>MCTRL_METRICS_FILE</key>
      <string>$(xml_escape "$metrics_file")</string>
      <key>MCTRL_HEALTH_FILE</key>
      <string>$(xml_escape "$health_file")</string>
EOF
    if [[ "$job" == "pr-monitor" ]]; then
        cat <<'EOF'
      <key>MCTRL_PRE_EXEC_SLEEP_MAX_SECONDS</key>
      <string>300</string>
EOF
    fi
    cat <<'EOF'
    </dict>
EOF
}

render_launchd_plist() {
    local job="$1"
    local label out_log err_log

    label="$(job_label "$job")"
    out_log="$LOG_DIR/$(job_log_stem "$job").out.log"
    err_log="$LOG_DIR/$(job_log_stem "$job").err.log"

    cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>$(xml_escape "$label")</string>
    <key>ProgramArguments</key>
$(render_launchd_program_arguments "$job")
    <key>RunAtLoad</key>
    <true/>
    <key>StartCalendarInterval</key>
$(render_launchd_start_calendar_interval "$job")
    <key>WorkingDirectory</key>
    <string>$(xml_escape "$SCRIPT_DIR")</string>
    <key>StandardOutPath</key>
    <string>$(xml_escape "$out_log")</string>
    <key>StandardErrorPath</key>
    <string>$(xml_escape "$err_log")</string>
    <key>EnvironmentVariables</key>
$(render_launchd_environment_variables "$job")
    <key>ProcessType</key>
    <string>Background</string>
  </dict>
</plist>
EOF
}

render_systemd_exec_start() {
    local job="$1"

    set_wrapper_args "$job"
    join_systemd_quoted "${WRAPPER_ARGS[@]}"
}

render_systemd_service() {
    local job="$1"
    local exec_start
    local escaped_workdir
    local escaped_path
    local evidence_root
    local lock_file
    local metrics_file
    local health_file
    exec_start="$(render_systemd_exec_start "$job")"
    escaped_workdir="$(systemd_escape "$SCRIPT_DIR")"
    escaped_path="$(systemd_escape "$PATH")"
    evidence_root="$(systemd_escape "$(runtime_state_root "$job")")"
    lock_file="$(systemd_escape "$(runtime_state_root "$job")/.mctrl.lock")"
    metrics_file="$(systemd_escape "$(runtime_state_root "$job")/metrics.json")"
    health_file="$(systemd_escape "$(runtime_state_root "$job")/health.json")"

    cat <<EOF
[Unit]
Description=WorldArchitect PR automation: $job
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory="$escaped_workdir"
Environment="PATH=$escaped_path"
Environment="MCTRL_TRIGGER_SOURCE=catch_up"
Environment="MCTRL_WORKFLOW_LANE=$job"
Environment="MCTRL_EVIDENCE_ROOT=$evidence_root"
Environment="MCTRL_LOCK_FILE=$lock_file"
Environment="MCTRL_METRICS_FILE=$metrics_file"
Environment="MCTRL_HEALTH_FILE=$health_file"
EOF
    cat <<EOF
ExecStart=$exec_start
EOF
}

render_systemd_timer() {
    local job="$1"
    cat <<EOF
[Unit]
Description=WorldArchitect PR automation timer: $job

[Timer]
Persistent=true
Unit=$(job_service_name "$job").service
EOF
    case "$job" in
        pr-monitor)
            cat <<'EOF'
OnCalendar=*-*-* 0/2:00:00
RandomizedDelaySec=300
EOF
            ;;
        fix-comment)
            cat <<'EOF'
OnCalendar=*-*-* *:45:00
EOF
            ;;
        comment-validation|fixpr)
            cat <<'EOF'
OnCalendar=*-*-* *:00:00
OnCalendar=*-*-* *:30:00
EOF
            ;;
        codex-api)
            cat <<'EOF'
OnCalendar=*-*-* *:30:00
EOF
            ;;
        *)
            die "Unknown systemd timer job: $job"
            ;;
    esac
    cat <<'EOF'

[Install]
WantedBy=timers.target
EOF
}

install_if_changed() {
    local target="$1"
    local tmp_file

    tmp_file="$(mktemp)"
    cat >"$tmp_file"
    mkdir -p "$(dirname "$target")"

    if [[ -f "$target" ]] && cmp -s "$tmp_file" "$target"; then
        rm -f "$tmp_file"
        log "Unchanged: $target"
        return 0
    fi

    if [[ "$DRY_RUN" -eq 1 ]]; then
        rm -f "$tmp_file"
        log "[dry-run] would update: $target"
        return 0
    fi

    mv "$tmp_file" "$target"
    log "Updated: $target"
}

run_or_echo() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '[dry-run] %s\n' "$*"
        return 0
    fi

    "$@"
}

install_launchd_jobs() {
    local uid label plist_path job

    mkdir -p "$LAUNCHD_DIR" "$LOG_DIR"
    uid="$(id -u)"

    for job in "${JOB_NAMES[@]}"; do
        plist_path="$LAUNCHD_DIR/$(job_label "$job").plist"
        render_launchd_plist "$job" | install_if_changed "$plist_path"

        label="$(job_label "$job")"
        run_or_echo launchctl bootout "gui/$uid" "$plist_path" >/dev/null 2>&1 || true
        run_or_echo launchctl bootstrap "gui/$uid" "$plist_path"
        run_or_echo launchctl enable "gui/$uid/$label"
        run_or_echo launchctl kickstart -k "gui/$uid/$label"
        if [[ "$DRY_RUN" -eq 0 ]]; then
            launchctl print "gui/$uid/$label" >/dev/null
        fi
    done
}

systemctl_cmd() {
    if [[ "${SYSTEMD_SCOPE:-user}" == "system" ]]; then
        printf 'systemctl'
        return 0
    fi
    printf 'systemctl --user'
}

install_systemd_jobs() {
    local job service_path timer_path systemctl_base
    mkdir -p "$SYSTEMD_DIR" "$LOG_DIR"

    if ! command -v systemctl >/dev/null 2>&1; then
        die "systemctl not found; install systemd or rerun on macOS"
    fi

    systemctl_base="$(systemctl_cmd)"

    for job in "${JOB_NAMES[@]}"; do
        service_path="$SYSTEMD_DIR/$(job_service_name "$job").service"
        timer_path="$SYSTEMD_DIR/$(job_service_name "$job").timer"
        render_systemd_service "$job" | install_if_changed "$service_path"
        render_systemd_timer "$job" | install_if_changed "$timer_path"
    done

    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '[dry-run] %s daemon-reload\n' "$systemctl_base"
        for job in "${JOB_NAMES[@]}"; do
            printf '[dry-run] %s enable --now %s.timer\n' "$systemctl_base" "$(job_service_name "$job")"
            printf '[dry-run] %s start %s.service\n' "$systemctl_base" "$(job_service_name "$job")"
            printf '[dry-run] %s is-enabled %s.timer\n' "$systemctl_base" "$(job_service_name "$job")"
            printf '[dry-run] %s is-active %s.timer\n' "$systemctl_base" "$(job_service_name "$job")"
        done
        return 0
    fi

    if [[ "${SYSTEMD_SCOPE:-user}" == "system" ]]; then
        systemctl daemon-reload
        for job in "${JOB_NAMES[@]}"; do
            systemctl enable --now "$(job_service_name "$job").timer"
            systemctl start "$(job_service_name "$job").service"
            systemctl is-enabled "$(job_service_name "$job").timer" >/dev/null
            systemctl is-active "$(job_service_name "$job").timer" >/dev/null
        done
        return 0
    fi

    systemctl --user daemon-reload
    for job in "${JOB_NAMES[@]}"; do
        systemctl --user enable --now "$(job_service_name "$job").timer"
        systemctl --user start "$(job_service_name "$job").service"
        systemctl --user is-enabled "$(job_service_name "$job").timer" >/dev/null
        systemctl --user is-active "$(job_service_name "$job").timer" >/dev/null
    done
}

disable_matching_openclaw_jobs() {
    local openclaw_bin openclaw_json disable_failures output

    openclaw_bin="${OPENCLAW_BIN:-$(command -v openclaw 2>/dev/null || true)}"
    if [[ -z "$openclaw_bin" ]]; then
        warn "openclaw CLI not found; leaving OpenClaw cron jobs unchanged"
        return 0
    fi

    if ! openclaw_json="$("$openclaw_bin" cron list --all --json 2>/dev/null)"; then
        warn "openclaw cron list failed; native schedulers were installed, but OpenClaw cron jobs were left unchanged"
        return 0
    fi

    output="$(
        OPENCLAW_JSON="$openclaw_json" python3 -c '
import json
import os

targets = {"pr-monitor", "fix-comment", "comment-validation", "codex-api", "fixpr"}
data = json.loads(os.environ["OPENCLAW_JSON"])
for job in data.get("jobs", []):
    name = job.get("name")
    if name in targets:
        enabled = "true" if job.get("enabled") else "false"
        print("{}\t{}\t{}".format(name, job.get("id", ""), enabled))
'
    )"

    disable_failures=0
    while IFS=$'\t' read -r name job_id enabled; do
        [[ -n "${name:-}" ]] || continue
        if [[ -z "$job_id" ]]; then
            warn "OpenClaw job '$name' has no id; leaving it unchanged"
            continue
        fi
        if [[ "$enabled" != "true" ]]; then
            log "OpenClaw job already disabled: $name ($job_id)"
            continue
        fi
        log "Disabling OpenClaw cron job: $name ($job_id)"
        if [[ "$DRY_RUN" -eq 1 ]]; then
            printf '[dry-run] %s cron disable %s\n' "$openclaw_bin" "$job_id"
            continue
        fi
        if ! "$openclaw_bin" cron disable "$job_id"; then
            warn "Failed to disable OpenClaw cron job '$name' ($job_id)"
            disable_failures=1
        fi
    done <<<"$output"

    if [[ "$disable_failures" -ne 0 ]]; then
        die "Native schedulers were installed, but one or more OpenClaw cron jobs could not be disabled"
    fi
}

print_summary() {
    local job

    log ""
    log "Installed native scheduler definitions for:"
    for job in "${JOB_NAMES[@]}"; do
        set_job_args "$job"
        log "  - $job: $(job_schedule_note "$job")"
        log "    Command: $(join_shell_quoted "${JOB_ARGS[@]}")"
    done
    log ""
    log "Notes:"
    log "  - pr-monitor uses a bounded random sleep of up to 300 seconds before execution."
    log "  - This approximates the OpenClaw scheduler stagger while preserving the two-hour cadence."
    log "  - Re-running ./install.sh updates the same native definitions in place."
    log "  - To uninstall, disable/remove the generated units or plists and optionally re-enable the same OpenClaw cron jobs."
}

print_validation_commands() {
    local platform="$1"
    local job uid

    log ""
    log "Validation commands for this machine:"
    if [[ "$platform" == "macos" ]]; then
        uid="$(id -u)"
        for job in "${JOB_NAMES[@]}"; do
            log "  launchctl print gui/$uid/$(job_label "$job")"
        done
        log "  ls -1 \"$LAUNCHD_DIR\""
    else
        if [[ "${SYSTEMD_SCOPE:-user}" == "system" ]]; then
            for job in "${JOB_NAMES[@]}"; do
                log "  systemctl status $(job_service_name "$job").service"
                log "  systemctl status $(job_service_name "$job").timer"
            done
            log "  systemctl list-timers | grep ${PROJECT_NAME:-your-project}-pr-automation"
        else
            for job in "${JOB_NAMES[@]}"; do
                log "  systemctl --user status $(job_service_name "$job").service"
                log "  systemctl --user status $(job_service_name "$job").timer"
            done
            log "  systemctl --user list-timers | grep ${PROJECT_NAME:-your-project}-pr-automation"
        fi
    fi
    log "  openclaw cron list --all --json"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=1
                ;;
            --platform)
                shift
                [[ $# -gt 0 ]] || die "--platform requires a value"
                PLATFORM_OVERRIDE="$1"
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                die "Unknown argument: $1"
                ;;
        esac
        shift
    done
}

parse_args "$@"

PLATFORM="$(detect_platform)"
MONITOR_BINARY="$(resolve_monitor_binary)"
if [[ "$PLATFORM" == "linux" ]]; then
    DEFAULT_LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/${PROJECT_NAME:-your-project}-automation"
else
    DEFAULT_LOG_DIR="$HOME/Library/Logs/${PROJECT_NAME:-your-project}-automation"
fi
LOG_DIR="${AUTOMATION_LOG_DIR:-$DEFAULT_LOG_DIR}"
LAUNCHD_DIR="${LAUNCHD_DIR:-$HOME/Library/LaunchAgents}"
SYSTEMD_DIR="${SYSTEMD_DIR:-$HOME/.config/systemd/user}"

log "Installing native PR automation jobs for platform: $PLATFORM"
log "Resolved monitor binary: $MONITOR_BINARY"
log "Using log directory: $LOG_DIR"
if [[ "$DRY_RUN" -eq 1 ]]; then
    log "Dry run enabled: scheduler commands and OpenClaw changes will be printed but not executed"
fi

case "$PLATFORM" in
    macos)
        install_launchd_jobs
        ;;
    linux)
        install_systemd_jobs
        ;;
    *)
        die "Unsupported platform: $PLATFORM"
        ;;
esac

disable_matching_openclaw_jobs
print_summary
print_validation_commands "$PLATFORM"
