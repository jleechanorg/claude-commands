#!/usr/bin/env bash
# cleanup-ao-sessions.sh — Age-based GC for ~/.ao-sessions/<id> directories.
#
# Companion to ~/Library/LaunchAgents/com.jleechan.cleanup-ao-sessions.plist
# which already schedules this script at 04:23 daily with `--clean --days 1`.
# Without this script body the launchd plist silently fails — the work it
# was meant to do is exactly what this file does.
#
# AO worker sessions accumulate fast. Per the prior three-tier disk cleanup
# playbook (~/.claude/projects/.../memory/feedback_2026-06-14_disk_cleanup_three_tier.md):
#   ~/.ao-sessions/<sid>/.gemini/  — 22 GB conversation protobuf + brain logs
#   ~/.ao-sessions/<sid>/.gemini/antigravity/worktrees/<project>/<branch>/venv/  — 1 GB each
# 6 workers × 22 GB = 132 GB in a single day. Sessions are never auto-cleaned
# by the AO daemon — that's our job.
#
# ──────────────────────────────────────────────────────────────────────────────
# SAFETY (read these — they're the difference between safe and catastrophic)
# ──────────────────────────────────────────────────────────────────────────────
# 1. Dry-run by default. Pass --clean to actually rename session dirs to .bak.<ts>.
# 2. NEVER auto-deletes .bak.<ts>. Use --drop-bak to actually drop them. Backups
#    are intended for human review before deletion; the script never reaches
#    inside a .bak.<ts> dir on its own.
# 3. Sessions matching the orchestrator role prefixes (wa-*, jc-*) are NEVER
#    touched. Orchestrator tmux sessions are long-running control planes; deleting
#    their on-disk state corrupts AO state without killing the live tmux.
# 4. Sessions with a live tmux window OR a live PID matching the session id are
#    skipped — the on-disk state belongs to a running process.
# 5. Sessions newer than MIN_AGE_MINUTES (default 30) are skipped regardless of
#    the --days threshold — gives in-flight workers a hard floor.
#
# ──────────────────────────────────────────────────────────────────────────────
# USAGE
# ──────────────────────────────────────────────────────────────────────────────
#   cleanup-ao-sessions.sh                  # dry-run, default --days 1
#   cleanup-ao-sessions.sh --clean          # rename to .bak.<ts>
#   cleanup-ao-sessions.sh --days 7         # gate: --days minimum
#   cleanup-ao-sessions.sh --min-age 60     # floor in minutes for fresh work
#   cleanup-ao-sessions.sh --drop-bak       # actually delete .bak.<ts> dirs
#   cleanup-ao-sessions.sh --drop-bak --days 14  # only drop backups older than 14d

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
AO_SESSIONS_DIR="${AO_SESSIONS:-$HOME/.ao-sessions}"
TMP_DIR=$(getconf DARWIN_USER_TEMP_DIR 2>/dev/null || echo "/tmp/")

# Defaults — overridden by flags
DRY_RUN=true
DROP_BAK=false
THRESHOLD_DAYS=1
MIN_AGE_MINUTES=30
LOG_FILE="${CLEANUP_AO_SESSIONS_LOG:-/tmp/cleanup-ao-sessions.log}"

# Orchestrator session-id prefixes that MUST NOT be auto-cleaned.
# - wa-*  : worldarchitect.ai workers and orchestrators
# - jc-*  : jleechanclaw orchestrators
# These are long-running control planes; their on-disk state must outlive the
# short-lived wa-*/ao-* workers they spawn.
ORCHESTRATOR_PREFIXES_REGEX='^(wa-|jc-)'

