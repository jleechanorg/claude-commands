#!/bin/bash
set -euo pipefail

REPO_AUTOMATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_AUTOMATION_DIR/install.sh"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="$3"
    if [[ "$haystack" != *"$needle"* ]]; then
        echo "FAIL: $message" >&2
        echo "Expected to find: $needle" >&2
        exit 1
    fi
}

assert_file_contains() {
    local file="$1"
    local needle="$2"
    local message="$3"
    if ! grep -Fq -- "$needle" "$file"; then
        echo "FAIL: $message" >&2
        echo "Expected to find: $needle" >&2
        echo "In file: $file" >&2
        exit 1
    fi
}

assert_file_not_contains() {
    local file="$1"
    local needle="$2"
    local message="$3"
    if [[ ! -f "$file" ]]; then
        echo "FAIL: $message" >&2
        echo "Expected file to exist: $file" >&2
        exit 1
    fi
    if grep -Fq -- "$needle" "$file"; then
        echo "FAIL: $message" >&2
        echo "Did not expect to find: $needle" >&2
        echo "In file: $file" >&2
        exit 1
    fi
}

setup_fake_environment() {
    local env_root="$1"
    mkdir -p "$env_root/bin" "$env_root/home"

    cat >"$env_root/bin/github-owner-pr-monitor" <<'EOF'
#!/bin/bash
exit 0
EOF
    chmod +x "$env_root/bin/github-owner-pr-monitor"

    cat >"$env_root/bin/openclaw" <<'EOF'
#!/bin/bash
set -euo pipefail

state_file="${OPENCLAW_STATE_FILE:?}"
log_file="${OPENCLAW_CALL_LOG:?}"
echo "openclaw $*" >>"$log_file"

disabled_ids=""
if [[ -f "$state_file" ]]; then
    disabled_ids="$(cat "$state_file")"
fi

is_disabled() {
    local id="$1"
    grep -Fqx "$id" "$state_file" 2>/dev/null
}

if [[ "${1:-}" == "cron" && "${2:-}" == "list" && "${3:-}" == "--all" && "${4:-}" == "--json" ]]; then
    python3 - <<'PY'
import json
import os

state_path = os.environ["OPENCLAW_STATE_FILE"]
disabled = set()
if os.path.exists(state_path):
    with open(state_path, "r", encoding="utf-8") as fh:
        disabled = {line.strip() for line in fh if line.strip()}

jobs = [
    {"id": "id-pr-monitor", "name": "pr-monitor"},
    {"id": "id-fix-comment", "name": "fix-comment"},
    {"id": "id-comment-validation", "name": "comment-validation"},
    {"id": "id-codex-api", "name": "codex-api"},
    {"id": "id-fixpr", "name": "fixpr"},
    {"id": "id-keepalive", "name": "ai-orch-session-keepalive"},
    {"id": "id-slack", "name": "Daily Slack Check-in 9AM"},
]

payload = {
    "jobs": [
        {
            "id": job["id"],
            "name": job["name"],
            "enabled": job["id"] not in disabled,
        }
        for job in jobs
    ]
}
print(json.dumps(payload))
PY
    exit 0
fi

if [[ "${1:-}" == "cron" && "${2:-}" == "disable" && -n "${3:-}" ]]; then
    printf '%s\n' "$3" >>"$state_file"
    exit 0
fi

echo "unsupported openclaw invocation: $*" >&2
exit 1
EOF
    chmod +x "$env_root/bin/openclaw"
}

setup_fake_launchctl() {
    local env_root="$1"
    cat >"$env_root/bin/launchctl" <<'EOF'
#!/bin/bash
set -euo pipefail
echo "launchctl $*" >>"${LAUNCHCTL_CALL_LOG:?}"
exit 0
EOF
    chmod +x "$env_root/bin/launchctl"
}

setup_fake_systemctl() {
    local env_root="$1"
    cat >"$env_root/bin/systemctl" <<'EOF'
#!/bin/bash
set -euo pipefail

echo "systemctl $*" >>"${SYSTEMCTL_CALL_LOG:?}"

if [[ "${1:-}" == "--user" ]]; then
    shift
fi

case "${1:-}" in
    daemon-reload|enable|start)
        exit 0
        ;;
    is-enabled)
        echo "enabled"
        exit 0
        ;;
    is-active)
        echo "active"
        exit 0
        ;;
    *)
        echo "unsupported systemctl invocation: $*" >&2
        exit 1
        ;;
