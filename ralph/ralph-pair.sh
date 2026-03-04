#!/bin/bash
# Ralph-Pair — Ralph with Deterministic Verification
# Same as ralph.sh but after each iteration, runs verifyCommand for every
# unpassed story and auto-marks them as passed when commands succeed.
#
# Usage: ./ralph-pair.sh [command] [options]
#   run    [max_iterations]   Run agent loop with verification (default)
#   status [--watch|-w]       CLI status monitor
#
# The only difference from ralph.sh:
#   After the coder agent completes an iteration, we run verifyCommand
#   for every unpassed story. Stories whose verifyCommand passes get
#   auto-marked as passes:true in prd_state.json. If the coder claims
#   COMPLETE but some stories haven't passed verification, we continue
#   to the next iteration.
#
# PRD schema: User stories may include an optional "verifyCommand" field
# (shell command string). Only trusted PRD sources should be used; commands
# are executed via bash -c in the workspace.
#
# Dual PRD model: PRD_FILE (prd.json) is the original spec; PRD_STATE_FILE
# (prd_state.json) holds runtime pass/fail state. The coder reads PRD_FILE
# for the full spec; verifier/metrics/status use PRD_STATE_FILE for state.

set -euo pipefail

# Ensure GITHUB_TOKEN is available for sourced libs / gh CLI (use GH_TOKEN fallback)
if [ -z "${GITHUB_TOKEN:-}" ] && [ -n "${GH_TOKEN:-}" ]; then
  export GITHUB_TOKEN="$GH_TOKEN"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
RUNTIME_DIR="${RALPH_PAIR_RUNTIME_DIR:-/tmp/ralph-pair-run}"
export RALPH_RUNTIME_DIR="$RUNTIME_DIR"
PROGRESS_FILE="$RUNTIME_DIR/progress.txt"
PRD_STATE_FILE="$RUNTIME_DIR/prd_state.json"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"
DASHBOARD_HTML="$SCRIPT_DIR/dashboard.html"
DASHBOARD_PORT=9450
METRICS_FILE="$RUNTIME_DIR/metrics.json"
EVIDENCE_DIR="$RUNTIME_DIR/evidence"

# Source extracted libraries (same as ralph.sh)
for lib in evidence metrics workspace tools status terminal_recorder; do
  [ -f "$SCRIPT_DIR/lib/${lib}.sh" ] && source "$SCRIPT_DIR/lib/${lib}.sh"
done

# ─── VERIFIER ─────────────────────────────────────────────────────────────────
# Run verifyCommand for ALL unpassed stories and auto-mark passed ones.
# Does NOT rely on the coder to update prd_state.json.

run_verification_pass() {
  local workspace="$1"
  local agent_cmd="$2"  # unused, kept for compat
  local snapshot_file="${3:-}"  # unused, kept for compat

  if [ ! -f "$PRD_STATE_FILE" ]; then
    echo "  ⚠️  No PRD state to verify"
    return 0
  fi

  # Get all unpassed stories with verifyCommand
  local to_verify
  to_verify=$(python3 - "$PRD_STATE_FILE" << 'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    prd = json.load(f)
for s in prd.get('userStories', []):
    sid = s.get('id', '?')
    title = s.get('title', '')
    vcmd = s.get('verifyCommand', '')
    passes = s.get('passes', False)
    if not passes and vcmd:
        print(f'{sid}\t{title}\t{vcmd}')
PYEOF
)

  if [ -z "$to_verify" ]; then
    echo "  ℹ️  All stories passed or no verifyCommands to run"
    return 0
  fi

  local any_failed=0
  local marked=0
  local verify_log="$RUNTIME_DIR/verify_${$}.txt"
  while IFS=$'\t' read -r sid title vcmd; do
    echo "  🔍 $sid: $title"
    echo "     \$ $vcmd"
    if (cd "$workspace" && bash -c "$vcmd" > "$verify_log" 2>&1); then
      echo "     ✅ PASSED — marking $sid as done"
      # Auto-set passes: true in prd_state.json (atomic write via temp file)
      python3 - "$PRD_STATE_FILE" "$sid" << 'PYMARK'
import json, sys, os, tempfile
prd_file, story_id = sys.argv[1], sys.argv[2]
with open(prd_file) as f: prd = json.load(f)
# Mark this story as passed
for s in prd['userStories']:
    if s['id'] == story_id:
        s['passes'] = True
        break
# If this is a verify story (VN), also mark its paired implement story (SN)
if story_id.startswith('V'):
    paired_id = 'S' + story_id[1:]
    for s in prd['userStories']:
        if s['id'] == paired_id:
            s['passes'] = True
            break
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(prd_file))
with os.fdopen(fd, 'w') as f: json.dump(prd, f, indent=2)
os.replace(tmp, prd_file)
PYMARK
      marked=$((marked + 1))
    else
      echo "     ❌ FAILED"
      tail -5 "$verify_log" 2>/dev/null | sed 's/^/     /'
      any_failed=1
    fi
  done <<< "$to_verify"

  [ "$marked" -gt 0 ] && echo "  📊 Auto-marked $marked stories as passed in prd_state.json"
  return $any_failed
}