# ── Arg parsing ───────────────────────────────────────────────────────────────
usage() {
  cat <<EOF
Usage: $(basename "$0") [--clean] [--days N] [--min-age MIN] [--drop-bak] [--help]

Delete (rename, then optionally drop) stale AO worker session directories.

By default runs in dry-run mode. Use --clean to actually rename session dirs to
.bak.<ts>. Use --drop-bak (separate pass) to actually delete .bak.<ts> dirs.

Options:
  --clean         Apply — rename session dirs to .bak.<ts>. Default: dry-run.
  --days N        Age threshold in days for the main sweep (default: 1).
  --min-age MIN   Absolute floor in minutes; sessions younger than this are
                  always skipped, regardless of --days (default: 30).
  --drop-bak      Drop .bak.<ts> dirs older than --days. NEVER run automatically
                  — invoked manually after human review.
  -h, --help      Show this help.

Examples:
  $(basename "$0")                                # dry-run preview (1d threshold)
  $(basename "$0") --clean                        # actually rename (launchd does this)
  $(basename "$0") --drop-bak --days 14           # drop backups older than 14d
EOF
}

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --clean)    DRY_RUN=false ;;
    --days)     shift; THRESHOLD_DAYS="${1:?--days requires a number}" ;;
    --min-age)  shift; MIN_AGE_MINUTES="${1:?--min-age requires a number}" ;;
    --drop-bak) DROP_BAK=true ;;
    -h|--help)  usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# ── Helpers ───────────────────────────────────────────────────────────────────
