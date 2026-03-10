#!/bin/bash
# Ralph Wiggum - PRD-Driven Autonomous Workflow Toolkit
# Usage: ./ralph.sh [command] [options]
#   run    [max_iterations]   Run agent loop (default)
#   status [--watch|-w]                           CLI status monitor
#   dashboard [--open|-o]                         Web dashboard on :9450

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"
DASHBOARD_HTML="$SCRIPT_DIR/dashboard.html"
DASHBOARD_PORT=9450
METRICS_FILE="$SCRIPT_DIR/metrics.json"
RUNTIME_DIR="/tmp/ralph-run"
export RALPH_RUNTIME_DIR="$RUNTIME_DIR"
EVIDENCE_DIR="$RUNTIME_DIR/evidence"

# Source extracted libraries
for lib in evidence metrics workspace tools status terminal_recorder; do
  [ -f "$SCRIPT_DIR/lib/${lib}.sh" ] && source "$SCRIPT_DIR/lib/${lib}.sh"
done

# Keep Claude worker count bounded so parallel Ralph runs do not pile up stuck sessions.
wait_for_convo_slot() {
  local max_active_convos="${RALPH_MAX_ACTIVE_CONVOS:-20}"
  local active_convos convos_to_kill
  local pid age age_list age_days age_hms p1 p2 p3 age_h age_m age_s age_seconds

  active_convos=$(pgrep -f "claude.*--dangerously-skip-permissions" || true)
  if [ -z "$active_convos" ]; then
    return
  fi

  age_list=""
  while IFS= read -r pid; do
    [ -z "$pid" ] && continue

    age=$(ps -o etime= -p "$pid" 2>/dev/null | xargs)
    if [ -z "$age" ]; then
      age_seconds=0
    else
      age_seconds=0
      if [[ "$age" == *-* ]]; then
        age_days=${age%%-*}
        age_hms=${age#*-}
        IFS=: read -r age_h age_m age_s <<< "$age_hms"
        age_h=${age_h#0}
        age_m=${age_m#0}
        age_s=${age_s#0}
        age_seconds=$(( (age_days * 86400) + (age_h * 3600) + (age_m * 60) + age_s ))
      else
        IFS=: read -r p1 p2 p3 <<< "$age"
        if [ -n "$p3" ]; then
          age_h=${p1#0}
          age_m=${p2#0}
          age_s=${p3#0}
          age_seconds=$(( (age_h * 3600) + (age_m * 60) + age_s ))
        else
          age_m=${p1#0}
          age_s=${p2#0}
          age_seconds=$(( (age_m * 60) + age_s ))
        fi
      fi
    fi

    age_list+="$age_seconds $pid"$'\n'
  done <<EOF
$active_convos
EOF

  convos_to_kill=$(
    printf "%s" "$age_list" \
      | sort -n -k1,1 \
      | awk -v cap="$max_active_convos" 'NF==2 && NR > cap {print $2}'
  )

  if [ -n "$convos_to_kill" ]; then
    echo "Active Claude conversations over cap (${max_active_convos}); cleaning oldest sessions."
    while IFS= read -r pid; do
      [ -z "$pid" ] && continue
      echo "  terminating oldest Claude worker PID $pid"
      kill -TERM "$pid" 2>/dev/null || true
    done <<< "$convos_to_kill"

    sleep 1
    while IFS= read -r pid; do
      [ -z "$pid" ] && continue
      if ps -p "$pid" >/dev/null 2>&1; then
        kill -KILL "$pid" 2>/dev/null || true
      fi
    done <<< "$convos_to_kill"
  fi
}

prd_all_passed() {
  [ -f "$PRD_FILE" ] || return 1
  jq -e '(.userStories // []) | length > 0 and all(.[]; .passes == true)' "$PRD_FILE" >/dev/null 2>&1
}

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
    echo "Ralph interrupted. Progress saved to $PROGRESS_FILE"
  fi

  terminal_record_stop 2>/dev/null || true
  if [ -n "${TERMINAL_LOG:-}" ] && [ -f "$TERMINAL_LOG" ]; then
    run_cleanup_task "terminal SRT" 5 terminal_to_srt "$TERMINAL_LOG" "$EVIDENCE_DIR/captions/terminal.srt" 2>/dev/null || true
    run_cleanup_task "terminal video" 5 terminal_render_video "$TERMINAL_LOG" "$EVIDENCE_DIR/terminal_recording.webm" "$EVIDENCE_DIR/captions/terminal.srt" 2>/dev/null || true
  fi

  if [ ! -f "$EVIDENCE_DIR/captions/terminal.srt" ]; then
    mkdir -p "$EVIDENCE_DIR/captions"
    cat > "$EVIDENCE_DIR/captions/terminal.srt" <<'EOF'
1
00:00:00,000 --> 00:00:03,000
Terminal SRT fallback generated during cleanup
EOF
  fi

  # Record metrics FIRST so evidence_finalize can read them
  if [ -n "${RUN_START:-}" ] && [ -n "${WORKSPACE:-}" ] && [ -n "${PROGRESS_FILE:-}" ] && [ -n "${RALPH_TOOL:-}" ]; then
    run_cleanup_task "metrics record" 5 record_metrics "$outcome" "$PRD_FILE" "$METRICS_FILE" "$WORKSPACE" "$PROGRESS_FILE" "$RALPH_TOOL" "$RUN_START" 2>/dev/null || true
  fi
  if [ ! -f "$METRICS_FILE" ]; then
    mkdir -p "$(dirname "$METRICS_FILE")"
    local tmp_metrics
    tmp_metrics="$(mktemp)"
    if ! jq -n \
      --arg outcome "$outcome" \
      --arg tool "${RALPH_TOOL:-unknown}" \
      --arg workspace "${WORKSPACE:-unknown}" \
      '{outcome:$outcome,duration_seconds:0,duration_human:"0m 0s",stories_passed:0,stories_total:0,files_modified:0,tool:$tool,workspace:$workspace}' \
      > "$tmp_metrics"; then
      echo "Warning: failed to generate fallback metrics via jq" >&2
      printf '%s\n' '{"outcome":"unknown","duration_seconds":0,"duration_human":"0m 0s","stories_passed":0,"stories_total":0,"files_modified":0,"tool":"unknown","workspace":"unknown"}' > "$tmp_metrics"
    fi
    mv "$tmp_metrics" "$METRICS_FILE"
  fi
  run_cleanup_task "evidence finalize" 8 evidence_finalize "$PRD_FILE" "$METRICS_FILE" "$EVIDENCE_DIR" 2>/dev/null || true

  if [ ! -f "$EVIDENCE_DIR/evidence_summary.md" ]; then
    mkdir -p "$EVIDENCE_DIR"
    printf '# Ralph Evidence Summary\n**Result:** pending\n' > "$EVIDENCE_DIR/evidence_summary.md"
  fi

  set -e
  return "$exit_code"
}

# ─── RUN COMMAND ──────────────────────────────────────────────────────────────

cmd_run() {
  RUN_SESSION_ACTIVE=0
  RUN_CLEANUP_DONE=0
  RUN_OUTCOME="interrupted"

  trap 'run_cleanup "$RUN_OUTCOME" "$?" 1' INT TERM
  trap 'run_cleanup "$RUN_OUTCOME" "$?"' EXIT

  # Parse arguments
  MAX_ITERATIONS=10
  RALPH_TOOL="${RALPH_TOOL:-claude}"
  WORKSPACE=""
  while [[ $# -gt 0 ]]; do
    case $1 in
      [0-9]*)
        MAX_ITERATIONS="$1"
        shift
        ;;
      --tool)
        if [[ $# -lt 2 ]]; then
          echo "Error: --tool requires an argument (claude|minimax|codex|amp)" >&2
          cmd_help
          exit 2
        fi
        RALPH_TOOL="$2"
        shift 2
        ;;
      --workspace)
        if [[ $# -lt 2 ]]; then
          echo "Error: --workspace requires a directory argument" >&2
          exit 2
        fi
        WORKSPACE="$2"
        shift 2
        ;;
      *)
        echo "Error: Unknown argument '$1' for run command" >&2
        cmd_help
        exit 2
        ;;
    esac
  done

  if ! AGENT_CMD=$(resolve_tool_cmd "$RALPH_TOOL"); then
    exit 2
  fi

  # Resolve workspace early (needed for prd init branch detection)
  WORKSPACE=$(resolve_workspace "$WORKSPACE" "$REPO_ROOT" 2>/dev/null || echo "$REPO_ROOT")

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
      echo "   Archived to: $ARCHIVE_FOLDER"

      echo "# Ralph Progress Log" > "$PROGRESS_FILE"
      echo "Started: $(date)" >> "$PROGRESS_FILE"
      echo "---" >> "$PROGRESS_FILE"
    fi
  fi

  # Track current branch
  if [ -f "$PRD_FILE" ]; then
    CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || true)
    [ -n "$CURRENT_BRANCH" ] && echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi

  # Initialize progress file
  if [ ! -f "$PROGRESS_FILE" ]; then
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi

  # Initialize prd.json if missing (prevents silent no-PRD runs)
  if [ ! -f "$PRD_FILE" ]; then
    mkdir -p "$(dirname "$PRD_FILE")"
    BRANCH_FOR_PRD=$(git -C "$WORKSPACE" branch --show-current 2>/dev/null || true)
    if [ -z "$BRANCH_FOR_PRD" ]; then
      echo "Error: Workspace $WORKSPACE is not a git repository. Cannot create prd.json template." >&2
      echo "  Use --workspace with a git checkout, or run Ralph from inside a repo." >&2
      exit 2
    fi
    if command -v jq >/dev/null 2>&1; then
      jq -n \
        --arg project "Your Project Name" \
        --arg branch "$BRANCH_FOR_PRD" \
        '{
          project: $project,
          branchName: $branch,
          description: "Describe your task or goal here.",
          exitCriteria: ["Add your exit criteria."],
          userStories: [{
            id: "US-1",
            title: "First user story",
            description: "Describe what needs to be done.",
            acceptanceCriteria: ["Criterion 1", "Criterion 2"],
            priority: 1,
            passes: false,
            notes: ""
          }]
        }' > "$PRD_FILE"
    else
      printf '%s\n' "{\"project\":\"Your Project Name\",\"branchName\":\"$BRANCH_FOR_PRD\",\"description\":\"Describe your task or goal here.\",\"exitCriteria\":[\"Add your exit criteria.\"],\"userStories\":[{\"id\":\"US-1\",\"title\":\"First user story\",\"description\":\"Describe what needs to be done.\",\"acceptanceCriteria\":[\"Criterion 1\",\"Criterion 2\"],\"priority\":1,\"passes\":false,\"notes\":\"\"}]}" > "$PRD_FILE"
    fi
    echo "Created minimal $PRD_FILE template. Edit it with your task/branch/goal, then re-run Ralph." >&2
    echo "  Example: Add user stories, set branchName, and define acceptance criteria." >&2
    exit 2
  fi

  RUN_START=$(date +%s)

  # No-op fast path: if all stories already pass, skip tool/env validation entirely.
  if prd_all_passed; then
    echo "All stories in PRD already pass. Nothing to run."
    RUN_OUTCOME="complete"
    exit 0
  fi

  if [ "$RALPH_TOOL" = "minimax" ]; then
    if [ -z "${MINIMAX_API_KEY:-}" ]; then
      echo "Error: MINIMAX_API_KEY is required for --tool minimax" >&2
      RUN_OUTCOME="config_error"
      exit 2
    fi

    # Remove Claude session vars so nested Claude invocation remains clean.
    while IFS='=' read -r key _; do
      case "$key" in
        CLAUDE_CODE_*) unset "$key" 2>/dev/null || true ;;
      esac
    done < <(env)

    export ANTHROPIC_BASE_URL="https://api.minimax.io/anthropic"
    export ANTHROPIC_AUTH_TOKEN="$MINIMAX_API_KEY"
    export ANTHROPIC_API_KEY="$MINIMAX_API_KEY"
    export ANTHROPIC_MODEL="MiniMax-M2.5"
    # Allow long-running MiniMax turns while keeping a configurable timeout.
    export API_TIMEOUT_MS="${MINIMAX_API_TIMEOUT_MS:-3000000}"
  fi

  # Initialize evidence + dashboard
  evidence_init "$EVIDENCE_DIR" 2>/dev/null || true
  mkdir -p "$RUNTIME_DIR/logs" "$RUNTIME_DIR/state"
  RUN_SESSION_ACTIVE=1

  echo "Starting Ralph - Max iterations: $MAX_ITERATIONS | Tool: $RALPH_TOOL ($AGENT_CMD)"
  [ "$WORKSPACE" != "$REPO_ROOT" ] && echo "  Workspace: $WORKSPACE"

  # Start terminal recording
  TERMINAL_LOG="$EVIDENCE_DIR/recordings/terminal_$(date +%Y%m%d_%H%M%S).log"
  terminal_record_start "ralph-run" "$TERMINAL_LOG" 2>/dev/null || true

  for i in $(seq 1 $MAX_ITERATIONS); do
    echo ""
    echo "==============================================================="
    echo "  Ralph Iteration $i of $MAX_ITERATIONS"
    echo "==============================================================="

    if [ "$RALPH_TOOL" = "codex" ]; then
      # Codex requires prompt as CLI argument — still use build_prompt for workspace awareness
      PROMPT=$(build_prompt "$SCRIPT_DIR/CLAUDE.md" "$PRD_FILE" "$PROGRESS_FILE" "$WORKSPACE" 2>/dev/null || cat "$SCRIPT_DIR/CLAUDE.md")
      if ! OUTPUT=$($AGENT_CMD "$PROMPT" 2>&1 | tee -a "$TERMINAL_LOG"); then
        echo "Error: $RALPH_TOOL failed on iteration $i" >&2
        RUN_OUTCOME="agent_error"
        exit 1
      fi
    else
      # Claude and Amp read prompt from stdin
      unset CLAUDECODE 2>/dev/null || true  # Allow claude inside tmux/subprocess
      if [ "$RALPH_TOOL" = "claude" ] || [ "$RALPH_TOOL" = "minimax" ]; then
        wait_for_convo_slot
      fi
      PROMPT_TEXT=$(build_prompt "$SCRIPT_DIR/CLAUDE.md" "$PRD_FILE" "$PROGRESS_FILE" "$WORKSPACE" 2>/dev/null || cat "$SCRIPT_DIR/CLAUDE.md")
      if ! OUTPUT=$(echo "$PROMPT_TEXT" | $AGENT_CMD 2>&1 | tee -a "$TERMINAL_LOG"); then
        echo "Error: $RALPH_TOOL failed on iteration $i" >&2
        RUN_OUTCOME="agent_error"
        exit 1
      fi
    fi

    # Evidence hooks
    evidence_screenshot "$EVIDENCE_DIR" "post_iter${i}" 2>/dev/null || true
    evidence_captions "$i" "$PRD_FILE" "$EVIDENCE_DIR" 2>/dev/null || true

    if prd_all_passed; then
      echo ""
      echo "Ralph completed all tasks! (all stories in PRD are passes=true)"
      echo "Completed at iteration $i of $MAX_ITERATIONS"
      evidence_browser_proof "$SCRIPT_DIR" "$EVIDENCE_DIR" 2>/dev/null || true
      RUN_OUTCOME="complete"
      exit 0
    fi

    if echo "$OUTPUT" | tr -s '[:space:]' ' ' | grep -qE '<promise>[[:space:]]*COMPLETE[[:space:]]*</promise>'; then
      echo ""
      echo "Ralph completed all tasks!"
      echo "Completed at iteration $i of $MAX_ITERATIONS"
      evidence_browser_proof "$SCRIPT_DIR" "$EVIDENCE_DIR" 2>/dev/null || true
      RUN_OUTCOME="complete"
      exit 0
    fi

    echo "Iteration $i complete. Continuing..."
    sleep 2
  done

  echo ""
  echo "Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
  echo "Check $PROGRESS_FILE for status."
  RUN_OUTCOME="max_iterations"
  exit 1
}

# ─── STATUS COMMAND ───────────────────────────────────────────────────────────
# show_status is sourced from lib/status.sh

cmd_status() {
  if [ "${1:-}" = "--watch" ] || [ "${1:-}" = "-w" ]; then
    while true; do
      clear
      show_status "$PRD_FILE" "$PROGRESS_FILE" "$REPO_ROOT"
      sleep "${RALPH_REFRESH:-3}"
    done
  else
    show_status "$PRD_FILE" "$PROGRESS_FILE" "$REPO_ROOT"
  fi
}

# ─── DASHBOARD COMMAND ────────────────────────────────────────────────────────

cmd_dashboard() {
  trap 'if [ -n "$SERVER_PID" ]; then kill "$SERVER_PID" 2>/dev/null || true; fi' EXIT INT TERM

  EXISTING_PID=$(lsof -ti:$DASHBOARD_PORT 2>/dev/null || true)
  if [ -n "$EXISTING_PID" ]; then
    echo "⚠️  Killing existing process on port $DASHBOARD_PORT (PID: $EXISTING_PID)"
    kill $EXISTING_PID 2>/dev/null || true
    sleep 1
  fi

  echo "🐺 Ralph Dashboard starting on http://localhost:$DASHBOARD_PORT"

  REPO_ROOT="$REPO_ROOT" \
  PRD_FILE="$PRD_FILE" \
  PROGRESS_FILE="$PROGRESS_FILE" \
  DASHBOARD_HTML="$DASHBOARD_HTML" \
  python3 "$SCRIPT_DIR/lib/dashboard.py" --port "$DASHBOARD_PORT" &

  SERVER_PID=$!
  echo "Server PID: $SERVER_PID"
  sleep 1

  if [ "${1:-}" = "--open" ] || [ "${1:-}" = "-o" ]; then
    if command -v open >/dev/null 2>&1; then
      open "http://localhost:$DASHBOARD_PORT"
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "http://localhost:$DASHBOARD_PORT"
    else
      echo "INFO: No browser opener found. Open http://localhost:$DASHBOARD_PORT manually."
    fi
  fi

  echo "Dashboard: http://localhost:$DASHBOARD_PORT"
  echo "Press Ctrl+C to stop"
  wait $SERVER_PID
}

# ─── MAIN DISPATCH ────────────────────────────────────────────────────────────

cmd_help() {
  echo "Ralph Wiggum - PRD-Driven Autonomous Workflow Toolkit"
  echo ""
  echo "Usage: ./ralph.sh <command> [options]"
  echo ""
  echo "Commands:"
  echo "  run [--tool claude|minimax|codex|amp] [N]   Run agent loop (default, N=max iterations)"
  echo "  status [--watch|-w]                 CLI status monitor"
  echo "  dashboard [--open|-o]               Web dashboard on :$DASHBOARD_PORT"
  echo "  help                                Show this help"
  echo ""
  echo "Tool options (--tool):"
  echo "  claude   Claude Code CLI: claude --dangerously-skip-permissions -p (default)"
  echo "  minimax  Claude via MiniMax: requires MINIMAX_API_KEY"
  echo "  codex    Codex CLI:       codex exec --full-auto \"<prompt>\""
  echo "  amp      Amp CLI:         amp -x \"<prompt>\""
  echo ""
  echo "Environment:"
  echo "  RALPH_TOOL   Default tool when --tool is not specified (default: claude)"
}

case "${1:-run}" in
  run)        [ $# -gt 0 ] && shift; cmd_run "$@" ;;
  status)     [ $# -gt 0 ] && shift; cmd_status "$@" ;;
  dashboard)  [ $# -gt 0 ] && shift; cmd_dashboard "$@" ;;
  help|--help|-h) cmd_help ;;
  # Backwards compat: if first arg is a number, treat as `run`
  --tool)
    cmd_run "$@" ;;
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