# ─── CLEANUP (same as ralph.sh) ──────────────────────────────────────────────

run_cleanup_task() {
  local label="$1"
  local timeout_secs="$2"
  shift 2

  local pid
  (
    "$@"
  ) &
  pid=$!

  local elapsed=0
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$elapsed" -ge "$timeout_secs" ]; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      echo "  ⚠️ $label cleanup timed out"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  wait "$pid" 2>/dev/null || true
}

run_cleanup() {
  local outcome="${1:-interrupted}"
  local exit_code="${2:-1}"
  local was_interrupted="${3:-0}"

  if [ "${RUN_CLEANUP_DONE:-0}" -eq 1 ]; then
    return "$exit_code"
  fi
  RUN_CLEANUP_DONE=1

  if [ "${RUN_SESSION_ACTIVE:-0}" -ne 1 ]; then
    return "$exit_code"
  fi

  set +e

  if [ "$was_interrupted" -eq 1 ]; then
    echo ""
    echo "Ralph-Pair interrupted. Progress saved to $PROGRESS_FILE"
  fi

  terminal_record_stop 2>&1 || { ec=$?; echo "  ⚠️ terminal_record_stop failed (exit $ec)" >&2; }
  if [ -n "${TERMINAL_LOG:-}" ] && [ -f "$TERMINAL_LOG" ]; then
    run_cleanup_task "terminal SRT" 5 terminal_to_srt "$TERMINAL_LOG" "$EVIDENCE_DIR/captions/terminal.srt" 2>&1 || { ec=$?; echo "  ⚠️ terminal SRT failed (exit $ec)" >&2; }
    run_cleanup_task "terminal video" 5 terminal_render_video "$TERMINAL_LOG" "$EVIDENCE_DIR/terminal_recording.webm" "$EVIDENCE_DIR/captions/terminal.srt" 2>&1 || { ec=$?; echo "  ⚠️ terminal video failed (exit $ec)" >&2; }
  fi

  if [ -n "${TERMINAL_LOG:-}" ] && [ -f "$TERMINAL_LOG" ] && [ ! -f "$EVIDENCE_DIR/captions/terminal.srt" ]; then
    mkdir -p "$EVIDENCE_DIR/captions"
    cat > "$EVIDENCE_DIR/captions/terminal.srt" <<'EOF'
1
00:00:00,000 --> 00:00:03,000
Terminal SRT fallback generated during cleanup
EOF
  fi

  local metrics_prd="${PRD_STATE_FILE:-$PRD_FILE}"
  if [ -n "${RUN_START:-}" ] && [ -n "${WORKSPACE:-}" ] && [ -n "${PROGRESS_FILE:-}" ] && [ -n "${RALPH_TOOL:-}" ]; then
    run_cleanup_task "metrics record" 5 record_metrics "$outcome" "$metrics_prd" "$METRICS_FILE" "$WORKSPACE" "$PROGRESS_FILE" "$RALPH_TOOL" "$RUN_START" 2>&1 || { ec=$?; echo "  ⚠️ metrics record failed (exit $ec)" >&2; }
  fi
  if [ ! -f "$METRICS_FILE" ]; then
    mkdir -p "$(dirname "$METRICS_FILE")"
    printf '{"outcome":"%s","duration_seconds":0,"stories_passed":0,"stories_total":0,"files_modified":0,"tool":"%s","workspace":"%s"}' \
      "$outcome" "${RALPH_TOOL:-unknown}" "${WORKSPACE:-unknown}" > "$METRICS_FILE"
  fi
  run_cleanup_task "evidence finalize" 8 evidence_finalize "$metrics_prd" "$METRICS_FILE" "$EVIDENCE_DIR" 2>&1 || { ec=$?; echo "  ⚠️ evidence finalize failed (exit $ec)" >&2; }

  if [ ! -f "$EVIDENCE_DIR/evidence_summary.md" ]; then
    mkdir -p "$EVIDENCE_DIR"
    printf '# Ralph-Pair Evidence Summary\n**Result:** pending\n' > "$EVIDENCE_DIR/evidence_summary.md"
  fi

  set -e
  return "$exit_code"
}