log() {
  local msg="[$(date '+%Y-%m-%dT%H:%M:%S')] $*"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

dry_tag() { [[ "$DRY_RUN" == true ]] && echo "DRY-RUN: " || echo ""; }

dir_age_seconds() {
  local path="$1"
  local mtime now
  mtime=$(stat -f '%m' "$path" 2>/dev/null) || return 1
  now=$(date +%s)
  echo $(( now - mtime ))
}

dir_age_days() {
  local path="$1"
  local secs
  secs=$(dir_age_seconds "$path") || return 1
  echo $(( secs / 86400 ))
}

dir_age_minutes() {
  local path="$1"
  local secs
  secs=$(dir_age_seconds "$path") || return 1
  echo $(( secs / 60 ))
}

size_human() {
  du -sh "$1" 2>/dev/null | cut -f1
}

# session_is_active — return 0 if the session has any live tmux window OR any
# process whose argv contains the session id.
session_is_active() {
  local sid="$1"

  # Live tmux window referencing the session id
  if command -v tmux >/dev/null 2>&1; then
    if tmux list-windows -a -F "#{window_name} #{pane_current_path}" 2>/dev/null \
      | grep -q "$sid"; then
      return 0
    fi
  fi

  # Live process referencing the session id (covers worker PIDs that escaped
  # the tmux window, e.g. detached Claude/Codex children).
  if pgrep -fl "$sid" >/dev/null 2>&1; then
    return 0
  fi

  return 1
}

is_orchestrator_session() {
  local sid="$1"
  [[ "$sid" =~ $ORCHESTRATOR_PREFIXES_REGEX ]]
}

# ── Main ──────────────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

if [[ ! -d "$AO_SESSIONS_DIR" ]]; then
  log "No $AO_SESSIONS_DIR — nothing to do."
  exit 0
fi

# ── Drop-backup pass (manual-only) ───────────────────────────────────────────
if [[ "$DROP_BAK" == true ]]; then
  log "=== --drop-bak pass: removing .bak.<ts> dirs older than ${THRESHOLD_DAYS}d ==="
  bak_pruned=0
  bak_freed_kb=0
  while IFS= read -r -d '' bak_dir; do
    [[ -d "$bak_dir" ]] || continue
    age=$(dir_age_days "$bak_dir") || continue
    if (( age < THRESHOLD_DAYS )); then
      continue
    fi
    size_kb=$(du -sk "$bak_dir" 2>/dev/null | cut -f1 || echo 0)
    size_h=$(size_human "$bak_dir")
    log "drop-bak: removing $bak_dir (${age}d old, ${size_h})"
    rm -rf "$bak_dir"
    bak_pruned=$(( bak_pruned + 1 ))
    bak_freed_kb=$(( bak_freed_kb + size_kb ))
  done < <(find "$AO_SESSIONS_DIR" -mindepth 1 -maxdepth 1 -type d -name "*.bak.*" -print0 2>/dev/null)

  bak_freed_gb=$(awk "BEGIN {printf \"%.2f\", $bak_freed_kb / 1048576}")
  log "--drop-bak DONE: removed $bak_pruned backup dir(s), ~${bak_freed_gb} GB freed"
  exit 0
fi

# ── Main sweep (rename or dry-run) ───────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  log "DRY-RUN mode (pass --clean to actually rename)"
fi
log "Age threshold: ${THRESHOLD_DAYS} days; min-age floor: ${MIN_AGE_MINUTES} minutes"
log ""

pruned_count=0
skipped_count=0
total_reclaimable_kb=0

for session_dir in "${AO_SESSIONS_DIR}"/*/; do
  [[ -d "$session_dir" ]] || continue
  sid=$(basename "$session_dir")

  # Orchestrator-prefix guard — never touch wa-* or jc-* on-disk state.
  if is_orchestrator_session "$sid"; then
    log "SKIP $sid: orchestrator role prefix (wa-/jc-) is preserved"
    skipped_count=$(( skipped_count + 1 ))
    continue
  fi

  age_min=$(dir_age_minutes "$session_dir") || { log "SKIP $sid: cannot stat"; skipped_count=$(( skipped_count + 1 )); continue; }
  age_days=$(( age_min / 1440 ))

  # Absolute floor — never reap fresh work regardless of --days.
  if (( age_min < MIN_AGE_MINUTES )); then
    log "SKIP $sid: ${age_min}m old (min-age floor ${MIN_AGE_MINUTES}m) — too recent"
    skipped_count=$(( skipped_count + 1 ))
    continue
  fi

  if (( age_days < THRESHOLD_DAYS )); then
    log "SKIP $sid: ${age_days}d old (threshold ${THRESHOLD_DAYS}d) — too recent"
    skipped_count=$(( skipped_count + 1 ))
    continue
  fi

  if session_is_active "$sid"; then
    log "SKIP $sid: live tmux window OR live PID referencing this session"
    skipped_count=$(( skipped_count + 1 ))
    continue
  fi

  session_size_kb=$(du -sk "$session_dir" 2>/dev/null | cut -f1 || echo 0)
  session_size_h=$(size_human "$session_dir")

  # Track and include the redirected /tmp files size in the same session
  session_tmp="${TMP_DIR}ao-${sid}"
  tmp_size_kb=0
  if [[ -d "$session_tmp" ]]; then
    tmp_size_kb=$(du -sk "$session_tmp" 2>/dev/null | cut -f1 || echo 0)
  fi

  total_session_kb=$(( session_size_kb + tmp_size_kb ))
  total_reclaimable_kb=$(( total_reclaimable_kb + total_session_kb ))
  total_session_gb=$(awk "BEGIN {printf \"%.1f\", $total_session_kb / 1048576}")

  log "CANDIDATE $sid: ${age_days}d old, ${session_size_h} (plus ${total_session_gb} GB in tmp)"

  if [[ "$DRY_RUN" == false ]]; then
    # Rename to .bak.<ts> for reversibility. Real deletion is a separate
    # manual --drop-bak pass — this script NEVER auto-deletes.
    ts=$(date +%Y%m%d-%H%M%S)
    bak_path="${session_dir%/}.bak.${ts}"
    if mv "$session_dir" "$bak_path" 2>/dev/null; then
      log "  RENAMED $sid → $(basename "$bak_path") (would free ${total_session_gb} GB on drop)"
    else
      log "  ERROR: failed to rename $sid to $bak_path"
      skipped_count=$(( skipped_count + 1 ))
      continue
    fi
    if [[ -d "$session_tmp" ]]; then
      mv "$session_tmp" "${session_tmp}.bak.${ts}" 2>/dev/null || true
    fi
    pruned_count=$(( pruned_count + 1 ))
  else
    log "  DRY-RUN: would rename $sid → ${sid}.bak.<ts> (would free ${total_session_gb} GB on drop)"
    pruned_count=$(( pruned_count + 1 ))
  fi
done

echo ""
total_reclaimable_gb=$(awk "BEGIN {printf \"%.1f\", $total_reclaimable_kb / 1048576}")

if [[ "$DRY_RUN" == true ]]; then
  log "DRY-RUN SUMMARY: ${pruned_count} sessions would be renamed, ~${total_reclaimable_gb} GB reclaimable"
  log "  Skipped ${skipped_count} sessions (orchestrator, fresh, active, or below threshold)"
  log "  Run with --clean to proceed."
else
  log "DONE: ${pruned_count} sessions renamed to .bak.<ts>, ~${total_reclaimable_gb} GB reclaimable (after --drop-bak)"
  log "  Skipped ${skipped_count} sessions (orchestrator, fresh, active, or below threshold)"
  log "  Backups are NOT auto-deleted. Use --drop-bak --days N to manually drop them."
fi