esac
EOF
    chmod +x "$env_root/bin/systemctl"
}

run_macos_install_test() {
    local env_root="$TEST_ROOT/macos"
    local launchd_dir="$env_root/home/Library/LaunchAgents"
    local log_dir="$env_root/home/Library/Logs/worldarchitect-automation"
    local legacy_pr_monitor_plist="$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist"
    local runtime_tmp="$env_root/runtime-tmp"
    local expected_runtime_root="$runtime_tmp/worldarchitect-automation/uid-$(id -u)/mctrl/pr-monitor"

    setup_fake_environment "$env_root"
    setup_fake_launchctl "$env_root"

    mkdir -p "$launchd_dir"
    cat >"$legacy_pr_monitor_plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>ai.worldarchitect.pr-automation.pr-monitor</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>-lc</string>
      <string>sleep \$(( RANDOM % 301 )); exec /opt/homebrew/bin/github-owner-pr-monitor --max-prs 10</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${HOME}/projects/your-project.com/automation</string>
  </dict>
</plist>
EOF

    export HOME="$env_root/home"
    export PATH="$env_root/bin:/usr/bin:/bin"
    export OPENCLAW_STATE_FILE="$env_root/openclaw_state.txt"
    export OPENCLAW_CALL_LOG="$env_root/openclaw_calls.log"
    export LAUNCHCTL_CALL_LOG="$env_root/launchctl_calls.log"
    export NATIVE_SCHEDULER_PLATFORM="macos"
    export LAUNCHD_DIR="$launchd_dir"
    export AUTOMATION_LOG_DIR="$log_dir"
    export TMPDIR="$runtime_tmp"

    local output
    output="$("$INSTALL_SCRIPT")"
    output+=$'\n'"$("$INSTALL_SCRIPT")"

    assert_contains "$output" "Installing native PR automation jobs for platform: macos" "macOS install output should mention platform"
    assert_file_not_contains "$legacy_pr_monitor_plist" "<string>/bin/bash</string>" "legacy direct-binary launchd program should be removed during migration"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" '<key>MCTRL_PRE_EXEC_SLEEP_MAX_SECONDS</key>' "pr-monitor plist should configure bounded stagger"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" '<string>300</string>' "pr-monitor plist should set 300 second bounded stagger"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" '<key>Hour</key>' "pr-monitor plist should declare explicit two-hour launchd hours"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" '<integer>22</integer>' "pr-monitor plist should include the final two-hour slot"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" "${REPO_AUTOMATION_DIR}/openclaw_mctrl_entry.sh" "pr-monitor plist should invoke mctrl wrapper"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" '<key>MCTRL_TRIGGER_SOURCE</key>' "launchd plist should set trigger source env"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" '<string>catch_up</string>' "launchd plist should mark trigger source as catch_up"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" '<string>--exec</string>' "launchd plist should pass wrapper exec mode"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" "$env_root/bin/github-owner-pr-monitor --max-prs 10" "pr-monitor plist should retain exact monitor command"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" "<string>${expected_runtime_root}</string>" "launchd plist should write pr-monitor runtime evidence under the per-user temp root"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.pr-monitor.plist" "<string>${expected_runtime_root}/.mctrl.lock</string>" "launchd plist should write lock file under the per-user temp root"
    assert_file_contains "$LAUNCHCTL_CALL_LOG" "launchctl bootout gui/" "macOS install should boot out the existing launchd job before migration"
    assert_file_contains "$LAUNCHCTL_CALL_LOG" "launchctl bootstrap gui/" "macOS install should bootstrap the migrated launchd job"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.fix-comment.plist" "<string>--job-type</string>" "fix-comment plist should set wrapper job type"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.fix-comment.plist" "<string>fix-comment</string>" "fix-comment plist should include job type"
    assert_file_contains "$launchd_dir/ai.worldarchitect.pr-automation.fix-comment.plist" "<integer>45</integer>" "fix-comment plist should keep :45 schedule"

    local disable_count
    disable_count="$(grep -c 'openclaw cron disable' "$OPENCLAW_CALL_LOG" || true)"
    if [[ "$disable_count" -ne 5 ]]; then
        echo "FAIL: expected exactly 5 OpenClaw disables across two macOS installs, got $disable_count" >&2
        exit 1
    fi

    if grep -Fq 'id-keepalive' "$OPENCLAW_CALL_LOG" || grep -Fq 'id-slack' "$OPENCLAW_CALL_LOG"; then
        echo "FAIL: non-target OpenClaw jobs were disabled during macOS install" >&2
        exit 1
    fi
}

