#!/usr/bin/env bash
set -euo pipefail

# Minimal mctrl -> ai_orch entrypoint.
# Keeps native automation intact and emits lifecycle metadata for mctrl-native
# catch-up dispatch. Legacy MISSION_CONTROL_* env vars are accepted only as
# compatibility fallbacks during the rename.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

default_runtime_state_root() {
  local job_type="$1"
  local base_dir="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
  local uid
  uid="$(id -u)"
  base_dir="${base_dir%/}"
  printf '%s/${PROJECT_NAME:-your-project}-automation/uid-%s/mctrl/%s' "${base_dir}" "${uid}" "${job_type}"
}

EVIDENCE_ROOT="${MCTRL_EVIDENCE_ROOT:-${MISSION_CONTROL_EVIDENCE_ROOT:-}}"

# Export GITHUB_TOKEN for downstream tooling consistency
export GITHUB_TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"

AGENT_CLI="${MCTRL_AGENT_CLI:-${MISSION_CONTROL_AGENT_CLI:-minimax}}"
MODEL="${MCTRL_MODEL:-${MISSION_CONTROL_MODEL:-}}"
TASK="${MCTRL_TASK:-${MISSION_CONTROL_TASK:-Reply with exactly: MCTRL_AI_ORCH_OK}}"
EXEC_COMMAND="${MCTRL_EXEC:-${MISSION_CONTROL_EXEC:-}}"
DRY_RUN=0
MODEL_EXPLICIT=0

SAFETY_DATA_DIR="${AUTOMATION_SAFETY_DATA_DIR:-/tmp/automation_safety}"
SAFETY_MANAGER_MODULE="jleechanorg_pr_automation.automation_safety_manager"
LOCK_FILE=""
METRICS_FILE=""
HEALTH_FILE=""
STALL_TIMEOUT_SECONDS="${MCTRL_STALL_TIMEOUT_SECONDS:-${MISSION_CONTROL_STALL_TIMEOUT_SECONDS:-1800}}"
LOCK_STALE_SECONDS="${MCTRL_LOCK_STALE_SECONDS:-${MISSION_CONTROL_LOCK_STALE_SECONDS:-7200}}"
PRE_EXEC_SLEEP_MAX_SECONDS="${MCTRL_PRE_EXEC_SLEEP_MAX_SECONDS:-${MISSION_CONTROL_PRE_EXEC_SLEEP_MAX_SECONDS:-0}}"

# Set PYTHONPATH to allow module imports from the automation directory
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

JOB_ID="${MCTRL_JOB_ID:-${MISSION_CONTROL_JOB_ID:-}}"
JOB_TYPE="${MCTRL_JOB_TYPE:-${MISSION_CONTROL_JOB_TYPE:-design_review}}"
PR_NUMBER="${MCTRL_PR_NUMBER:-${MISSION_CONTROL_PR_NUMBER:-}}"
HEAD_SHA="${MCTRL_HEAD_SHA:-${MISSION_CONTROL_HEAD_SHA:-}}"
REPO_NAME="${MCTRL_REPO:-${MISSION_CONTROL_REPO:-jleechanorg/${PROJECT_DOMAIN:-your-project}.com}}"
BRANCH_NAME="${MCTRL_BRANCH:-${MISSION_CONTROL_BRANCH:-}}"
TRIGGER_SOURCE="${MCTRL_TRIGGER_SOURCE:-${MISSION_CONTROL_TRIGGER_SOURCE:-catch_up}}"
WORKFLOW_LANE="${MCTRL_WORKFLOW_LANE:-${MISSION_CONTROL_WORKFLOW_LANE:-${JOB_TYPE}}}"

ERR_TAXONOMY_ARG="E_ARG_MISSING"
ERR_TAXONOMY_UNKNOWN_ARG="E_UNKNOWN_ARG"
ERR_TAXONOMY_TOOLING="E_TOOLING_MISSING"
ERR_TAXONOMY_SAFETY="E_SAFETY_BLOCKED"
ERR_TAXONOMY_EXECUTION="E_EXECUTION_FAILED"
ERR_TAXONOMY_STALLED="E_STALLED"
ERR_TAXONOMY_INTERNAL="E_INTERNAL"

