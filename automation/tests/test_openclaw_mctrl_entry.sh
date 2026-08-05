#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENTRYPOINT="${SCRIPT_DIR}/openclaw_mctrl_entry.sh"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "${TEST_DIR}"' EXIT

mkdir -p "${TEST_DIR}/bin" "${TEST_DIR}/state"
REAL_PYTHON3="$(command -v python3)"
export PATH="${TEST_DIR}/bin:${PATH}"

cat >"${TEST_DIR}/bin/flock" <<'EOF'
#!/usr/bin/env bash
# test shim: always succeeds and does not execute command mode
exit 0
EOF
chmod +x "${TEST_DIR}/bin/flock"

cat >"${TEST_DIR}/bin/python3" <<EOF
#!/usr/bin/env bash
if [[ "\$1" == "-m" ]]; then
  shift
  mod="\$1"
  shift
  case "\$mod" in
    jleechanorg_pr_automation.automation_safety_manager)
      args=("\$@")
      idx=0
      while [[ \$idx -lt \${#args[@]} ]]; do
        token="\${args[\$idx]}"
        case "\$token" in
          --check-pr)
            exit "\${SAFETY_CHECK_PR_RC:-0}"
            ;;
          --check-global)
            exit "\${SAFETY_CHECK_GLOBAL_RC:-0}"
            ;;
          --record-global)
            exit "\${SAFETY_RECORD_GLOBAL_RC:-0}"
            ;;
          --record-pr)
            if [[ -n "\${SAFETY_RECORD_PR_LOG:-}" ]]; then
              pr_number="\${args[\$((idx+1))]:-}"
              result="\${args[\$((idx+2))]:-}"
              printf '%s %s\n' "\${pr_number}" "\${result}" >> "\${SAFETY_RECORD_PR_LOG}"
            fi
            exit "\${SAFETY_RECORD_PR_RC:-0}"
            ;;
        esac
        idx=\$((idx+1))
      done
      exit 0
      ;;
  esac
fi
if [[ "\$1" == "-" ]]; then
  "${REAL_PYTHON3}" "\$@"
  exit \$?
fi
exec "${REAL_PYTHON3}" "\$@"
EOF
chmod +x "${TEST_DIR}/bin/python3"

cat >"${TEST_DIR}/bin/ai_orch" <<'EOF'
#!/usr/bin/env bash
echo "ok"
exit 0
EOF
chmod +x "${TEST_DIR}/bin/ai_orch"

cat >"${TEST_DIR}/bin/jleechanorg-pr-monitor" <<'EOF'
#!/usr/bin/env bash
python3 - "$@" <<'PY' > "${MONITOR_ARGS_LOG:?}"
import json
import os
import sys

json.dump(
    {
        "argv": sys.argv[1:],
        "automation_safety_wrapper": os.environ.get("AUTOMATION_SAFETY_WRAPPER"),
        "parent_command": os.popen(f"ps -p {os.getppid()} -o command=").read().strip(),
    },
    sys.stdout,
)
sys.stdout.write("\n")
PY
exit 0
EOF
chmod +x "${TEST_DIR}/bin/jleechanorg-pr-monitor"

# dry run produces metadata/health/metrics and redacts tokens
MCTRL_EVIDENCE_ROOT="${TEST_DIR}/evidence"
AUTOMATION_SAFETY_DATA_DIR="${TEST_DIR}/state"
GITHUB_TOKEN="ghp_supersecret"
export GITHUB_TOKEN AUTOMATION_SAFETY_DATA_DIR MCTRL_EVIDENCE_ROOT

output="$(${ENTRYPOINT} --dry-run --task 'please use ghp_supersecret token' --repo owner/repo --branch test-branch)"
meta_file="$(echo "$output" | sed -n 's/.*dry run complete: //p')"

if ! grep -q 'REDACTED_' "$meta_file"; then
  echo "FAIL: expected task token redaction in metadata"
  exit 1
fi

unset GITHUB_TOKEN GH_TOKEN
output_no_tokens="$(${ENTRYPOINT} --dry-run --task 'safe text 123' --repo owner/repo --branch test-branch)"
meta_file_no_tokens="$(echo "$output_no_tokens" | sed -n 's/.*dry run complete: //p')"
if ! grep -q '"task": "safe text 123"' "$meta_file_no_tokens"; then
  echo "FAIL: empty token redaction corrupted task"
  exit 1
fi

metrics_file="${MCTRL_EVIDENCE_ROOT}/metrics.json"
health_file="${MCTRL_EVIDENCE_ROOT}/health.json"

if [[ ! -f "$metrics_file" ]]; then
  echo "FAIL: metrics file missing"
  exit 1
fi
if [[ ! -f "$health_file" ]]; then
  echo "FAIL: health file missing"
  exit 1
fi

