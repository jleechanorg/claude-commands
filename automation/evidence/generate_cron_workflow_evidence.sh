#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AUTOMATION_DIR="$ROOT_DIR/automation"
BRANCH="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD)"
HEAD_COMMIT="$(git -C "$ROOT_DIR" rev-parse HEAD)"
ORIGIN_MAIN="$(git -C "$ROOT_DIR" rev-parse origin/main 2>/dev/null || true)"

TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
BASE_TMP="$(mktemp -d -t cron-workflow-evidence.XXXXXX 2>/dev/null || mktemp -d)"
OUT_DIR="${BASE_TMP}/cron-workflow-evidence/${BRANCH}/${TS_UTC}"
ART_DIR="${OUT_DIR}/artifacts"
mkdir -p "$ART_DIR"

TARGET_REPO="${EVIDENCE_TARGET_REPO:-jleechanorg/worldarchitect.ai}"
TARGET_PR="${EVIDENCE_TARGET_PR:-3269}"

if ! [[ "$TARGET_PR" =~ ^[0-9]+$ ]]; then
  echo "ERROR: EVIDENCE_TARGET_PR must be numeric (got '${TARGET_PR}')" >&2
  exit 1
fi

VENV_DIR="${BASE_TMP}/venv"
mkdir -p "$VENV_DIR"

run_and_capture() {
  local name="$1"
  shift
  local out="${ART_DIR}/${name}.out.txt"
  local err="${ART_DIR}/${name}.err.txt"
  local meta="${ART_DIR}/${name}.meta.json"
  echo "==> ${name}"
  printf '$ %q' "$@" >"$out"
  printf '\n' >>"$out"
  : >"$err"
  set +e
  "$@" >>"$out" 2>>"$err"
  local code=$?
  set -e
  python3 - "$name" "$TS_UTC" "$code" "$@" >"$meta" <<'PY'
import json
import sys

name = sys.argv[1]
ts = sys.argv[2]
code = int(sys.argv[3])
cmd = sys.argv[4:]
print(
    json.dumps(
        {
            "name": name,
            "cmd": cmd,
            "exit_code": code,
            "timestamp_utc": ts,
        },
        indent=2,
        sort_keys=True,
    )
)
PY
  # Always continue; failures are recorded in meta.
  return 0
}

write_sha256() {
  local path="$1"
  local out="${path}.sha256"
  if [[ -f "$path" ]]; then
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum "$path" > "$out"
      return 0
    fi
    if command -v shasum >/dev/null 2>&1; then
      shasum -a 256 "$path" > "$out"
      return 0
    fi
    python3 - "$path" > "$out" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
digest = hashlib.sha256(path.read_bytes()).hexdigest()
print(f"{digest}  {path.name}")
PY
    return 0
  fi
  printf 'MISSING %s\n' "$path" > "$out"
  return 0
}

cat > "${OUT_DIR}/README.md" <<EOF
# Cron Workflow Evidence

- Created (UTC): ${TS_UTC}
- Repo: ${ROOT_DIR}
- Branch: ${BRANCH}
- Head commit: ${HEAD_COMMIT}
- Origin/main: ${ORIGIN_MAIN}
- Target PR: ${TARGET_REPO}#${TARGET_PR}
- Venv: ${VENV_DIR}