require_arg() {
  local flag="$1"
  local value="$2"
  if [[ -z "${value}" || "${value}" == --* ]]; then
    echo "Error [${ERR_TAXONOMY_ARG}]: ${flag} requires a non-empty value that does not start with '--'" >&2
    exit 2
  fi
}

redact_sensitive() {
  local value="${1:-}"
  if [[ -z "${value}" ]]; then
    printf '%s' ""
    return
  fi

  # Broad secret redaction guardrail for metadata and logs.
  # Guard empty replacement patterns to avoid shell parameter expansion corruption.
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    value="${value//${GITHUB_TOKEN}/[REDACTED_GITHUB_TOKEN]}"
  fi
  if [[ -n "${GH_TOKEN:-}" ]]; then
    value="${value//${GH_TOKEN}/[REDACTED_GH_TOKEN]}"
  fi
  printf '%s' "${value}" | sed -E 's/(gh[pousr]_[A-Za-z0-9_]+)/[REDACTED_GH_TOKEN]/g; s/(sk-[A-Za-z0-9_-]{20,})/[REDACTED_API_KEY]/g'
}

write_metrics() {
  local status="$1"
  local elapsed_seconds="$2"
  STATUS="${status}" ELAPSED_SECONDS="${elapsed_seconds}" METRICS_FILE="${METRICS_FILE}" python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

metrics_file = Path(os.environ["METRICS_FILE"])
status = os.environ["STATUS"]
elapsed_seconds = int(os.environ.get("ELAPSED_SECONDS", "0"))

metrics = {
    "runs_total": 0,
    "runs_ok": 0,
    "runs_blocked": 0,
    "runs_failed": 0,
    "runs_stalled": 0,
    "last_status": None,
    "last_run_at": None,
    "last_duration_seconds": 0,
}

if metrics_file.exists():
    try:
        loaded = json.loads(metrics_file.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            metrics.update(loaded)
    except Exception:
        pass

metrics["runs_total"] = int(metrics.get("runs_total", 0)) + 1
if status == "ok":
    metrics["runs_ok"] = int(metrics.get("runs_ok", 0)) + 1
elif status == "blocked":
    metrics["runs_blocked"] = int(metrics.get("runs_blocked", 0)) + 1
elif status == "stalled":
    metrics["runs_stalled"] = int(metrics.get("runs_stalled", 0)) + 1
else:
    metrics["runs_failed"] = int(metrics.get("runs_failed", 0)) + 1

metrics["last_status"] = status
metrics["last_duration_seconds"] = elapsed_seconds
metrics["last_run_at"] = datetime.now(timezone.utc).isoformat()

metrics_file.parent.mkdir(parents=True, exist_ok=True)
metrics_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
PY
}

write_health() {
  local status="$1"
  local detail="$2"
  STATUS="${status}" DETAIL="${detail}" HEALTH_FILE="${HEALTH_FILE}" python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

payload = {
    "status": os.environ["STATUS"],
    "detail": os.environ.get("DETAIL") or None,
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

path = Path(os.environ["HEALTH_FILE"])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
}

write_metadata() {
  local mode="$1"
  local meta_file="$2"
  RC="${RC:-0}" MODE="${mode}" AI_ORCH_BIN="${AI_ORCH_BIN:-}" AGENT_CLI="${AGENT_CLI}" MODEL="${MODEL}" TASK="$(redact_sensitive "${TASK}")" EXEC_COMMAND="$(redact_sensitive "${EXEC_COMMAND}")" OUT_FILE="${OUT_FILE:-}" ERR_FILE="${ERR_FILE:-}" JOB_ID="${JOB_ID}" JOB_TYPE="${JOB_TYPE}" PR_NUMBER="${PR_NUMBER}" HEAD_SHA="${HEAD_SHA}" REPO_NAME="${REPO_NAME}" BRANCH_NAME="${BRANCH_NAME}" TRIGGER_SOURCE="${TRIGGER_SOURCE}" WORKFLOW_LANE="${WORKFLOW_LANE}" python3 - <<'PY' > "${meta_file}"
import json
import os

pr_number = (os.environ.get("PR_NUMBER") or "").strip()
head_sha = (os.environ.get("HEAD_SHA") or "").strip()
job_id = (os.environ.get("JOB_ID") or "").strip()
job_type = (os.environ.get("JOB_TYPE") or "").strip()
repo_name = (os.environ.get("REPO_NAME") or "").strip()
branch_name = (os.environ.get("BRANCH_NAME") or "").strip()

rc = int(os.environ.get("RC", "0"))
if os.environ["MODE"] == "dry_run":
  run_status = "dry_run"
elif os.environ["MODE"] == "live_run":
  if rc == 0:
    run_status = "ok"
  elif rc == 124:
    run_status = "stalled"
  else:
    run_status = "failed"
else:
  run_status = os.environ["MODE"]

def to_int_if_valid(value):
  value = (value or "").strip()
  if value.isdigit():
    parsed = int(value)
    if parsed > 0:
      return parsed
  return None

pr_number_value = to_int_if_valid(pr_number)
pr_correlation_part = f"pr-{pr_number_value}" if pr_number_value is not None else None
pr_idempotency_part = str(pr_number_value) if pr_number_value is not None else None
if pr_correlation_part and head_sha and job_type:
  correlation_id = ":".join([pr_correlation_part, head_sha, job_type])
else:
  correlation_id = None
if pr_idempotency_part and head_sha and job_type:
  idempotency_key = "|".join([pr_idempotency_part, head_sha, job_type])
else:
  idempotency_key = None

payload = {
  "status": run_status,
  "ai_orch": os.environ.get("AI_ORCH_BIN") or "ai_orch_not_in_path",
  "agent_cli": os.environ["AGENT_CLI"],
  "model": os.environ["MODEL"],
  "task": os.environ["TASK"],
  "exec_command": os.environ.get("EXEC_COMMAND") or None,
  "job_id": job_id or None,
  "job_type": job_type or None,
  "trigger_source": os.environ.get("TRIGGER_SOURCE") or None,
  "workflow_lane": os.environ.get("WORKFLOW_LANE") or job_type or None,
  "pr_number": pr_number_value,
  "head_sha": head_sha or None,
  "correlation_id": correlation_id,
  "idempotency_key": idempotency_key,
  "context": {
    "repo": repo_name or None,
    "branch": branch_name or None,
  },
}

if os.environ["MODE"] != "dry_run":
  payload["exit_code"] = int(os.environ.get("RC", "0"))
  payload["stdout_file"] = os.environ.get("OUT_FILE") or None
  payload["stderr_file"] = os.environ.get("ERR_FILE") or None

print(json.dumps(payload, indent=2))
PY
}

exit_with_artifacts() {
  local metadata_status="$1"
  local health_status="$2"
  local health_detail="$3"
  local metrics_status="$4"
  local exit_code="$5"
  RC="${exit_code}"
  write_metadata "${metadata_status}" "${META_FILE}" || true
  write_health "${health_status}" "${health_detail}" || true
  write_metrics "${metrics_status}" 0 || true
  exit "${exit_code}"
}

is_valid_pr_number() {
  local value="${1:-}"
  [[ "${value}" =~ ^[1-9][0-9]*$ ]]
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent-cli)
      require_arg "--agent-cli" "${2:-}"
      AGENT_CLI="$2"; shift 2 ;;
    --model)
      require_arg "--model" "${2:-}"
      MODEL="$2"; MODEL_EXPLICIT=1; shift 2 ;;
    --task)
      require_arg "--task" "${2:-}"
      TASK="$2"; shift 2 ;;
    --exec)
      require_arg "--exec" "${2:-}"
      EXEC_COMMAND="$2"; shift 2 ;;
    --pr-number)
      require_arg "--pr-number" "${2:-}"
      PR_NUMBER="$2"; shift 2 ;;
    --job-id)
      require_arg "--job-id" "${2:-}"
      JOB_ID="$2"; shift 2 ;;
    --head-sha)
      require_arg "--head-sha" "${2:-}"
      HEAD_SHA="$2"; shift 2 ;;
    --job-type)
      require_arg "--job-type" "${2:-}"
      JOB_TYPE="$2"; shift 2 ;;
    --repo)
      require_arg "--repo" "${2:-}"
      REPO_NAME="$2"; shift 2 ;;
    --branch)
      require_arg "--branch" "${2:-}"
      BRANCH_NAME="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    *)
      echo "Error [${ERR_TAXONOMY_UNKNOWN_ARG}]: Unknown arg: $1" >&2
      exit 2 ;;
  esac