# ─── RUN COMMAND (modified ralph loop with verification) ──────────────────────

cmd_run() {
  RUN_SESSION_ACTIVE=0
  RUN_CLEANUP_DONE=0
  RUN_OUTCOME="interrupted"

  trap 'run_cleanup "$RUN_OUTCOME" "$?" 1' INT TERM
  trap 'run_cleanup "$RUN_OUTCOME" "$?"' EXIT

  # Parse arguments (same as ralph.sh)
  MAX_ITERATIONS=10
  RALPH_TOOL="${RALPH_TOOL:-claude}"
  WORKSPACE=""
  while [[ $# -gt 0 ]]; do
    case $1 in
      [0-9]*)         MAX_ITERATIONS="$1"; shift ;;
      --tool)         [ -z "${2:-}" ] && { echo "Error: --tool requires a value" >&2; exit 2; }; RALPH_TOOL="$2"; shift 2 ;;
      --workspace)    [ -z "${2:-}" ] && { echo "Error: --workspace requires a value" >&2; exit 2; }; WORKSPACE="$2"; shift 2 ;;
      *)              echo "Error: Unknown argument '$1'" >&2; exit 2 ;;
    esac
  done

  if ! AGENT_CMD=$(resolve_tool_cmd "$RALPH_TOOL"); then
    exit 2
  fi

  # Initialize runtime directory FIRST (archive may write to it)
  mkdir -p "$RUNTIME_DIR/logs" "$RUNTIME_DIR/state"

  # Archive previous run if branch changed
  if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
    CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || true)
    LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || true)
    if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
      DATE=$(date +%Y-%m-%d)
      FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
      ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"
      echo "Archiving previous run: $LAST_BRANCH"
      mkdir -p "$ARCHIVE_FOLDER"
      [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
      [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    fi
  fi

  # Track current branch
  if [ -f "$PRD_FILE" ]; then
    CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || true)
    [ -n "$CURRENT_BRANCH" ] && echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi

  if [ ! -f "$PROGRESS_FILE" ]; then
    echo "# Ralph-Pair Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi

  if [ ! -f "$PRD_STATE_FILE" ] && [ -f "$PRD_FILE" ]; then
    cp "$PRD_FILE" "$PRD_STATE_FILE"
    echo "  Initialized runtime PRD state: $PRD_STATE_FILE"
  fi

  WORKSPACE=$(resolve_workspace "$WORKSPACE" "$REPO_ROOT" 2>/dev/null || echo "$REPO_ROOT")
  RUN_START=$(date +%s)

  evidence_init "$EVIDENCE_DIR" 2>/dev/null || true
  RUN_SESSION_ACTIVE=1

  echo "Starting Ralph-Pair - Max iterations: $MAX_ITERATIONS | Tool: $RALPH_TOOL ($AGENT_CMD)"
  echo "  Mode: coder + deterministic verifier (runs verifyCommand per story)"
  [ "$WORKSPACE" != "$REPO_ROOT" ] && echo "  Workspace: $WORKSPACE"

  # Start terminal recording
  TERMINAL_LOG="$EVIDENCE_DIR/recordings/terminal_$(date +%Y%m%d_%H%M%S).log"
  terminal_record_start "ralph-run" "$TERMINAL_LOG" 2>/dev/null || true

  for i in $(seq 1 $MAX_ITERATIONS); do
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Ralph-Pair Iteration $i of $MAX_ITERATIONS (Coder Phase)"
    echo "═══════════════════════════════════════════════════════════════"

    # ─── CODER PHASE — runs FROM workspace dir so files land there ────
    if [ "$RALPH_TOOL" = "codex" ]; then
      PROMPT=$(build_prompt "$SCRIPT_DIR/CLAUDE.md" "$PRD_FILE" "$PROGRESS_FILE" "$WORKSPACE" 2>/dev/null || cat "$SCRIPT_DIR/CLAUDE.md")
      if ! OUTPUT=$(cd "$WORKSPACE" && $AGENT_CMD "$PROMPT" 2>&1 | tee -a "$TERMINAL_LOG"); then
        echo "Error: $RALPH_TOOL failed on iteration $i" >&2
        RUN_OUTCOME="agent_error"
        exit 1
      fi
    else
      unset CLAUDECODE 2>/dev/null || true
      PROMPT_TEXT=$(build_prompt "$SCRIPT_DIR/CLAUDE.md" "$PRD_FILE" "$PROGRESS_FILE" "$WORKSPACE" 2>/dev/null || cat "$SCRIPT_DIR/CLAUDE.md")
      if ! OUTPUT=$(cd "$WORKSPACE" && echo "$PROMPT_TEXT" | $AGENT_CMD 2>&1 | tee -a "$TERMINAL_LOG"); then
        echo "Error: $RALPH_TOOL failed on iteration $i" >&2
        RUN_OUTCOME="agent_error"
        exit 1
      fi
    fi

    # Evidence hooks
    evidence_screenshot "$EVIDENCE_DIR" "post_iter${i}" 2>/dev/null || true
    evidence_captions "$i" "$PRD_FILE" "$EVIDENCE_DIR" 2>/dev/null || true

    # ─── VERIFIER PHASE ──────────────────────────────────────────────
    echo ""
    echo "───────────────────────────────────────────────────────────────"
    echo "  Ralph-Pair Iteration $i — Verifier Phase"
    echo "───────────────────────────────────────────────────────────────"

    run_verification_pass "$WORKSPACE" "$AGENT_CMD" "" || true

    # ─── CHECK COMPLETION ────────────────────────────────────────────
    # Check if ALL stories are now passed (either by coder or by verifier)
    ALL_PASSED=$(python3 - "$PRD_STATE_FILE" << 'PYCHECK'
import json, sys
with open(sys.argv[1]) as f:
    prd = json.load(f)
stories = prd.get('userStories', [])
all_pass = len(stories) > 0 and all(s.get('passes') for s in stories)
print('yes' if all_pass else 'no')
PYCHECK
)

    if [ "$ALL_PASSED" = "yes" ]; then
      echo ""
      echo "Ralph-Pair completed all tasks! (verified)"
      echo "Completed at iteration $i of $MAX_ITERATIONS"
      evidence_browser_proof "$SCRIPT_DIR" "$EVIDENCE_DIR" 2>/dev/null || true
      RUN_OUTCOME="complete"
      exit 0
    fi

    # Show progress
    PASSED_COUNT=$(python3 - "$PRD_STATE_FILE" << 'PYCOUNT'
import json, sys
with open(sys.argv[1]) as f:
    prd = json.load(f)
passed = sum(1 for s in prd['userStories'] if s.get('passes'))
total = len(prd['userStories'])
print(f'{passed}/{total}')
PYCOUNT
)
    echo "  📊 Stories: $PASSED_COUNT passed. Continuing to next iteration..."
    sleep 2
  done

  echo ""
  echo "Ralph-Pair reached max iterations ($MAX_ITERATIONS) without completing all tasks."
  echo "Check $PROGRESS_FILE for status."
  RUN_OUTCOME="max_iterations"
  exit 1
}