This run exercises the *real* CLI entrypoints used by crontab (see \`automation/restore_crontab.sh\`),
captures exact command lines, stdout/stderr, and exit codes, and includes a PR marker inspection.
EOF

cat > "${OUT_DIR}/metadata.json" <<EOF
{
  "timestamp_utc": "${TS_UTC}",
  "repo_root": "${ROOT_DIR}",
  "branch": "${BRANCH}",
  "head_commit": "${HEAD_COMMIT}",
  "origin_main_commit": "${ORIGIN_MAIN}",
  "target_repo": "${TARGET_REPO}",
  "target_pr": ${TARGET_PR},
  "venv_dir": "${VENV_DIR}"
}
EOF

write_sha256 "${OUT_DIR}/README.md"
write_sha256 "${OUT_DIR}/metadata.json"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install -U pip setuptools wheel >/dev/null

INSTALL_MODE="${EVIDENCE_INSTALL_MODE:-editable}"
if [[ "$INSTALL_MODE" == "pypi" ]]; then
  AUTOMATION_VERSION="${EVIDENCE_PR_AUTOMATION_VERSION:-0.2.37}"
  ORCH_VERSION="${EVIDENCE_ORCHESTRATION_VERSION:-0.1.21}"
  PIP_INSTALL_COMMON=(--no-cache-dir --index-url https://pypi.org/simple)
  "$VENV_DIR/bin/pip" install "${PIP_INSTALL_COMMON[@]}" "jleechanorg-orchestration==${ORCH_VERSION}" >/dev/null
  "$VENV_DIR/bin/pip" install "${PIP_INSTALL_COMMON[@]}" "jleechanorg-pr-automation[dev]==${AUTOMATION_VERSION}" >/dev/null
else
  "$VENV_DIR/bin/pip" install -e "$AUTOMATION_DIR[dev]" >/dev/null
fi

run_and_capture "env_versions" "$VENV_DIR/bin/python" - <<'PY' || true
import importlib.metadata as m
import sys
import jleechanorg_pr_automation
print("python:", sys.version)
print("jleechanorg_pr_automation.__file__:", jleechanorg_pr_automation.__file__)
print("dist version:", m.version("jleechanorg-pr-automation"))
PY
write_sha256 "${ART_DIR}/env_versions.out.txt"
write_sha256 "${ART_DIR}/env_versions.err.txt"
write_sha256 "${ART_DIR}/env_versions.meta.json"

if [[ "$INSTALL_MODE" == "pypi" ]]; then
  run_and_capture "pytest_automation" "$VENV_DIR/bin/python" - <<'PY' || true
import importlib.util
import os
import subprocess
import sys

spec = importlib.util.find_spec("jleechanorg_pr_automation")
if spec is None or spec.origin is None:
    raise SystemExit("Could not locate installed jleechanorg_pr_automation")

pkg_dir = os.path.dirname(spec.origin)
tests_dir = os.path.join(pkg_dir, "tests")
cmd = [sys.executable, "-m", "pytest", "-q", "-c", os.devnull, tests_dir]
print("Running:", " ".join(cmd))
proc = subprocess.run(cmd, check=False)
raise SystemExit(proc.returncode)
PY
else
  run_and_capture "pytest_automation" "$VENV_DIR/bin/python" -m pytest -q "$AUTOMATION_DIR/jleechanorg_pr_automation/tests" || true
fi
write_sha256 "${ART_DIR}/pytest_automation.out.txt"
write_sha256 "${ART_DIR}/pytest_automation.err.txt"
write_sha256 "${ART_DIR}/pytest_automation.meta.json"

run_and_capture "inspect_markers" "$VENV_DIR/bin/python" "$AUTOMATION_DIR/evidence/inspect_pr_marker_counts.py" \
  --repo "$TARGET_REPO" --pr "$TARGET_PR" --json-out "${ART_DIR}/marker_counts.json"
write_sha256 "${ART_DIR}/inspect_markers.out.txt"
write_sha256 "${ART_DIR}/inspect_markers.err.txt"
write_sha256 "${ART_DIR}/inspect_markers.meta.json"
write_sha256 "${ART_DIR}/marker_counts.json"

# Run the cron commands in a non-mutating mode for evidence collection.
# Use explicit CLI params (not environment variables) for safety limits.
PR_AUTOMATION_LIMIT="${PR_AUTOMATION_LIMIT:-1000}"
FIX_COMMENT_LIMIT="${FIX_COMMENT_LIMIT:-1000}"
FIXPR_LIMIT="${FIXPR_LIMIT:-1000}"
CODEX_TASK_LIMIT="${CODEX_TASK_LIMIT:-1}"

run_and_capture "cron_workflow1_pr_monitor" "$VENV_DIR/bin/jleechanorg-pr-monitor" \
  --no-act \
  --pr-automation-limit "$PR_AUTOMATION_LIMIT" \
  --fix-comment-limit "$FIX_COMMENT_LIMIT" \
  --fixpr-limit "$FIXPR_LIMIT"
write_sha256 "${ART_DIR}/cron_workflow1_pr_monitor.out.txt"
write_sha256 "${ART_DIR}/cron_workflow1_pr_monitor.err.txt"
write_sha256 "${ART_DIR}/cron_workflow1_pr_monitor.meta.json"

run_and_capture "cron_workflow2_fixpr" "$VENV_DIR/bin/jleechanorg-pr-monitor" \
  --no-act \
  --fixpr \
  --max-prs 5 \
  --cli-agent gemini \
  --pr-automation-limit "$PR_AUTOMATION_LIMIT" \
  --fix-comment-limit "$FIX_COMMENT_LIMIT" \
  --fixpr-limit "$FIXPR_LIMIT"
write_sha256 "${ART_DIR}/cron_workflow2_fixpr.out.txt"
write_sha256 "${ART_DIR}/cron_workflow2_fixpr.err.txt"
write_sha256 "${ART_DIR}/cron_workflow2_fixpr.meta.json"

run_and_capture "cron_workflow3_codex_update" "$VENV_DIR/bin/jleechanorg-pr-monitor" \
  --no-act \
  --codex-update \
  --codex-task-limit "$CODEX_TASK_LIMIT"
write_sha256 "${ART_DIR}/cron_workflow3_codex_update.out.txt"
write_sha256 "${ART_DIR}/cron_workflow3_codex_update.err.txt"
write_sha256 "${ART_DIR}/cron_workflow3_codex_update.meta.json"

# Targeted workflow gating (shows workflow-specific limit checks without touching multiple PRs).
run_and_capture "target_pr_pr_automation_no_act" "$VENV_DIR/bin/jleechanorg-pr-monitor" \
  --no-act \
  --target-pr "$TARGET_PR" \
  --target-repo "$TARGET_REPO" \
  --pr-automation-limit "$PR_AUTOMATION_LIMIT" \
  --fix-comment-limit "$FIX_COMMENT_LIMIT" \
  --fixpr-limit "$FIXPR_LIMIT"
write_sha256 "${ART_DIR}/target_pr_pr_automation_no_act.out.txt"
write_sha256 "${ART_DIR}/target_pr_pr_automation_no_act.err.txt"
write_sha256 "${ART_DIR}/target_pr_pr_automation_no_act.meta.json"

run_and_capture "target_pr_fix_comment_no_act" "$VENV_DIR/bin/jleechanorg-pr-monitor" \
  --no-act \
  --fix-comment \
  --target-pr "$TARGET_PR" \
  --target-repo "$TARGET_REPO" \
  --cli-agent gemini \
  --pr-automation-limit "$PR_AUTOMATION_LIMIT" \
  --fix-comment-limit "$FIX_COMMENT_LIMIT" \
  --fixpr-limit "$FIXPR_LIMIT"
write_sha256 "${ART_DIR}/target_pr_fix_comment_no_act.out.txt"
write_sha256 "${ART_DIR}/target_pr_fix_comment_no_act.err.txt"
write_sha256 "${ART_DIR}/target_pr_fix_comment_no_act.meta.json"

run_and_capture "target_pr_fixpr_no_act" "$VENV_DIR/bin/jleechanorg-pr-monitor" \
  --no-act \
  --fixpr \
  --target-pr "$TARGET_PR" \
  --target-repo "$TARGET_REPO" \
  --cli-agent gemini \
  --pr-automation-limit "$PR_AUTOMATION_LIMIT" \
  --fix-comment-limit "$FIX_COMMENT_LIMIT" \
  --fixpr-limit "$FIXPR_LIMIT"
write_sha256 "${ART_DIR}/target_pr_fixpr_no_act.out.txt"
write_sha256 "${ART_DIR}/target_pr_fixpr_no_act.err.txt"
write_sha256 "${ART_DIR}/target_pr_fixpr_no_act.meta.json"

echo "Evidence written to: ${OUT_DIR}"