run_linux_install_test() {
    local env_root="$TEST_ROOT/linux"
    local systemd_dir="$env_root/home/.config/systemd/user"
    local xdg_state_home="$env_root/home/.local/state"
    local expected_log_dir="$xdg_state_home/worldarchitect-automation"
    local runtime_tmp="$env_root/runtime-tmp"
    local expected_runtime_root="$runtime_tmp/worldarchitect-automation/uid-$(id -u)/mctrl/codex-api"

    setup_fake_environment "$env_root"
    setup_fake_systemctl "$env_root"

    export HOME="$env_root/home"
    export PATH="$env_root/bin:$env_root/home/Path With Spaces:/usr/bin:/bin"
    export OPENCLAW_STATE_FILE="$env_root/openclaw_state.txt"
    export OPENCLAW_CALL_LOG="$env_root/openclaw_calls.log"
    export SYSTEMCTL_CALL_LOG="$env_root/systemctl_calls.log"
    export NATIVE_SCHEDULER_PLATFORM="linux"
    export SYSTEMD_DIR="$systemd_dir"
    export XDG_STATE_HOME="$xdg_state_home"
    export TMPDIR="$runtime_tmp"
    unset AUTOMATION_LOG_DIR

    local output
    output="$("$INSTALL_SCRIPT")"

    assert_contains "$output" "Installing native PR automation jobs for platform: linux" "Linux install output should mention platform"
    assert_contains "$output" "$expected_log_dir" "Linux install output should use XDG state log directory"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-pr-monitor.timer" "OnCalendar=*-*-* 0/2:00:00" "pr-monitor timer should include two-hour cadence"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-pr-monitor.timer" "RandomizedDelaySec=300" "pr-monitor timer should include bounded randomized delay"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-fix-comment.timer" "OnCalendar=*-*-* *:45:00" "fix-comment timer should keep :45 schedule"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-codex-api.service" "${REPO_AUTOMATION_DIR}/openclaw_mctrl_entry.sh" "systemd service should invoke mctrl wrapper"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-codex-api.service" "Environment=\"MCTRL_TRIGGER_SOURCE=catch_up\"" "systemd service should mark trigger source as catch_up"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-codex-api.service" "Environment=\"MCTRL_EVIDENCE_ROOT=${expected_runtime_root}\"" "systemd service should write runtime evidence under the per-user temp root"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-codex-api.service" "\"--job-type\" \"codex-api\"" "codex-api service should set wrapper job type"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-codex-api.service" "ExecStart=\"" "systemd service should render a direct ExecStart command"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-codex-api.service" "\"--exec\" \"$env_root/bin/github-owner-pr-monitor --codex-api --codex-apply-and-push --codex-task-limit 10\"" "codex-api service should retain exact command under wrapper exec mode"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-pr-monitor.service" "WorkingDirectory=\"$REPO_AUTOMATION_DIR\"" "systemd service should quote working directory"
    assert_file_contains "$systemd_dir/worldarchitect-pr-automation-pr-monitor.service" "Environment=\"PATH=$env_root/bin:$env_root/home/Path With Spaces:/usr/bin:/bin\"" "systemd service should quote PATH environment"

    if [[ ! -d "$expected_log_dir" ]]; then
        echo "FAIL: expected Linux log directory to be created at $expected_log_dir" >&2
        exit 1
    fi

    if [[ -d "$env_root/home/Library/Logs/worldarchitect-automation" ]]; then
        echo "FAIL: Linux install should not create macOS-style ~/Library/Logs directory" >&2
        exit 1
    fi

    local disable_count
    disable_count="$(grep -c 'openclaw cron disable' "$OPENCLAW_CALL_LOG" || true)"
    if [[ "$disable_count" -ne 5 ]]; then
        echo "FAIL: expected exactly 5 OpenClaw disables during Linux install, got $disable_count" >&2
        exit 1
    fi

    assert_file_contains "$SYSTEMCTL_CALL_LOG" "--user enable --now worldarchitect-pr-automation-pr-monitor.timer" "systemctl should enable pr-monitor timer"
    assert_file_contains "$SYSTEMCTL_CALL_LOG" "--user start worldarchitect-pr-automation-pr-monitor.service" "systemctl should kick off pr-monitor service"
}

chmod +x "$INSTALL_SCRIPT"

run_macos_install_test
run_linux_install_test

echo "PASS: native scheduler install.sh tests"