done

if [[ -z "${MCTRL_WORKFLOW_LANE:-}" && -z "${MISSION_CONTROL_WORKFLOW_LANE:-}" ]]; then
  WORKFLOW_LANE="${JOB_TYPE}"
fi

if [[ -z "${EVIDENCE_ROOT}" ]]; then
  EVIDENCE_ROOT="$(default_runtime_state_root "${JOB_TYPE}")"
fi
LOCK_FILE="${MCTRL_LOCK_FILE:-${MISSION_CONTROL_LOCK_FILE:-${EVIDENCE_ROOT}/.mctrl.lock}}"
METRICS_FILE="${MCTRL_METRICS_FILE:-${MISSION_CONTROL_METRICS_FILE:-${EVIDENCE_ROOT}/metrics.json}}"
HEALTH_FILE="${MCTRL_HEALTH_FILE:-${MISSION_CONTROL_HEALTH_FILE:-${EVIDENCE_ROOT}/health.json}}"
mkdir -p "${EVIDENCE_ROOT}"

if [[ "${MODEL_EXPLICIT}" == "0" && "${AGENT_CLI}" == "minimax" ]]; then
  MODEL="MiniMax-M2.5"
fi

if [[ "${DRY_RUN}" != "1" && "${PRE_EXEC_SLEEP_MAX_SECONDS}" =~ ^[0-9]+$ ]] && (( PRE_EXEC_SLEEP_MAX_SECONDS > 0 )); then
  sleep "$(( RANDOM % (PRE_EXEC_SLEEP_MAX_SECONDS + 1) ))"