# blocked preflight should be tracked as blocked and still emit run metadata
set +e
SAFETY_CHECK_PR_RC=1 "${ENTRYPOINT}" --task "blocked check" --pr-number 123 >/dev/null 2>&1
blocked_rc=$?
set -e

if [[ "${blocked_rc}" -ne 0 ]]; then
  echo "FAIL: expected blocked preflight to exit 0, got ${blocked_rc}"
  exit 1
fi

blocked_run_json="$(ls -td "${MCTRL_EVIDENCE_ROOT}"/run_* | head -n1)/run.json"
python3 - "$metrics_file" "$blocked_run_json" <<'PY'
import json
import sys

metrics = json.load(open(sys.argv[1], encoding="utf-8"))
run = json.load(open(sys.argv[2], encoding="utf-8"))

if int(metrics.get("runs_blocked", 0)) < 1:
    raise SystemExit("FAIL: expected runs_blocked >= 1 after blocked preflight")
if metrics.get("last_status") != "blocked":
    raise SystemExit("FAIL: expected last_status=blocked after blocked preflight")
if run.get("status") != "blocked":
    raise SystemExit("FAIL: expected run.json status=blocked for blocked preflight")
if int(run.get("exit_code", -1)) != 0:
    raise SystemExit("FAIL: expected blocked preflight run.json exit_code=0")
PY

# non-numeric PR values must fail closed
set +e
"${ENTRYPOINT}" --task "invalid pr" --pr-number abc >/dev/null 2>&1
invalid_pr_rc=$?
set -e

if [[ "${invalid_pr_rc}" -ne 2 ]]; then
  echo "FAIL: expected invalid PR_NUMBER exit code 2, got ${invalid_pr_rc}"
  exit 1
fi

invalid_pr_run_json="$(ls -td "${MCTRL_EVIDENCE_ROOT}"/run_* | head -n1)/run.json"
python3 - "$invalid_pr_run_json" <<'PY'
import json
import sys

run = json.load(open(sys.argv[1], encoding="utf-8"))
if run.get("status") != "failed":
    raise SystemExit("FAIL: invalid PR_NUMBER should produce run.json status=failed")
PY

# global run accounting failure should hard-fail
set +e
SAFETY_RECORD_GLOBAL_RC=1 "${ENTRYPOINT}" --task "record global fail" --pr-number 123 >/dev/null 2>&1
record_global_rc=$?
set -e

if [[ "${record_global_rc}" -ne 91 ]]; then
  echo "FAIL: expected record-global failure exit code 91, got ${record_global_rc}"
  exit 1
fi

# stalled-task path should return 124 and increment stalled counter
cat >"${TEST_DIR}/bin/ai_orch" <<'EOF'
#!/usr/bin/env bash
sleep 2
exit 0
EOF
chmod +x "${TEST_DIR}/bin/ai_orch"

record_pr_log="${TEST_DIR}/record-pr.log"
export SAFETY_RECORD_PR_LOG="${record_pr_log}"
rm -f "${record_pr_log}"
runs_failed_before_stall="$(python3 - "$metrics_file" <<'PY'
import json
import sys
metrics = json.load(open(sys.argv[1], encoding="utf-8"))
print(int(metrics.get("runs_failed", 0)))
PY
)"

set +e
MCTRL_STALL_TIMEOUT_SECONDS=1 "${ENTRYPOINT}" --task "normal" --pr-number 123 >/dev/null 2>&1
rc=$?
set -e

if [[ "$rc" -ne 124 ]]; then
  echo "FAIL: expected stalled exit code 124, got $rc"
  exit 1
fi

latest_run_json="$(ls -td "${MCTRL_EVIDENCE_ROOT}"/run_* | head -n1)/run.json"

python3 - "$metrics_file" "$latest_run_json" "${runs_failed_before_stall}" <<'PY'
import json
import sys

metrics = json.load(open(sys.argv[1], encoding="utf-8"))
run = json.load(open(sys.argv[2], encoding="utf-8"))
runs_failed_before_stall = int(sys.argv[3])

if int(metrics.get("runs_stalled", 0)) < 1:
    raise SystemExit("FAIL: expected runs_stalled >= 1")
if int(metrics.get("runs_failed", 0)) != runs_failed_before_stall:
    raise SystemExit("FAIL: stalled run must not increment runs_failed")
if metrics.get("last_status") != "stalled":
    raise SystemExit("FAIL: expected last_status=stalled")
if run.get("status") != "stalled":
    raise SystemExit("FAIL: expected run.json status=stalled")
if int(run.get("exit_code", -1)) != 124:
    raise SystemExit("FAIL: expected run.json exit_code=124")
PY

if ! grep -q '^123 failure$' "${record_pr_log}"; then
  echo "FAIL: expected stalled run to record PR failure"
  exit 1
fi

