#!/usr/bin/env bash
set -euo pipefail
umask 077

# Ensure /opt/homebrew/bin is in PATH if it exists (for Homebrew GNU rsync, flock, etc.)
if [[ -d /opt/homebrew/bin ]]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MACHINE_NAME="${MACHINE_NAME:-$(hostname -s 2>/dev/null || hostname)}"
GIT_BACKUP_ROOT="${GIT_BACKUP_ROOT:-$REPO_ROOT/backup/$MACHINE_NAME}"
if [[ "$(uname -s)" == "Darwin" ]]; then
  _dropbox_default="$HOME/Library/CloudStorage/Dropbox"
else
  _dropbox_default="$HOME/Dropbox"
fi
DROPBOX_BASE_DIR="${DROPBOX_BASE_DIR:-$_dropbox_default}"
DROPBOX_TARGET="${DROPBOX_BASE_DIR}/${DROPBOX_BACKUP_SUBDIR:-conversation-backups}"
unset _dropbox_default
DRY_RUN=0
ALLOW_GIT_BACKUP_PUSH="${ALLOW_GIT_BACKUP_PUSH:-0}"
ALLOW_GIT_BACKUP_SYNC="${ALLOW_GIT_BACKUP_SYNC:-$ALLOW_GIT_BACKUP_PUSH}"
TOKEN_HEALTH_PRECHECK="${TOKEN_HEALTH_PRECHECK:-0}"
TOKEN_HEALTH_PRECHECK_FAIL_ON_FAILURE="${TOKEN_HEALTH_PRECHECK_FAIL_ON_FAILURE:-1}"
REQUIRE_DROPBOX_ONLY="${REQUIRE_DROPBOX_ONLY:-1}"
GIT_BACKUP_PUSH_REMOTE="${GIT_BACKUP_PUSH_REMOTE:-origin}"
GIT_BACKUP_PUSH_BRANCH="${GIT_BACKUP_PUSH_BRANCH:-main}"
GIT_BACKUP_ALLOWED_REMOTE_HTTPS="https://github.com/jleechanorg/claude-commands.git"
GIT_BACKUP_ALLOWED_REMOTE_SSH="git@github.com:jleechanorg/claude-commands.git"
CODEX_SESSIONS_EXCLUDE_PATTERNS="${CODEX_SESSIONS_EXCLUDE_PATTERNS:-sessions_archive/}"
OPENCLAW_BACKUP_DIR="${OPENCLAW_BACKUP_DIR:-$HOME/.openclaw}"
OPENCLAW_CONVO_DIR="${OPENCLAW_CONVO_DIR:-}"
if [[ -n "$OPENCLAW_CONVO_DIR" ]]; then
  OPENCLAW_BACKUP_DIR="$OPENCLAW_CONVO_DIR"
fi
OPENCLAW_GIT_EXCLUDE_PATTERNS="${OPENCLAW_GIT_EXCLUDE_PATTERNS:-agents/,jleechanclaw/,agf-api/,agf-lambda/,workspace/,src/tests/,agents/*/agent/auth-profiles.json,agents/*/agent/auth-profiles.json.lock,agents/*/agent/auth.json,memory/,media/,browser/,identity/,credentials/,logs/,*.log,openclaw.json,openclaw.json.bak,openclaw.json.bak*,exec-approvals.json,*gateway*.txt,extensions/*/node_modules/,*.git/,.env,.env.*,*.env,*tctoken*,*token*.json,*token*.txt,*token*.yaml,*token*.yml,*token*.env,*credential*.json,*service-account*.json,*service_account*.json,*secret*.json,*secret*,*password*,*.key,*.pem,*.p12,*.jwk,*.crt,*.der,*.pfx,*.sqlite,*.sqlite-shm,*.sqlite-wal,*.db,*.db-shm,*.db-wal,set-slack-env.sh,slack-app-manifest.json,slack-app-manifest.yaml,thread_ack_ledger.json,update-check.json,qdrant_storage/,hermes-agent/venv/}"
OPENCLAW_CONVO_EXCLUDE_PATTERNS="${OPENCLAW_CONVO_EXCLUDE_PATTERNS:-agents/,jleechanclaw/,qdrant_storage/,extensions/,logs/,browser/,memory/}"
OPENCODE_CONVO_EXCLUDE_PATTERNS="${OPENCLAW_CONVO_EXCLUDE_PATTERNS}"
OPENCODE_DATA_DIR="${OPENCODE_DATA_DIR:-$HOME/.local/share/opencode}"
# OpenCode conversation data — backed up to Dropbox only (large SQLite + binary data not suitable for git)
OPENCODE_GIT_EXCLUDE_PATTERNS="${OPENCODE_GIT_EXCLUDE_PATTERNS:-auth.json,opencode.db,opencode.db-shm,opencode.db-wal,snapshot/,tool-output/,log/,bin/}"
BACKUP_REPORT_FILE="${BACKUP_REPORT_FILE:-$HOME/Library/Logs/home-backup.latest.report.txt}"
REPORT_WRITE_FILE="$BACKUP_REPORT_FILE"
BACKUP_REPORT_TEMP_FILE=""
SECURE_TEMP="$(mktemp -d)"

cleanup() {
  if [[ -n "$BACKUP_REPORT_TEMP_FILE" && -f "$BACKUP_REPORT_TEMP_FILE" ]]; then
    rm -f "$BACKUP_REPORT_TEMP_FILE"
  fi
  rm -rf "$SECURE_TEMP"
}
trap cleanup EXIT

run_token_healthcheck() {
  if [[ "$TOKEN_HEALTH_PRECHECK" != "1" ]]; then
    return 0
  fi

  local check_script="$SCRIPT_DIR/check-bashrc-token-health.sh"
  local result_file="$SECURE_TEMP/token_healthcheck.log"
  local check_status=0

  if [[ ! -x "$check_script" ]]; then
    log "Token health check skipped: missing $check_script"
    return 0
  fi

  if "$check_script" >"$result_file" 2>&1; then
    log "Token health check passed"
    while IFS= read -r line; do
      log "token-health: $line"
    done <"$result_file"
  else
    check_status=1
    log "Token health check reported failures."
    while IFS= read -r line; do
      log "token-health: $line"
    done <"$result_file"
  fi

  if [[ "$check_status" -ne 0 && "$TOKEN_HEALTH_PRECHECK_FAIL_ON_FAILURE" == "1" ]]; then
    log "Token health check failure policy active: aborting backup"
    return 1
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run]

Backs up Codex/Claude/OpenClaw home data from ~ into repo-local Git backup
and Dropbox in parallel.

Default safety mode is Dropbox-only:
- ALLOW_GIT_BACKUP_SYNC=0 (skip Git backup snapshot copy entirely)
- ALLOW_GIT_BACKUP_PUSH=0 (skip Git snapshot push even if sync runs)