# ─── STATUS (reuse ralph's status) ───────────────────────────────────────────

cmd_status() {
  if [ "${1:-}" = "--watch" ] || [ "${1:-}" = "-w" ]; then
    while true; do
      clear
      local status_prd="$PRD_STATE_FILE"
      [ ! -f "$status_prd" ] && status_prd="$PRD_FILE"
      show_status "$status_prd" "$PROGRESS_FILE" "$REPO_ROOT"
      sleep "${RALPH_REFRESH:-3}"
    done
  else
    local status_prd="$PRD_STATE_FILE"
    [ ! -f "$status_prd" ] && status_prd="$PRD_FILE"
    show_status "$status_prd" "$PROGRESS_FILE" "$REPO_ROOT"
  fi
}

# ─── MAIN DISPATCH ───────────────────────────────────────────────────────────

cmd_help() {
  echo "Ralph-Pair — Ralph with Deterministic Verification"
  echo ""
  echo "Usage: ./ralph-pair.sh <command> [options]"
  echo ""
  echo "Commands:"
  echo "  run [--tool claude|codex|amp] [N]   Run agent loop with verification"
  echo "  status [--watch|-w]                 CLI status monitor"
  echo "  help                                Show this help"
  echo ""
  echo "After each coder iteration, runs verifyCommand for every unpassed"
  echo "story and auto-marks them as passed. Only exits when ALL stories"
  echo "have their verifyCommand pass."
}

case "${1:-run}" in
  run)        [ $# -gt 0 ] && shift; cmd_run "$@" ;;
  status)     [ $# -gt 0 ] && shift; cmd_status "$@" ;;
  help|--help|-h) cmd_help ;;
  --tool)     cmd_run "$@" ;;
  *)
    if [[ "${1:-}" =~ ^[0-9]+$ ]]; then
      cmd_run "$@"
    else
      echo "Unknown command: $1"
      cmd_help
      exit 1
    fi
    ;;
esac