fi

mkdir -p "$(dirname "${LOCK_FILE}")"
if command -v flock >/dev/null 2>&1; then
  exec 9>"${LOCK_FILE}"
  if ! flock -n 9; then
    echo "[mctrl] another run is in progress, skipping" >&2
    exit 0
  fi
else
  # macOS-safe fallback when `flock` is unavailable: atomic mkdir lock.
  LOCK_DIR_FALLBACK="${LOCK_FILE}.d"
  mkdir_lock_fallback() {
    mkdir "${LOCK_DIR_FALLBACK}" 2>/dev/null || return 1
    printf '%s\n' "$$" > "${LOCK_DIR_FALLBACK}/pid"
    date +%s > "${LOCK_DIR_FALLBACK}/created_at"
    return 0
  }
  if ! mkdir_lock_fallback; then
    created_at=""
    if [[ -f "${LOCK_DIR_FALLBACK}/created_at" ]]; then
      created_at="$(cat "${LOCK_DIR_FALLBACK}/created_at" 2>/dev/null || true)"
    fi
    now_epoch="$(date +%s)"
    if [[ "${created_at}" =~ ^[0-9]+$ ]] && (( now_epoch - created_at > LOCK_STALE_SECONDS )); then
      echo "[mctrl] stale fallback lock detected (age=$((now_epoch - created_at))s), recovering" >&2
      rm -rf "${LOCK_DIR_FALLBACK}"
      mkdir_lock_fallback || {
        echo "[mctrl] another run is in progress, skipping" >&2
        exit 0
      }
    else
      echo "[mctrl] another run is in progress, skipping" >&2
      exit 0
    fi
  fi
  trap 'rm -rf "${LOCK_DIR_FALLBACK}" >/dev/null 2>&1 || true' EXIT
fi

RUN_DIR="$(mktemp -d "${EVIDENCE_ROOT}/run_XXXXXXXX")"
OUT_FILE="${RUN_DIR}/ai_orch.out.txt"
ERR_FILE="${RUN_DIR}/ai_orch.err.txt"
META_FILE="${RUN_DIR}/run.json"

SAFETY_COMMON_ARGS=(--data-dir "${SAFETY_DATA_DIR}")
if [[ -n "${REPO_NAME}" ]]; then
  SAFETY_COMMON_ARGS+=(--repo "${REPO_NAME}")
fi
if [[ -n "${BRANCH_NAME}" ]]; then
  SAFETY_COMMON_ARGS+=(--branch "${BRANCH_NAME}")