Set ALLOW_GIT_BACKUP_SYNC=1 to allow local git-target snapshots and
set ALLOW_GIT_BACKUP_PUSH=1 only when you explicitly want a guarded push.
Set REQUIRE_DROPBOX_ONLY=1 (default) to force both git snapshot flags off unless
you explicitly opt out with REQUIRE_DROPBOX_ONLY=0.
Set TOKEN_HEALTH_PRECHECK=1 to run token liveness smoke checks on each run.
Set TOKEN_HEALTH_PRECHECK_FAIL_ON_FAILURE=1 (default) to fail backup when checks fail.

Git snapshot push is disabled by default.
Set ALLOW_GIT_BACKUP_PUSH=1 (explicit opt-in) to permit snapshots to push.
Default behavior is Dropbox-only.
EOF
}

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

log() { echo "[$(date +%F' '%T)] $*"; }

if [[ "$REQUIRE_DROPBOX_ONLY" == "1" ]]; then
  if [[ "$ALLOW_GIT_BACKUP_SYNC" != "0" || "$ALLOW_GIT_BACKUP_PUSH" != "0" ]]; then
    log "Dropbox-only guard active (REQUIRE_DROPBOX_ONLY=1): forcing ALLOW_GIT_BACKUP_SYNC=0 and ALLOW_GIT_BACKUP_PUSH=0"
  fi
  ALLOW_GIT_BACKUP_SYNC=0
  ALLOW_GIT_BACKUP_PUSH=0
fi

run_token_healthcheck

# Lock configuration to prevent concurrent overlapping runs
LOCK_FILE="/var/tmp/backup-home.lock"
# Ensure the lock file exists
touch "$LOCK_FILE"
exec 9>>"$LOCK_FILE"

if ! flock -n 9; then
  log "Backup already in progress (locked via $LOCK_FILE)."
  if [[ -f "$LOCK_FILE" ]]; then
    other_pid=$(cat "$LOCK_FILE" 2>/dev/null || true)
    if [[ -n "$other_pid" ]] && kill -0 "$other_pid" 2>/dev/null; then
      log "Active backup instance PID: $other_pid"
      if [[ "$(uname -s)" == "Darwin" ]]; then
        elapsed=$(ps -p "$other_pid" -o etime= 2>/dev/null | tr -d '[:space:]' || true)
        if [[ -n "$elapsed" ]]; then
          log "Active backup elapsed time: $elapsed"
          if [[ "$elapsed" == *-* ]]; then
            log "WARNING: Active backup has been running for days ($elapsed). This is likely a stale/stuck run."
          elif [[ "$elapsed" =~ ^([0-9]{2,}): ]]; then
            hours="${BASH_REMATCH[1]}"
            if [[ "$hours" -ge 12 ]]; then
              log "WARNING: Active backup has been running for $hours hours ($elapsed). This is likely a stale/stuck run."
            fi
          fi
        fi
      fi
    else
      log "Lock file contains inactive PID or is empty. flock is active but process is not found."
    fi
  fi
  exit 0
fi

# We have the lock. Write our PID to the lock file.
if [[ "$DRY_RUN" -eq 0 ]]; then
  true > "$LOCK_FILE"
  echo "$$" >&9
fi

append_backup_report() {
  local line="$1"
  mkdir -p "$(dirname "$REPORT_WRITE_FILE")"
  printf '%s\n' "$line" >> "$REPORT_WRITE_FILE"
}

finalize_backup_report() {
  if [[ "$DRY_RUN" -eq 1 || -z "$BACKUP_REPORT_TEMP_FILE" ]]; then
    return 0
  fi
  mv "$BACKUP_REPORT_TEMP_FILE" "$BACKUP_REPORT_FILE"
  BACKUP_REPORT_TEMP_FILE=""
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

require_snapshot_push_target() {
  local work_dir="$1"
  local remote="$2"
  local branch="$3"

  if ! git -C "$work_dir" remote get-url "$remote" >/dev/null 2>&1; then
    log "ERROR: snapshot push blocked — remote '$remote' is not configured"
    return 1
  fi

  local remote_url
  remote_url="$(git -C "$work_dir" remote get-url "$remote")"
  if [[ "$remote_url" != "$GIT_BACKUP_ALLOWED_REMOTE_HTTPS" && "$remote_url" != "$GIT_BACKUP_ALLOWED_REMOTE_SSH" ]]; then
    log "ERROR: snapshot push blocked — remote '$remote_url' is not an allowed repository"
    return 1
  fi

  if ! git -C "$work_dir" rev-parse --verify --quiet "$branch" >/dev/null; then
    log "ERROR: snapshot push blocked — branch '$branch' is missing locally"
    return 1
  fi

  return 0
}

validate_path() {
  local path="$1"
  local context="$2"

  if [[ "$path" =~ (^|/)\.\.(/|$) ]]; then
    echo "Invalid path for $context: $path" >&2
    exit 2
  fi
}

ensure_parent_dir() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
}

append_csv_pattern() {
  local csv="${1:-}"
  local pattern="${2:-}"
  if [[ -z "$pattern" ]]; then
    printf "%s" "$csv"
    return
  fi
  if [[ -z "$csv" ]]; then
    printf "%s" "$pattern"
  else
    printf "%s,%s" "$csv" "$pattern"
  fi
}