exec_mode_dir="$(mktemp -d "${TEST_DIR}/exec-mode.XXXXXX")"
export MONITOR_ARGS_LOG="${exec_mode_dir}/monitor-args.log"
export MCTRL_TRIGGER_SOURCE="catch_up"
export MCTRL_WORKFLOW_LANE="fixpr"
exec_output="$(
  MCTRL_EVIDENCE_ROOT="${exec_mode_dir}/evidence" \
  AUTOMATION_SAFETY_DATA_DIR="${TEST_DIR}/state" \
  "${ENTRYPOINT}" --exec "${TEST_DIR}/bin/jleechanorg-pr-monitor --fixpr '' 'value with spaces' --max-prs 10" --job-type fixpr --pr-number 321 --head-sha deadbeef --repo owner/repo
)"
exec_run_json="$(ls -td "${exec_mode_dir}/evidence"/run_* | head -n1)/run.json"

if [[ ! -f "${MONITOR_ARGS_LOG}" ]]; then
  echo "FAIL: expected exec mode to invoke jleechanorg-pr-monitor"
  exit 1
fi

python3 - "${MONITOR_ARGS_LOG}" "${exec_run_json}" <<'PY'
import json
import sys

monitor_args = json.load(open(sys.argv[1], encoding="utf-8"))
run = json.load(open(sys.argv[2], encoding="utf-8"))
if monitor_args.get("argv") != ["--fixpr", "", "value with spaces", "--max-prs", "10"]:
    raise SystemExit(f"FAIL: expected exact exec-mode argv preservation, got {monitor_args!r}")
if monitor_args.get("automation_safety_wrapper") != "1":
    raise SystemExit("FAIL: expected exec mode to export AUTOMATION_SAFETY_WRAPPER=1")
if "bash -lc" in (monitor_args.get("parent_command") or ""):
    raise SystemExit("FAIL: expected exec mode to avoid /bin/bash -lc wrapper")
if run.get("trigger_source") != "catch_up":
    raise SystemExit("FAIL: expected trigger_source=catch_up in exec mode metadata")
if run.get("workflow_lane") != "fixpr":
    raise SystemExit("FAIL: expected workflow_lane=fixpr in exec mode metadata")
if run.get("idempotency_key") != "321|deadbeef|fixpr":
    raise SystemExit("FAIL: expected idempotency key in exec mode metadata")
if run.get("status") != "ok":
    raise SystemExit("FAIL: expected exec mode run to finish with status=ok")
PY

mv "${TEST_DIR}/bin/ai_orch" "${TEST_DIR}/bin/ai_orch.hidden"
exec_mode_no_ai_orch_dir="$(mktemp -d "${TEST_DIR}/exec-mode-no-ai-orch.XXXXXX")"
MONITOR_ARGS_LOG="${exec_mode_no_ai_orch_dir}/monitor-args.log" \
MCTRL_EVIDENCE_ROOT="${exec_mode_no_ai_orch_dir}/evidence" \
AUTOMATION_SAFETY_DATA_DIR="${TEST_DIR}/state" \
  "${ENTRYPOINT}" --exec "${TEST_DIR}/bin/jleechanorg-pr-monitor --fixpr --max-prs 1" --job-type fixpr --repo owner/repo >/dev/null
if [[ ! -f "${exec_mode_no_ai_orch_dir}/monitor-args.log" ]]; then
  echo "FAIL: expected exec mode to run without ai_orch in PATH"
  exit 1
fi
mv "${TEST_DIR}/bin/ai_orch.hidden" "${TEST_DIR}/bin/ai_orch"

unset MCTRL_WORKFLOW_LANE
exec_mode_job_type_dir="$(mktemp -d "${TEST_DIR}/exec-mode-job-type.XXXXXX")"
exec_job_type_output="$(
  MCTRL_EVIDENCE_ROOT="${exec_mode_job_type_dir}/evidence" \
  AUTOMATION_SAFETY_DATA_DIR="${TEST_DIR}/state" \
  "${ENTRYPOINT}" --exec "${TEST_DIR}/bin/jleechanorg-pr-monitor --comment-validation --max-prs 10" --job-type comment-validation --pr-number 654 --head-sha cafebabe --repo owner/repo
)"
exec_job_type_run_json="$(ls -td "${exec_mode_job_type_dir}/evidence"/run_* | head -n1)/run.json"

python3 - "${exec_job_type_run_json}" <<'PY'
import json
import sys

run = json.load(open(sys.argv[1], encoding="utf-8"))
if run.get("job_type") != "comment-validation":
    raise SystemExit("FAIL: expected job_type=comment-validation in job-type fallback test")
if run.get("workflow_lane") != "comment-validation":
    raise SystemExit("FAIL: expected workflow_lane to fall back to parsed job_type")
if run.get("idempotency_key") != "654|cafebabe|comment-validation":
    raise SystemExit("FAIL: expected idempotency key to use parsed job_type")
PY

echo "PASS: openclaw mctrl entrypoint tests"
echo "PASS: exec mode metadata tests"