fi

if [[ "${DRY_RUN}" != "1" ]]; then
  AI_ORCH_BIN=""
  if [[ -z "${EXEC_COMMAND}" ]]; then
    AI_ORCH_BIN="$(command -v ai_orch || true)"
  fi
  if [[ -z "${AI_ORCH_BIN}" && -z "${EXEC_COMMAND}" ]]; then
    echo "Error [${ERR_TAXONOMY_TOOLING}]: ai_orch not found in PATH" >&2
    exit_with_artifacts "failed" "degraded" "ai_orch_not_found" "failed" 127
  fi

  if ! python3 - <<'PY'
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec("jleechanorg_pr_automation.automation_safety_manager") else 1)
PY
  then
    echo "Error [${ERR_TAXONOMY_SAFETY}]: safety manager module unavailable; refusing to run" >&2
    exit_with_artifacts "failed" "degraded" "safety_module_unavailable" "failed" 90
  fi

  if [[ -n "${PR_NUMBER}" ]]; then
    if is_valid_pr_number "${PR_NUMBER}"; then
      if ! python3 -m "${SAFETY_MANAGER_MODULE}" "${SAFETY_COMMON_ARGS[@]}" --check-pr "${PR_NUMBER}" >/dev/null; then
        echo "[mctrl] blocked by AutomationSafetyManager PR limits for #${PR_NUMBER}" >&2
        exit_with_artifacts "blocked" "ok" "blocked_pr_limit" "blocked" 0
      fi
    else
      echo "Error [${ERR_TAXONOMY_ARG}]: PR_NUMBER must be a positive integer, got '${PR_NUMBER}'" >&2
      exit_with_artifacts "failed" "degraded" "invalid_pr_number" "failed" 2
    fi
  fi

  if ! python3 -m "${SAFETY_MANAGER_MODULE}" "${SAFETY_COMMON_ARGS[@]}" --check-global >/dev/null; then
    echo "[mctrl] blocked by AutomationSafetyManager global run limits" >&2
    exit_with_artifacts "blocked" "ok" "blocked_global_limit" "blocked" 0
  fi

  if ! python3 -m "${SAFETY_MANAGER_MODULE}" "${SAFETY_COMMON_ARGS[@]}" --record-global >/dev/null; then
    echo "Error [${ERR_TAXONOMY_SAFETY}]: failed to record global run start" >&2
    exit_with_artifacts "failed" "degraded" "global_record_failed" "failed" 91
  fi
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  AI_ORCH_BIN="$(command -v ai_orch || echo "ai_orch_not_in_path")"
  write_metadata "dry_run" "${META_FILE}"
  write_health "ok" "dry_run"
  write_metrics "ok" 0
  echo "[mctrl] dry run complete: ${META_FILE}"
  exit 0
fi