run_rsync_copy() {
  local src="$1"
  local dst="$2"
  local target_name="$3"
  local exclude_csv="${4:-}"
  local sync_mode="${5:-additive}"
  local rsync_stderr_file
  local rsync_stdout_file
  local rsync_exit=0
  local rsync_args=()
  local rsync_count=0
  local exclude_item=""
  local -a exclude_items=()
  local rsync_line=""

  if [[ ! -e "$src" ]]; then
    log "[$target_name] SKIP missing: $src"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[$target_name] DRY-RUN copy: $src -> $dst"
    if [[ -f "$src" && ! -d "$(dirname "$dst")" ]]; then
      log "[$target_name]   [>f+++++++++] $(basename "$dst")"
      log "[$target_name] DRY-RUN would change 1 item(s): $src -> $dst"
      return 0
    fi

    rsync_args=(-a --itemize-changes --out-format='[%i] %n%L' --exclude='.git' --exclude='*.lock' --exclude='*.tmp')
    if [[ "$sync_mode" == "additive" ]]; then
      rsync_args+=(--ignore-existing)
    fi

    if [[ -n "$exclude_csv" ]]; then
      IFS=',' read -r -a exclude_items <<< "$exclude_csv"
      for exclude_item in "${exclude_items[@]}"; do
        rsync_args+=("--exclude=$exclude_item")
      done
    fi

    rsync_args+=(--dry-run)

    rsync_stderr_file="$(mktemp "$SECURE_TEMP/rsync_dry_XXXXXXXX")"
    rsync_stdout_file="$(mktemp "$SECURE_TEMP/rsync_dry_XXXXXXXX")"
    set +e
    rsync "${rsync_args[@]}" "$src" "$dst" >"$rsync_stdout_file" 2>"$rsync_stderr_file"
    rsync_exit=$?
    set -e

    if [[ "$rsync_exit" -ne 0 ]]; then
      if [[ "$rsync_exit" -eq 23 || "$rsync_exit" -eq 24 ]] && \
        grep -Eqi "No such file or directory|vanished|open \(2\)" "$rsync_stderr_file"; then
        log "[$target_name] DRY-RUN copy: transient source churn while scanning $src -> $dst"
      else
        log "[$target_name] DRY-RUN copy failed while scanning: $src -> $dst (exit $rsync_exit)"
        tail -n 1 "$rsync_stderr_file" >&2 || true
        return 1
      fi
    fi

    if [[ -s "$rsync_stdout_file" ]]; then
      while IFS= read -r rsync_line; do
        [[ -z "$rsync_line" ]] && continue
        ((rsync_count += 1))
        log "[$target_name]   $rsync_line"
      done <"$rsync_stdout_file"
      log "[$target_name] DRY-RUN would change $rsync_count item(s): $src -> $dst"
    else
      log "[$target_name] DRY-RUN no changes: $src -> $dst"
    fi

    return 0
  fi

  ensure_parent_dir "$dst"
  rsync_stderr_file="$(mktemp "$SECURE_TEMP/rsync_XXXXXXXX")"
  rsync_stdout_file="$(mktemp "$SECURE_TEMP/rsync_XXXXXXXX")"
  rsync_args=(-a --itemize-changes --exclude='.git' --exclude='*.lock' --exclude='*.tmp')
  if [[ "$sync_mode" == "additive" ]]; then
    rsync_args+=(--ignore-existing)
  fi

  if [[ -n "$exclude_csv" ]]; then
    IFS=',' read -r -a exclude_items <<< "$exclude_csv"
    for exclude_item in "${exclude_items[@]}"; do
      rsync_args+=("--exclude=$exclude_item")
    done
  fi

  set +e
  rsync "${rsync_args[@]}" "$src" "$dst" >"$rsync_stdout_file" 2>"$rsync_stderr_file"
  rsync_exit=$?
  set -e

  if [[ "$rsync_exit" -eq 0 ]]; then
    while IFS= read -r rsync_line; do
      [[ -z "$rsync_line" ]] && continue
      ((rsync_count += 1))
      if [[ "$DRY_RUN" -eq 0 ]]; then
        append_backup_report "${target_name}|${src}|${dst}|${rsync_line}"
      fi
    done <"$rsync_stdout_file"

    if [[ "$rsync_count" -gt 0 ]]; then
      log "[$target_name] COPIED ($rsync_count new): $src -> $dst"
    else
      log "[$target_name] UP-TO-DATE: $src -> $dst"
    fi
    return 0
  fi

  if [[ "$rsync_exit" -eq 23 || "$rsync_exit" -eq 24 ]] && \
    grep -Eqi "No such file or directory|vanished|open \\(2\\)" "$rsync_stderr_file"; then
    log "[$target_name] WARN transient source churn while copying: $src -> $dst (rsync exit $rsync_exit)"
    return 0
  fi

  # Surface exit 10/11 with the destination's free space so the launchd report
  # shows whether disk pressure is the cause. (It usually isn't — see git
  # history: 2026-06-13 these errors were caused by --inplace deadlocking on
  # the Dropbox FUSE mount, not by disk-full. That flag has been removed, but
  # the free-space printout is still useful for diagnosing future failures.)
  if [[ "$rsync_exit" -eq 10 || "$rsync_exit" -eq 11 ]]; then
    local _avail_kb
    _avail_kb="$(df -k "$dst" 2>/dev/null | awk 'NR==2 {print $4}')"
    log "[$target_name] ERROR rsync failed: $src -> $dst (exit $rsync_exit) (dest has ${_avail_kb:-unknown}KB free)"
    tail -n 1 "$rsync_stderr_file" >&2 || true
    return 1
  fi

  # macOS openrsync bug: --itemize-changes on directory-to-directory copies to
  # CloudStorage volumes fails with "unexpected end of file". Retry without format
  # flags, which still copies correctly but loses per-file change logging.
  if grep -qi "unexpected end of file" "$rsync_stderr_file"; then
    log "[$target_name] WARN openrsync format-flag bug detected; retrying without --itemize-changes: $src -> $dst"
    rsync_args=(-a --exclude='.git' --exclude='*.lock' --exclude='*.tmp')
    if [[ "$sync_mode" == "additive" ]]; then
      rsync_args+=(--ignore-existing)
    fi
    if [[ -n "$exclude_csv" ]]; then
      IFS=',' read -r -a exclude_items <<< "$exclude_csv"
      for exclude_item in "${exclude_items[@]}"; do
        rsync_args+=("--exclude=$exclude_item")
      done
    fi
    set +e
    rsync "${rsync_args[@]}" "$src" "$dst" >"$rsync_stdout_file" 2>"$rsync_stderr_file"
    rsync_exit=$?
    set -e
    if [[ "$rsync_exit" -eq 0 ]]; then
      log "[$target_name] COPIED (count unavailable, openrsync fallback): $src -> $dst"
      return 0
    fi
    log "[$target_name] ERROR rsync fallback also failed: $src -> $dst (exit $rsync_exit)"
    tail -n 1 "$rsync_stderr_file" >&2 || true
    return 1
  fi

  log "[$target_name] ERROR rsync failed: $src -> $dst (exit $rsync_exit)"
  tail -n 1 "$rsync_stderr_file" >&2 || true
  return 1
}