if [[ -n "${EXEC_COMMAND}" ]]; then
  export AUTOMATION_SAFETY_WRAPPER=1
  # Use POSIX-compliant read loop instead of mapfile (Bash 4+ only, not available in Bash 3.2 on macOS)
  AI_ORCH_ARGS=()
  while IFS= read -r line; do
    AI_ORCH_ARGS+=("$line")
  done < <(
    EXEC_COMMAND="${EXEC_COMMAND}" python3 - <<'PY'
import os
import shlex

for arg in shlex.split(os.environ["EXEC_COMMAND"]):
    print(arg)
PY
  )
  if [[ ${#AI_ORCH_ARGS[@]} -eq 0 ]]; then
    echo "Error [${ERR_TAXONOMY_ARG}]: --exec produced an empty command" >&2
    exit_with_artifacts "failed" "degraded" "empty_exec_command" "failed" 2
  fi
else
  AI_ORCH_ARGS=(run --agent-cli "${AGENT_CLI}")
  if [[ -n "${MODEL}" ]]; then
    AI_ORCH_ARGS+=(--model "${MODEL}")
  fi
  AI_ORCH_ARGS+=("${TASK}")
fi

if [[ -n "${EXEC_COMMAND}" ]]; then
  RUN_CMD=("${AI_ORCH_ARGS[@]}")
else
  RUN_CMD=("${AI_ORCH_BIN}" "${AI_ORCH_ARGS[@]}")
fi

RUN_STARTED_AT="$(python3 - <<'PY'
import time
print(int(time.time()))
PY
)"

set +e
if [[ -n "${EXEC_COMMAND}" ]]; then
  python3 - "${STALL_TIMEOUT_SECONDS}" "${OUT_FILE}" "${ERR_FILE}" "${RUN_CMD[@]}" <<'PY'
import subprocess
import sys

stall_timeout = int(sys.argv[1])
out_file = sys.argv[2]
err_file = sys.argv[3]
command = sys.argv[4:]

with open(out_file, "wb") as out, open(err_file, "wb") as err:
    try:
        completed = subprocess.run(command, stdout=out, stderr=err, timeout=stall_timeout)
        sys.exit(completed.returncode)
    except subprocess.TimeoutExpired:
        sys.exit(124)
PY
  RC=$?
elif command -v timeout >/dev/null 2>&1; then
  timeout --signal=TERM --kill-after=5 "${STALL_TIMEOUT_SECONDS}" "${RUN_CMD[@]}" >"${OUT_FILE}" 2>"${ERR_FILE}"
  RC=$?
elif command -v gtimeout >/dev/null 2>&1; then
  gtimeout --signal=TERM --kill-after=5 "${STALL_TIMEOUT_SECONDS}" "${RUN_CMD[@]}" >"${OUT_FILE}" 2>"${ERR_FILE}"
  RC=$?
else
  python3 - "${STALL_TIMEOUT_SECONDS}" "${OUT_FILE}" "${ERR_FILE}" "${RUN_CMD[@]}" <<'PY'
import subprocess
import sys

stall_timeout = int(sys.argv[1])
out_file = sys.argv[2]
err_file = sys.argv[3]
command = sys.argv[4:]

with open(out_file, "wb") as out, open(err_file, "wb") as err:
    try:
        completed = subprocess.run(command, stdout=out, stderr=err, timeout=stall_timeout, check=False)
        sys.exit(completed.returncode)
    except subprocess.TimeoutExpired:
        sys.exit(124)
PY
  RC=$?
fi
set -e

RUN_ENDED_AT="$(python3 - <<'PY'
import time
print(int(time.time()))
PY
)"
ELAPSED_SECONDS=$((RUN_ENDED_AT - RUN_STARTED_AT))

if [[ "${RC}" == "0" ]]; then
  RUN_STATUS="ok"
elif [[ "${RC}" == "124" ]]; then
  RUN_STATUS="stalled"
  echo "Error [${ERR_TAXONOMY_STALLED}]: command invocation exceeded mctrl stall threshold (${STALL_TIMEOUT_SECONDS}s)" >&2
else
  RUN_STATUS="failed"
fi

if [[ -n "${PR_NUMBER}" ]] && is_valid_pr_number "${PR_NUMBER}"; then
  PR_RECORD_STATUS=""
  if [[ "${RUN_STATUS}" == "ok" ]]; then
    PR_RECORD_STATUS="success"
  elif [[ "${RUN_STATUS}" == "failed" || "${RUN_STATUS}" == "stalled" ]]; then
    PR_RECORD_STATUS="failure"
  fi

  if [[ -n "${PR_RECORD_STATUS}" ]]; then
    python3 -m "${SAFETY_MANAGER_MODULE}" "${SAFETY_COMMON_ARGS[@]}" --record-pr "${PR_NUMBER}" "${PR_RECORD_STATUS}" >/dev/null \
      || echo "[mctrl] warning: failed to record pr run (${PR_RECORD_STATUS})" >&2
  fi
fi

write_metadata "live_run" "${META_FILE}" || echo "[mctrl] warning: failed to write run metadata to ${META_FILE}" >&2
write_metrics "${RUN_STATUS}" "${ELAPSED_SECONDS}" || true

if [[ "${RUN_STATUS}" == "ok" ]]; then
  write_health "ok" "live_run_success" || true
else
  write_health "degraded" "${RUN_STATUS}" || true
fi

if [[ -f "${META_FILE}" ]]; then
  cat "${META_FILE}" || echo "[mctrl] warning: failed to read metadata" >&2
fi
exit "${RC}"