run_rsync_markdown_copy() {
  local src="$1"
  local dst="$2"
  local target_name="$3"
  local sync_mode="${4:-additive}"
  local rsync_stderr_file
  local rsync_stdout_file
  local rsync_exit=0
  local rsync_count=0
  local rsync_line=""
  local rsync_args=()

  if [[ ! -e "$src" ]]; then
    log "[$target_name] SKIP missing: $src"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[$target_name] DRY-RUN markdown copy: $src -> $dst"
    rsync_args=(-a --prune-empty-dirs --itemize-changes --out-format='[%i] %n%L' --exclude='*.lock' --exclude='*.tmp')
    if [[ "$sync_mode" == "additive" ]]; then
      rsync_args+=(--ignore-existing)
    fi
    rsync_args+=(--include='*/' --include='*.md' --exclude='*' --dry-run)

    rsync_stderr_file="$(mktemp "$SECURE_TEMP/rsync_md_dry_XXXXXXXX")"
    rsync_stdout_file="$(mktemp "$SECURE_TEMP/rsync_md_dry_XXXXXXXX")"
    set +e
    rsync "${rsync_args[@]}" "$src" "$dst" >"$rsync_stdout_file" 2>"$rsync_stderr_file"
    rsync_exit=$?
    set -e

    if [[ "$rsync_exit" -ne 0 ]]; then
      if [[ "$rsync_exit" -eq 23 || "$rsync_exit" -eq 24 ]] && \
        grep -Eqi "No such file or directory|vanished|open \(2\)" "$rsync_stderr_file"; then
        log "[$target_name] DRY-RUN markdown copy: transient source churn while scanning $src -> $dst"
      else
        log "[$target_name] DRY-RUN markdown copy failed while scanning: $src -> $dst (exit $rsync_exit)"
        tail -n 1 "$rsync_stderr_file" >&2 || true
        return 1
      fi
    fi

    if [[ -s "$rsync_stdout_file" ]]; then
      while IFS= read -r rsync_line; do
        [[ -z "$rsync_line" ]] && continue
        ((rsync_count += 1))
        log "[$target_name]   $rsync_line"
      done <"$rsync_stdout_file"
      log "[$target_name] DRY-RUN markdown copy would change $rsync_count item(s): $src -> $dst"
    else
      log "[$target_name] DRY-RUN markdown copy no changes: $src -> $dst"
    fi
    return 0
  fi

  ensure_parent_dir "$dst"
  rsync_stderr_file="$(mktemp "$SECURE_TEMP/rsync_md_XXXXXXXX")"
  rsync_stdout_file="$(mktemp "$SECURE_TEMP/rsync_md_XXXXXXXX")"
  rsync_args=(-a --prune-empty-dirs --itemize-changes --out-format='[%i] %n%L' --exclude='*.lock' --exclude='*.tmp')
  if [[ "$sync_mode" == "additive" ]]; then
    rsync_args+=(--ignore-existing)
  fi
  rsync_args+=(--include='*/' --include='*.md' --exclude='*')

  set +e
  rsync "${rsync_args[@]}" "$src" "$dst" >"$rsync_stdout_file" 2>"$rsync_stderr_file"
  rsync_exit=$?
  set -e

  if [[ "$rsync_exit" -eq 0 ]]; then
    while IFS= read -r rsync_line; do
      [[ -z "$rsync_line" ]] && continue
      ((rsync_count += 1))
      if [[ "$DRY_RUN" -eq 0 ]]; then
        append_backup_report "${target_name}|${src}|${dst}|${rsync_line}"
      fi
    done <"$rsync_stdout_file"

    if [[ "$rsync_count" -gt 0 ]]; then
      log "[$target_name] COPIED markdown ($rsync_count changes): $src -> $dst"
    else
      log "[$target_name] UP-TO-DATE markdown: $src -> $dst"
    fi
    return 0
  fi

  if [[ "$rsync_exit" -eq 23 || "$rsync_exit" -eq 24 ]] && \
    grep -Eqi "No such file or directory|vanished|open \\(2\\)" "$rsync_stderr_file"; then
    log "[$target_name] WARN transient source churn while markdown copying: $src -> $dst (rsync exit $rsync_exit)"
    return 0
  fi

  log "[$target_name] ERROR rsync markdown copy failed: $src -> $dst (exit $rsync_exit)"
  tail -n 1 "$rsync_stderr_file" >&2 || true
  return 1
}


backup_codex_sqlite() {
  local target_name="$1"
  local target_root="$2"
  local src_db="$HOME/.codex/state_5.sqlite"
  local dst_db="$target_root/$3"
  local sync_mode="${4:-additive}"
  local dst_dir=""
  local tmp_db=""

  if [[ ! -f "$src_db" ]]; then
    log "[$target_name] SKIP missing: $src_db"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[$target_name] DRY-RUN sqlite backup: $src_db -> $dst_db"
    return 0
  fi

  dst_dir="$(dirname "$dst_db")"
  ensure_parent_dir "$dst_db"

  if command -v sqlite3 >/dev/null 2>&1; then
    if [[ "$sync_mode" == "additive" && -f "$dst_db" ]]; then
      log "[$target_name] SKIP existing sqlite: $dst_db"
      return 0
    fi
    tmp_db="$(mktemp "$SECURE_TEMP/sqlite_XXXXXXXX")"
    if sqlite3 "$src_db" ".timeout 5000" ".backup '$tmp_db'" 2>/dev/null; then
      if [[ "$sync_mode" == "additive" && -f "$dst_db" ]]; then
        log "[$target_name] SKIP existing sqlite: $dst_db"
        rm -f "$tmp_db"
      else
        mv "$tmp_db" "$dst_db"
        log "[$target_name] COPIED (sqlite backup): $src_db -> $dst_db"
      fi
      return 0
    fi
    rm -f "$tmp_db"
    log "[$target_name] WARN sqlite3 backup failed, falling back to rsync copies"
  fi

  run_rsync_copy "$src_db" "$dst_db" "$target_name" "" "$sync_mode" || return 1
  run_rsync_copy "$HOME/.codex/state_5.sqlite-wal" "$dst_dir/state_5.sqlite-wal" "$target_name" "" "$sync_mode" || return 1
  run_rsync_copy "$HOME/.codex/state_5.sqlite-shm" "$dst_dir/state_5.sqlite-shm" "$target_name" "" "$sync_mode" || return 1
}

backup_antigravity_conversations() {
  local target_name="$1"
  local target_root="$2"
  local sync_mode="${3:-sync}"

  local ls_pid
  ls_pid="$(pgrep -f "language_server" 2>/dev/null | head -1)"
  if [[ -z "$ls_pid" ]]; then
    log "[$target_name] SKIP: Antigravity not running"
    return 0
  fi

  local csrf_token
  csrf_token="$(ps -p "$ls_pid" -o args= 2>/dev/null | awk '/--csrf_token/ {for(i=1;i<=NF;i++) if($i=="--csrf_token") print $(i+1)}')"
  if [[ -z "$csrf_token" ]]; then
    log "[$target_name] SKIP: could not extract CSRF token"
    return 0
  fi

  local python_path
  if [[ -d "$HOME/.local/orch-venv/lib/python3.13/site-packages" ]]; then
    python_path="$HOME/.local/orch-venv/bin/python3"
  else
    python_path="python3"
  fi

  local output_dir="$target_root/antigravity/"
  ensure_parent_dir "$output_dir"

  log "[$target_name] Exporting Antigravity conversations (port discovery)"

  local export_result
  export_result="$("$python_path" -c "
import json, os, sys, subprocess, re

ls_pid = '$ls_pid'
csrf = '$csrf_token'

result = subprocess.run(['lsof', '-p', ls_pid, '-iTCP', '-sTCP:LISTEN', '-P', '-n'], capture_output=True, text=True)
ports = []
for line in result.stdout.split('\n'):
    m = re.search(r':(\d+)\s+\(LISTEN\)', line)
    if m:
        ports.append(int(m.group(1)))

trajectories = {}
working_port = None
for port in sorted(set(ports)):
    try:
        import urllib.request
        import ssl
        data = json.dumps({}).encode()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            f'https://localhost:{port}/exa.language_server_pb.LanguageServerService/GetAllCascadeTrajectories',
            data=data,
            headers={'Content-Type': 'application/json', 'Connect-Protocol-Version': '1', 'X-Codeium-Csrf-Token': csrf}
        )
        resp = urllib.request.urlopen(req, timeout=5, context=ctx)
        result = json.loads(resp.read())
        convs = result.get('trajectorySummaries', {})
        if convs:
            trajectories = convs
            working_port = port
            break
    except:
        continue

if not trajectories:
    print('NO_CONVERSATIONS')
    sys.exit(0)

try:
    from antigravity_history.api import get_trajectory_steps
    from antigravity_history.parser import parse_steps, FieldLevel
    from antigravity_history.formatters import format_markdown, write_conversation
except ImportError as e:
    print(f'LIBRARY_MISSING:{e}')
    sys.exit(0)

exported = 0
for cid, info in sorted(trajectories.items(), key=lambda x: x[1].get('stepCount', 0), reverse=True)[:50]:
    try:
        steps = get_trajectory_steps(working_port, csrf, cid, step_count=10000)
        messages = parse_steps(steps, level=FieldLevel.THINKING)
        md = format_markdown(info.get('summary', 'Untitled'), cid, info, messages)
        safe_title = re.sub(r'[^\w\s\-]', '_', info.get('summary', 'Untitled'))[:60].strip()
        filepath = os.path.join('$output_dir', safe_title + '.md')
        counter = 2
        while os.path.exists(filepath) and counter < 100:
            filepath = os.path.join('$output_dir', f'{safe_title}_{counter}.md')
            counter += 1
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)
        exported += 1
    except Exception as e:
        print(f'ERR:{cid[:8]}:{str(e)[:50]}', file=sys.stderr)

print(f'EXPORTED:{exported}')
" 2>&1)"

  if echo "$export_result" | grep -q "NO_CONVERSATIONS"; then
    log "[$target_name] No conversations to export"
    return 0
  fi

  if echo "$export_result" | grep -q "LIBRARY_MISSING"; then
    log "[$target_name] SKIP: antigravity-history library not installed"
    return 0
  fi

  local exported_count
  exported_count="$(echo "$export_result" | grep "EXPORTED:" | cut -d: -f2)"
  if [[ -n "$exported_count" && "$exported_count" != "0" ]]; then
    log "[$target_name] Exported $exported_count Antigravity conversations"
    return 0
  fi

  log "[$target_name] Antigravity: $export_result"
  return 0
}

backup_item() {
  local target_name="$1"
  local target_root="$2"
  local mode="$3"
  local src="$4"
  local rel="$5"
  local exclude_csv="${6:-}"
  local sync_mode="${7:-additive}"

  case "$mode" in
    copy)
      run_rsync_copy "$src" "$target_root/$rel" "$target_name" "$exclude_csv" "$sync_mode"
      ;;
    copy_md)
      run_rsync_markdown_copy "$src" "$target_root/$rel" "$target_name" "$sync_mode"
      ;;
    sqlite)
      backup_codex_sqlite "$target_name" "$target_root" "$rel" "$sync_mode"
      ;;
    *)
      echo "Unknown backup mode: $mode" >&2
      exit 2
      ;;
  esac
}

write_target_metadata() {
  local target_name="$1"
  local target_root="$2"
  local metadata_path="$target_root/backup_metadata.txt"

  if [[ "$target_name" == "dropbox" ]]; then
    metadata_path="$target_root/home_backup_metadata.txt"
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[$target_name] DRY-RUN metadata: $metadata_path"
    return 0
  fi

  local tmp_meta
  tmp_meta="$(mktemp "$SECURE_TEMP/meta_XXXXXXXX")"
  printf 'timestamp_utc=%s\ntarget_name=%s\ntarget_root=%s\nmode=rsync-no-delete\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$target_name" "$target_root" > "$tmp_meta"
  mv "$tmp_meta" "$metadata_path"
}

run_target_job() {
  local target_name="$1"
  local target_root="$2"
  local rel_field="$3"
  local result_file="$4"
  local item=""
  local status="SUCCESS"
  local mode=""
  local src=""
  local git_rel=""
  local dropbox_rel=""
  local exclude_csv=""
  local sync_mode=""
  local rel=""
  local effective_exclude_csv=""
  local src_base=""
  local target_base=""
  local dst_path=""
  local rel_norm=""
  local relative_target=""
  local relative_target_top=""
  local relative_dst=""

  (
    trap - EXIT
    SECURE_TEMP="$(mktemp -d "$SECURE_TEMP/job_XXXXXXXX")"
    trap 'rm -rf "$SECURE_TEMP"' EXIT
    if [[ "$DRY_RUN" -eq 0 ]]; then
      mkdir -p "$target_root"
      chmod 700 "$target_root" 2>/dev/null || true
    fi

    log "[$target_name] Starting target backup at $target_root"

    local item_pids=()
    local item_failed=0
    local item_succeeded=0
    for item in "${BACKUP_ITEMS[@]}"; do
      IFS='|' read -r mode src git_rel dropbox_rel exclude_csv sync_mode <<< "$item"
      if [[ "$rel_field" == "git" ]]; then
        rel="$git_rel"
      else
        rel="$dropbox_rel"
      fi
      [[ -z "$rel" ]] && continue

      effective_exclude_csv="$exclude_csv"
      src_base="${src%/}"
      target_base="${target_root%/}"
      rel_norm="${rel#/}"
      dst_path="${target_base}/${rel_norm%/}"

      if [[ "$target_base" == "$src_base" || "$target_base" == "$src_base/"* ]]; then
        relative_target="${target_base#"$src_base"/}"
        if [[ -n "$relative_target" && "$relative_target" != "$target_base" ]]; then
          effective_exclude_csv="$(append_csv_pattern "$effective_exclude_csv" "${relative_target%/}/")"
          relative_target_top="${relative_target%%/*}"
          if [[ -n "$relative_target_top" && "$relative_target_top" != "$relative_target" ]]; then
            effective_exclude_csv="$(append_csv_pattern "$effective_exclude_csv" "${relative_target_top%/}/")"
          fi
        fi
      fi

      if [[ "$dst_path" == "$src_base" || "$dst_path" == "$src_base/"* ]]; then
        relative_dst="${dst_path#"$src_base"/}"
        if [[ -n "$relative_dst" && "$relative_dst" != "$dst_path" ]]; then
          # Avoid copying the destination back into the source tree.
          effective_exclude_csv="$(append_csv_pattern "$effective_exclude_csv" "${relative_dst%/}/")"
        fi
      fi

      backup_item "$target_name" "$target_root" "$mode" "$src" "$rel" "$effective_exclude_csv" "${sync_mode:-additive}" &
      item_pids+=($!)
    done

    # Wait for all item jobs. `run_rsync_copy` already absorbs transient
    # errors (rsync exit 23/24 with vanished-source, or openrsync's
    # "unexpected end of file" fallback) by returning 0. Anything that
    # returns non-zero from `wait` is therefore a real failure that
    # should poison the target status. This preserves the original
    # behaviour: the script does not silently swallow real errors.
    for pid in "${item_pids[@]}"; do
      if ! wait "$pid"; then
        item_failed=$((item_failed + 1))
        status="FAILED"
      else
        item_succeeded=$((item_succeeded + 1))
      fi
    done
    if [[ "$item_failed" -gt 0 ]]; then
      log "[$target_name] $item_failed item(s) failed (real error after transient-absorb at rsync level)"
    fi

    # Antigravity conversations require running IDE + API calls (Dropbox only)
    if [[ "$target_name" == "dropbox" ]]; then
      if ! backup_antigravity_conversations "$target_name" "$target_root" "sync"; then
        status="FAILED"
      fi
    fi

    if ! write_target_metadata "$target_name" "$target_root"; then
      status="FAILED"
    fi

    printf "%s\n" "$status" > "$result_file"
    log "[$target_name] Target backup complete with status: $status"
  ) &

  RUN_TARGET_JOB_PID=$!
}

require_cmd rsync
validate_path "$DROPBOX_BASE_DIR" "DROPBOX_BASE_DIR"

log "Starting home backup (git_root=$GIT_BACKUP_ROOT, dropbox_base=$DROPBOX_BASE_DIR, dry_run=$DRY_RUN)"
if [[ "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$(dirname "$BACKUP_REPORT_FILE")"
  BACKUP_REPORT_TEMP_FILE="$(mktemp "${BACKUP_REPORT_FILE}.tmp.XXXXXX")"
  REPORT_WRITE_FILE="$BACKUP_REPORT_TEMP_FILE"
  append_backup_report "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  append_backup_report "machine=$MACHINE_NAME"
  append_backup_report "git_root=$GIT_BACKUP_ROOT"
  append_backup_report "dropbox_target=$DROPBOX_TARGET"
fi

# Format: mode|src|git_rel|dropbox_rel|exclude_csv|sync_mode
# OpenClaw backups are split per target:
# - git target receives filtered data with explicit sensitive-file exclusions.
# - dropbox target receives filtered data excluding large runtime trees.
# Config files (agents, hooks, codex config) go to both git and Dropbox.
BACKUP_ITEMS=(
  "copy|$HOME/.codex/history.jsonl||codex_conversations/history.jsonl||sync"
  "copy|$HOME/.codex/sessions/||codex_conversations/sessions/|${CODEX_SESSIONS_EXCLUDE_PATTERNS}|sync"
  "copy|$HOME/.codex/archived_sessions/||codex_conversations/archived_sessions/||sync"
  "sqlite|$HOME/.codex/state_5.sqlite||codex_conversations/state_5.sqlite||sync"
  "copy|$HOME/.claude/history.jsonl||claude_conversations/history.jsonl||sync"
  "copy|$HOME/.claude/sessions/||claude_conversations/sessions/||sync"
  "copy|$HOME/.claude/projects/||claude_conversations/projects/||sync"
  # ~/.claude-agent-f/ — alternate Claude Code profile for `claudeaf()` / Agnt-F work.
  # DROPPED-ONLY on 2026-06-29 per /Users/jleechan/.claude/hooks/block-agentf-push-to-jleechanorg.sh.
  # Empty git_rel so the jleechanorg push-hook never sees agent-f string content.
  # Mirrors the `~/.claude/sessions/` (line 744) 4-tuple pattern. Local backup runs
  # immediately via the existing com.jleechan.git-push-user-scope launchd job; no
  # new plist needed. Excludes regenerable caches (backups/, cache/, chrome/,
  # paste-cache/, session-env/, __pycache__).
  "copy|$HOME/.claude-agent-f/||claude_conversations/claude_agent_f/||backups,cache,chrome,paste-cache,session-env,__pycache__|sync"
  "copy|${OPENCLAW_BACKUP_DIR%/}/|openclaw/||${OPENCLAW_GIT_EXCLUDE_PATTERNS}|sync"
  "copy|${OPENCLAW_BACKUP_DIR%/}/||openclaw_conversations/openclaw/|${OPENCLAW_CONVO_EXCLUDE_PATTERNS}|sync"
  "copy|${OPENCLAW_BACKUP_DIR%/}/agents/main/sessions/||openclaw_conversations/sessions/||sync"
  "copy|${OPENCLAW_BACKUP_DIR%/}/qdrant_storage/||openclaw_conversations/qdrant_storage/||sync"
  # Hermes conversation sessions — Dropbox only (3.8GB across both dirs, 2944 files).
  # Not git-tracked because sessions are large ephemeral chat history.
  "copy|$HOME/.hermes/sessions/||hermes_conversations/hermes/sessions/||sync"
  "copy|$HOME/.hermes_prod/sessions/||hermes_conversations/hermes_prod/sessions/||sync"
  "copy|$HOME/.claude/agents/|claude/agents/|claude_conversations/agents/||sync"
  "copy|$HOME/.claude/hooks/|claude/hooks/|claude_conversations/hooks/||sync"
  "copy|$HOME/.claude/CLAUDE.md|claude/CLAUDE.md|claude_conversations/CLAUDE.md||sync"
  "copy|$HOME/.claude/settings.json|claude/settings.json|claude_conversations/settings.json||sync"

  "copy|$HOME/.claude/commands/|claude/commands/|claude_conversations/commands/||sync"
  "copy|$HOME/.claude/skills/|claude/skills/|claude_conversations/skills/||sync"
  "copy|$HOME/.claude/scripts/|claude/scripts/|claude_conversations/scripts/||sync"
  "copy|$HOME/.claude/mcp-servers/|claude/mcp-servers/|claude_conversations/mcp-servers/||sync"
  "copy|$HOME/.codex/AGENTS.md|codex/AGENTS.md|codex_conversations/AGENTS.md||sync"
  "copy|$HOME/.codex/config.json|codex/config.json|codex_conversations/config.json||sync"
  "copy|$HOME/.codex/config.toml|codex/config.toml|codex_conversations/config.toml||sync"
  "copy|$HOME/.claude.json|claude.json|claude_conversations/claude.json||sync"
  "copy|$HOME/.claude/.claude.json|claude/claude-dotdir.json|claude_conversations/claude-dotdir.json||sync"
  # ~/.claude-wa — WorldArchitect Claude Code profile (claudewa / claude2).
  # Shared tooling + conversations: symlinked to ~/.claude (backed up via claude/* and
  # claude_conversations/projects above). This row captures WA-local state only:
  # .claude.json / .credentials.json, sessions/, history.jsonl, file-history/, backups/.
  # rsync -a stores symlinks as links (no duplicate copy of shared tree).
  # Installer: scripts/install-claude-wa-profile.sh (git-tracked in this repo).
  "copy|$HOME/.claude-wa/|claude/claude-wa/|claude_conversations/claude-wa/|cache,chrome,session-env,telemetry,debug,shell-snapshots,tasks,teams,plans,statsig,todos,__pycache__|sync"
  "copy|$HOME/.claude/mcp-strict.json|claude/mcp-strict.json|claude_conversations/mcp-strict.json||sync"
  "copy|$HOME/.config/git/hooks/|config/git/hooks/|config/git/hooks/||sync"
  "copy|$HOME/.cursor/mcp.json|cursor/mcp.json|cursor_conversations/mcp.json||sync"
  "copy|$HOME/.cursor/cli-config.json|cursor/cli-config.json|cursor_conversations/cli-config.json||sync"
  "copy|$HOME/.cursor/rules/|cursor/rules/|cursor_conversations/rules/||sync"
  "copy|$HOME/.cursor/chats/|cursor/chats/|cursor_conversations/chats/||sync"
  "copy|$HOME/.cursor/prompt_history.json||cursor_conversations/prompt_history.json||sync"
  "copy|${OPENCODE_DATA_DIR%/}/storage/session_diff/|opencode/session_diff/|opencode_conversations/session_diff/||sync"
  "copy|$HOME/.gemini/GEMINI.md|gemini/GEMINI.md|gemini_conversations/GEMINI.md||sync"
  "copy|$HOME/memory/|memory/|memory/||sync"
  "copy|$HOME/.gemini/settings.json|gemini/settings.json|gemini_conversations/settings.json||sync"
  "copy|$HOME/.gemini/antigravity-cli/settings.json|gemini/antigravity-cli/settings.json|gemini_conversations/antigravity-cli/settings.json||sync"
  "copy|$HOME/.gemini/mcp.json|gemini/mcp.json|gemini_conversations/mcp.json||sync"
  "copy|$HOME/.gemini/projects.json|gemini/projects.json|gemini_conversations/projects.json||sync"
  "copy|$HOME/.gemini/trusted_hooks.json|gemini/trusted_hooks.json|gemini_conversations/trusted_hooks.json||sync"
  "copy|$HOME/.gemini/trustedFolders.json|gemini/trustedFolders.json|gemini_conversations/trustedFolders.json||sync"
  "copy|$HOME/.gemini/config/|gemini/config/|gemini_conversations/config/||sync"
  "copy|$HOME/.bashrc||shell/bashrc||sync"
  "copy|$HOME/.config/mcp-daemon/|mcp-daemon/||logs/|sync"
  "copy|$HOME/.config/opencode/|mcp-daemon/opencode/|opencode_conversations/opencode/|node_modules/,commands|sync"
  "copy|${OPENCODE_DATA_DIR%/}/|opencode/||${OPENCODE_GIT_EXCLUDE_PATTERNS}|sync"
  "copy|${OPENCODE_DATA_DIR%/}/||opencode_conversations/opencode/|${OPENCODE_CONVO_EXCLUDE_PATTERNS}|sync"
)
# Back up a specific OpenClaw directory if requested via OPENCLAW_BACKUP_DIR or
# OPENCLAW_CONVO_DIR; otherwise defaults to entire ~/.openclaw.

# Disk snapshot — record sizes of known problem dirs before backup.
#
# As of 2026-06-26 the disk-magician snapshot is owned by the standalone
# launchd job `com.jleechan.user-scope-disk-snapshot` (installed via
# dotfiles/launchd/com.jleechan.user-scope-disk-snapshot.plist.template,
# runs daily at 04:00). The launchd job writes backup/Mac/disk_snapshot.json
# directly, so this script no longer spawns disk-magician inline.
#
# Why it was removed:
# - Inline invocation + 300s outer wait was getting killed before completion.
# - disk_magician_config.json has 55 monitored dirs; sum of per-dir timeouts
#   is 4890s (81m30s) worst case, vs. the 300s outer kill — a 16× mismatch.
# - The snapshot is purely informational; per the original comment it must
#   NOT block the actual backup. Decoupling matches that intent and the
#   existing pattern (other disk-magician jobs already use launchd).
#
# Stale-snapshot tolerance: up to ~24h (next launchd run is daily at 04:00).
# Acceptable because the snapshot is informational and the backup commits the
# file as-is (no rewriting here).

# Crontab snapshot — the user crontab is NOT a file under $HOME, so the
# BACKUP_ITEMS rsync rows cannot capture it. Dump `crontab -l` into the
# git-tracked backup tree so a fresh-machine restore can reinstate the
# scheduled jobs (notably the mem-watchdog `--once` minute scan and the
# @reboot daemon — the OOM-guard's redundant invokers). Runs before the
# snapshot commit below (which `git add backup/`), so the dump is included.
# Deliberately NO timestamp header: keep the file byte-stable so it only
# changes when the crontab actually changes, avoiding churn on every run.
dump_crontab() {
  local out_dir="$GIT_BACKUP_ROOT/cron"
  local out_file="$out_dir/crontab.txt"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN: would write crontab snapshot to $out_file"
    return 0
  fi
  mkdir -p "$out_dir"
  if crontab -l >"$out_file.tmp" 2>/dev/null; then
    mv "$out_file.tmp" "$out_file"
    log "[crontab] snapshot written to $out_file"
  else
    # No crontab, or `crontab -l` failed — do NOT delete an existing snapshot
    # (that history is the restore source). Just leave the prior file in place.
    rm -f "$out_file.tmp"
    log "[crontab] no user crontab present (or crontab -l failed); kept existing snapshot"
  fi
}
dump_crontab

dropbox_result_file="$(mktemp "$SECURE_TEMP/dropbox_target_XXXXXXXX")"
if [[ "$ALLOW_GIT_BACKUP_SYNC" == "1" ]]; then
  git_result_file="$(mktemp "$SECURE_TEMP/git_target_XXXXXXXX")"
  run_target_job "git" "$GIT_BACKUP_ROOT" "git" "$git_result_file"
  git_pid="$RUN_TARGET_JOB_PID"
else
  log "Skipping git backup target: set ALLOW_GIT_BACKUP_SYNC=1 for local snapshot copies"
fi
run_target_job "dropbox" "$DROPBOX_TARGET" "dropbox" "$dropbox_result_file"
dropbox_pid="$RUN_TARGET_JOB_PID"

if [[ "$ALLOW_GIT_BACKUP_SYNC" == "1" ]]; then
  wait "$git_pid" || true
fi
wait "$dropbox_pid" || true

if [[ "$ALLOW_GIT_BACKUP_SYNC" == "1" ]]; then
  git_status="$(cat "$git_result_file")"
else
  git_status="SUCCESS"
fi
dropbox_status="$(cat "$dropbox_result_file")"

log "Home backup results: git=$git_status dropbox=$dropbox_status"

if [[ "$git_status" == "SUCCESS" && "$DRY_RUN" -eq 0 ]]; then
  if [[ "$ALLOW_GIT_BACKUP_PUSH" != "1" ]]; then
    log "Skipping git snapshot commit/push: set ALLOW_GIT_BACKUP_PUSH=1 to enable"
  elif [[ "$ALLOW_GIT_BACKUP_SYNC" != "1" ]]; then
    log "Skipping git snapshot commit/push: ALLOW_GIT_BACKUP_SYNC must be 1 to stage a snapshot"
  elif ! require_snapshot_push_target "$REPO_ROOT" "$GIT_BACKUP_PUSH_REMOTE" "$GIT_BACKUP_PUSH_BRANCH"; then
    git_status="FAILED"
  else
    cd "$REPO_ROOT"
    current_branch="$(git rev-parse --abbrev-ref HEAD)"
    _snapshot_main_branch="$GIT_BACKUP_PUSH_BRANCH"

    _do_snapshot_commit() {
      local work_dir="$1"
      local branch="$2"
      if [[ -n "$(git -C "$work_dir" status --porcelain "backup/")" ]]; then
        git -C "$work_dir" add "backup/"
        # Run gitleaks before commit to detect secrets
        # Use baseline to ignore known leaks in existing files
        if command -v gitleaks >/dev/null 2>&1; then
          local gl_config_args=()
          [[ -f "${work_dir}/.gitleaks.toml" ]] && gl_config_args=(--config "${work_dir}/.gitleaks.toml")

          if ! gitleaks protect --staged \
              "${gl_config_args[@]}" 2>/dev/null; then

            # Auto-remediate: get leaks from staged files and scrub them in-place
            local gl_report="/tmp/gitleaks-staged-$$_$(date +%s).json"
            gitleaks protect --staged "${gl_config_args[@]}" \
              --report-format json --report-path "$gl_report" 2>/dev/null || true

            local leak_count
            leak_count="$(python3 -c "import json; d=json.load(open('$gl_report')); print(len(d))" 2>/dev/null || echo 0)"
            log "WARNING: gitleaks found $leak_count secret(s) in staged files — scrubbing tokens in-place"

            # Scrub secrets from staged files using the report
            python3 -c "
import json, os, sys

work_dir = '$work_dir'
report = json.load(open('$gl_report'))

from collections import defaultdict
by_file = defaultdict(set)
for finding in report:
    fpath = finding.get('File', '')
    secret = finding.get('Secret', '').strip()
    if fpath and secret:
        by_file[fpath].add(secret)

scrubbed = 0
for rel_path, secrets in by_file.items():
    abs_path = os.path.join(work_dir, rel_path)
    if not os.path.isfile(abs_path):
        continue
    try:
        content = open(abs_path, 'r', errors='replace').read()
        original = content
        for secret in secrets:
            if secret in content:
                content = content.replace(secret, '[REDACTED]')
        if content != original:
            open(abs_path, 'w').write(content)
            scrubbed += 1
            print('scrubbed: ' + rel_path, file=sys.stderr)
    except Exception as e:
        print('WARN: could not scrub ' + rel_path + ': ' + str(e), file=sys.stderr)

print(scrubbed)
" > /tmp/gitleaks-scrub-count.txt 2>/tmp/gitleaks-scrub-log.txt

            local scrub_count
            scrub_count="$(cat /tmp/gitleaks-scrub-count.txt)"
            while IFS= read -r scrub_line; do
              [[ -n "$scrub_line" ]] && log "INFO: $scrub_line"
            done < /tmp/gitleaks-scrub-log.txt
            rm -f /tmp/gitleaks-scrub-count.txt /tmp/gitleaks-scrub-log.txt "$gl_report"

            if [[ "$scrub_count" -eq 0 || "$scrub_count" == "" ]]; then
              log "ERROR: gitleaks found leaks but could not scrub any files — refusing to commit"
              return 1
            fi

            log "INFO: scrubbed $scrub_count file(s); re-staging and re-scanning"
            git -C "$work_dir" add "backup/" 2>/dev/null || true

            # Re-scan — must be clean now
            if ! gitleaks protect --staged \
                "${gl_config_args[@]}" 2>/dev/null; then
              log "ERROR: gitleaks still found secrets after auto-remediation — refusing to commit"
              return 1
            fi
            log "INFO: gitleaks clean after auto-remediation"
          fi
        fi
        git -C "$work_dir" commit "backup/" -m "backup: automated home config snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        log "Pushing: ${branch} -> ${GIT_BACKUP_PUSH_REMOTE}/${branch} (branch verified, no force)"
        git -C "$work_dir" push "$GIT_BACKUP_PUSH_REMOTE" "${branch}:${branch}"
        log "Committed and pushed config snapshot to git"
      else
        log "No config changes to commit"
      fi
    }

    if [[ "$current_branch" == "$_snapshot_main_branch" ]]; then
      if ! _do_snapshot_commit "$REPO_ROOT" "$_snapshot_main_branch"; then
        git_status="FAILED"
        log "ERROR: git snapshot commit/push failed"
      fi
    else
      log "Not on $_snapshot_main_branch (got '$current_branch') — committing via temporary worktree"
      _snapshot_worktree="$(mktemp -d)"
      if git worktree add "$_snapshot_worktree" "$_snapshot_main_branch" 2>/dev/null; then
        git -C "$_snapshot_worktree" pull "$GIT_BACKUP_PUSH_REMOTE" "$_snapshot_main_branch" --ff-only 2>/dev/null || true
        rsync -a "$GIT_BACKUP_ROOT/" "$_snapshot_worktree/backup/$MACHINE_NAME/"
        if ! _do_snapshot_commit "$_snapshot_worktree" "$_snapshot_main_branch"; then
          git_status="FAILED"
          log "ERROR: git snapshot commit/push failed (via worktree)"
        fi
        git worktree remove --force "$_snapshot_worktree" 2>/dev/null || true
      else
        git_status="FAILED"
        log "ERROR: could not create worktree for $_snapshot_main_branch — skipping automated snapshot commit"
      fi
      rm -rf "$_snapshot_worktree" 2>/dev/null || true
    fi
  fi
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  # disk-magician snapshot is now owned by the launchd job
  # `com.jleechan.user-scope-disk-snapshot` — no inline invocation here.
  # The backup simply commits whatever backup/Mac/disk_snapshot.json contains
  # at this moment (up to ~24h stale, acceptable for an informational report).
  append_backup_report "result_git=$git_status"
  append_backup_report "result_dropbox=$dropbox_status"
  finalize_backup_report
fi

if [[ "$git_status" != "SUCCESS" || "$dropbox_status" != "SUCCESS" ]]; then
  exit 1
fi
