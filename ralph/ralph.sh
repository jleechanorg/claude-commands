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

# ─── RUN COMMAND ──────────────────────────────────────────────────────────────

cmd_run() {
  trap 'echo ""; echo "Ralph interrupted. Progress saved to $PROGRESS_FILE"' INT TERM

  # Parse arguments
  MAX_ITERATIONS=10
  AI_TOOL="claude"
  while [[ $# -gt 0 ]]; do
    case $1 in
      --tool)
        AI_TOOL="$2"
        shift 2
        ;;
      --tool=*)
        AI_TOOL="${1#--tool=}"
        shift
        ;;
      [0-9]*)
        MAX_ITERATIONS="$1"
        shift
        ;;
      *)
        echo "Error: Unknown argument '$1' for run command" >&2
        cmd_help
        return 2
        ;;
    esac
  done

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

  echo "Starting Ralph - Max iterations: $MAX_ITERATIONS (tool: $AI_TOOL)"

  for i in $(seq 1 $MAX_ITERATIONS); do
    echo ""
    echo "==============================================================="
    echo "  Ralph Iteration $i of $MAX_ITERATIONS"
    echo "==============================================================="

    if ! OUTPUT=$("$AI_TOOL" --dangerously-skip-permissions --print < "$SCRIPT_DIR/CLAUDE.md" 2>&1 | tee /dev/stderr); then
      echo "Error: $AI_TOOL failed on iteration $i" >&2
      return 1
    fi

    if echo "$OUTPUT" | tr -s '[:space:]' ' ' | grep -qE '<promise>[[:space:]]*COMPLETE[[:space:]]*</promise>'; then
      echo ""
      echo "Ralph completed all tasks!"
      echo "Completed at iteration $i of $MAX_ITERATIONS"
      return 0
    fi

    echo "Iteration $i complete. Continuing..."
    sleep 2
  done

  echo ""
  echo "Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
  echo "Check $PROGRESS_FILE for status."
  return 1
}

# ─── STATUS COMMAND ───────────────────────────────────────────────────────────

show_status() {
  clear
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║            🐺 RALPH STATUS MONITOR                     ║"
  echo "╠══════════════════════════════════════════════════════════╣"
  echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                    ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  echo ""

  jq_or_default() {
    local expr="$1"
    local default_value="$2"
    shift 2
    local jq_output
    if ! jq_output=$(jq "$expr" "$@" 2>/dev/null); then
      echo "Warning: jq evaluation failed for expression: $expr" >&2
      echo "$default_value"
      return
    fi
    echo "${jq_output:-$default_value}"
  }

  jq_raw_or_default() {
    local expr="$1"
    local default_value="$2"
    shift 2
    local jq_output
    if ! jq_output=$(jq -r "$expr" "$@" 2>/dev/null); then
      echo "Warning: jq raw evaluation failed for expression: $expr" >&2
      echo "$default_value"
      return
    fi
    echo "${jq_output:-$default_value}"
  }

  # Count stories
  TOTAL=$(jq_or_default '.userStories | length' 0 "$PRD_FILE")
  TOTAL=${TOTAL:-0}
  if [ "$TOTAL" -eq 0 ]; then
    PASSED=0; FAILED=0; PCT=0; FILLED=0; EMPTY=40
  else
    PASSED=$(jq_or_default '[.userStories[] | select(.passes == true)] | length' 0 "$PRD_FILE")
    PCT=$((PASSED * 100 / TOTAL))
    FILLED=$((PCT * 40 / 100))
    EMPTY=$((40 - FILLED))
  fi

  # Progress bar
  BAR_LEN=40
  BAR=""
  [ "$FILLED" -gt 0 ] && BAR=$(printf '%0.s█' $(seq 1 $FILLED 2>/dev/null))
  [ "$EMPTY" -gt 0 ] && BAR+=$(printf '%0.s░' $(seq 1 $EMPTY 2>/dev/null))
  [ -z "$BAR" ] && BAR=$(printf '%0.s░' $(seq 1 $BAR_LEN 2>/dev/null))
  echo "  Progress: [$BAR] $PCT% ($PASSED/$TOTAL)"
  echo ""

  # Phase breakdown
  echo "  ┌─────────────────────────────────┬────────┬────────┐"
  echo "  │ Phase                           │ Status │ Count  │"
  echo "  ├─────────────────────────────────┼────────┼────────┤"

  PREFIXES=$(jq_raw_or_default '[.userStories[].id | split("-")[0] + "-"] | unique | sort | .[]' '' "$PRD_FILE")
  for PREFIX in $PREFIXES; do
    [ -z "$PREFIX" ] && continue
    LABEL=$(printf "%-31s" "$PREFIX")
    if ! P_TOTAL=$(jq --arg prefix "$PREFIX" '[.userStories[] | select(.id | startswith($prefix))] | length' "$PRD_FILE" 2>/dev/null); then
      echo "Warning: jq failed while calculating total for prefix $PREFIX" >&2
      P_TOTAL=0
    fi
    if ! P_DONE=$(jq --arg prefix "$PREFIX" '[.userStories[] | select(.id | startswith($prefix)) | select(.passes == true)] | length' "$PRD_FILE" 2>/dev/null); then
      echo "Warning: jq failed while calculating done count for prefix $PREFIX" >&2
      P_DONE=0
    fi
    if [ "$P_DONE" -eq "$P_TOTAL" ]; then
      STATUS="  DONE"
    elif [ "$P_DONE" -gt 0 ]; then
      STATUS="  WIP "
    else
      STATUS="  ----"
    fi
    printf "  │ %s │%s │  %d/%-3d │\n" "$LABEL" "$STATUS" "$P_DONE" "$P_TOTAL"
  done

  echo "  └─────────────────────────────────┴────────┴────────┘"
  echo ""

  # Next story
  NEXT=$(jq_raw_or_default '[.userStories[] | select(.passes == false)][0] | "\(.id): \(.title)"' 'N/A' "$PRD_FILE")
  echo "  Next story: $NEXT"
  echo ""

  # Recent commits
  echo "  Recent commits:"
  if ! git -C "$REPO_ROOT" log --format="    %C(yellow)%h%Creset %C(cyan)%ar%Creset (%ci) %s" -8 2>/dev/null; then
    echo "    (git history unavailable)"
  fi
  echo ""

  # Elapsed since last commit
  LAST_COMMIT_TS=$(git -C "$REPO_ROOT" log -1 --format="%ct" 2>/dev/null)
  NOW_TS=$(date +%s)
  if [ -n "$LAST_COMMIT_TS" ]; then
    ELAPSED=$(( NOW_TS - LAST_COMMIT_TS ))
    ELAPSED_MIN=$(( ELAPSED / 60 ))
    ELAPSED_SEC=$(( ELAPSED % 60 ))
    if [ "$ELAPSED_MIN" -gt 5 ]; then
      echo "  ⚠️  Last commit was ${ELAPSED_MIN}m ${ELAPSED_SEC}s ago (may be stuck)"
    else
      echo "  ✅ Last commit ${ELAPSED_MIN}m ${ELAPSED_SEC}s ago"
    fi
    echo ""
  fi

  # Process info
  RALPH_PIDS=$(pgrep -f "ralph.sh.*run\|ralph/ralph.sh" 2>/dev/null || true)
  CLAUDE_PIDS=$(pgrep -f "claude.*--dangerously-skip-permissions" 2>/dev/null | head -3 || true)

  if [ -n "$RALPH_PIDS" ]; then
    RALPH_PID=$(echo "$RALPH_PIDS" | head -1)
    RALPH_START=$(ps -o lstart= -p "$RALPH_PID" 2>/dev/null | xargs)
    echo "  Ralph: RUNNING (PID $RALPH_PID, started: $RALPH_START)"

    if [ -n "$CLAUDE_PIDS" ]; then
      for CPID in $CLAUDE_PIDS; do
        CTIME=$(ps -o etime= -p "$CPID" 2>/dev/null | xargs)
        CCPU=$(ps -o %cpu= -p "$CPID" 2>/dev/null | xargs)
        CMEM=$(ps -o rss= -p "$CPID" 2>/dev/null | xargs)
        CMEM_MB=$(( ${CMEM:-0} / 1024 ))
        echo "    └─ Claude worker PID $CPID (elapsed: $CTIME, cpu: ${CCPU}%, mem: ${CMEM_MB}MB)"
      done
    else
      echo "    └─ No active Claude worker (between iterations or starting up)"
    fi
  else
    echo "  Ralph: NOT RUNNING"
  fi

  echo ""

  # Last progress entries
  echo "  ── Last progress entries ──────────────────────────────"
  tail -15 "$PROGRESS_FILE" 2>/dev/null | while IFS= read -r line; do
    if [[ "$line" == "## "* ]]; then
      echo "  $(tput bold)$line$(tput sgr0)"
    elif [[ "$line" == *"✅ PASSED"* ]]; then
      echo "  $(tput setaf 2)$line$(tput sgr0)"
    elif [[ "$line" == *"FAILED"* ]] || [[ "$line" == *"ERROR"* ]]; then
      echo "  $(tput setaf 1)$line$(tput sgr0)"
    else
      echo "  $line"
    fi
  done

  echo ""
  echo "  ── File activity (last 2 min) ────────────────────────"
  RECENT=$(find "$REPO_ROOT" \( -name "*.ts" -o -name "*.py" -o -name "*.js" \) -mmin -2 \
    -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -8)
  if [ -n "$RECENT" ]; then
    echo "$RECENT" | while IFS= read -r f; do
      [ -n "$f" ] && echo "    $f"
    done
  else
    echo "    (no source files changed in last 2 min)"
  fi
}

cmd_status() {
  if [ "${1:-}" = "--watch" ] || [ "${1:-}" = "-w" ]; then
    while true; do
      show_status
      sleep "${RALPH_REFRESH:-3}"
    done
  else
    show_status
  fi
}

# ─── DASHBOARD COMMAND ────────────────────────────────────────────────────────

cmd_dashboard() {
  trap 'if [ -n "${SERVER_PID:-}" ]; then kill "${SERVER_PID}" 2>/dev/null || true; fi' EXIT INT TERM

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
  DASHBOARD_PORT="$DASHBOARD_PORT" \
  python3 - <<'PY' &
import http.server, json, subprocess, os, time, socketserver

PORT = int(os.environ['DASHBOARD_PORT'])
REPO = os.environ['REPO_ROOT']
PRD = os.environ['PRD_FILE']
PROGRESS = os.environ['PROGRESS_FILE']
HTML = os.environ['DASHBOARD_HTML']

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_status()).encode())
        elif path == '/' or path == '/index.html':
            try:
                with open(HTML, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Dashboard HTML not found')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def get_status():
    try:
        with open(PRD) as f:
            prd = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        import sys
        print(f'Error reading prd.json: {e}', file=sys.stderr)
        return {'error': f'Cannot read prd.json: {e}'}

    stories = prd.get('userStories', [])
    total = len(stories)
    passed = sum(1 for s in stories if s.get('passes'))

    prefix_groups = {}
    for s in stories:
        sid = s.get('id', '')
        prefix = sid.split('-')[0] + '-' if '-' in sid else sid
        if prefix not in prefix_groups:
            prefix_groups[prefix] = []
        prefix_groups[prefix].append(s)
    phases = []
    for prefix in sorted(prefix_groups.keys()):
        ph_stories = prefix_groups[prefix]
        phases.append({
            'name': prefix.rstrip('-'),
            'total': len(ph_stories),
            'done': sum(1 for s in ph_stories if s.get('passes'))
        })

    next_s = next((s for s in stories if not s.get('passes')), None)
    next_story = f"{next_s['id']}: {next_s['title']}" if next_s else None

    commits = []
    try:
        out = subprocess.check_output(
            ['git', 'log', '--format=%h|%ar|%ct|%s', '-10'],
            cwd=REPO, text=True, timeout=5
        )
        for line in out.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 3)
                commits.append({'hash': parts[0], 'ago': parts[1], 'ts': int(parts[2]), 'message': parts[3]})
    except Exception as e:
        import sys
        print(f'Error reading git log: {e}', file=sys.stderr)

    elapsed = None
    if commits:
        elapsed = int(time.time()) - commits[0]['ts']

    ralph_running = False
    ralph_pid = None
    try:
        out = subprocess.check_output(['pgrep', '-f', 'ralph.sh'], text=True, timeout=3)
        pids = out.strip().split('\n')
        if pids and pids[0]:
            ralph_running = True
            ralph_pid = pids[0]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    return {
        'total': total,
        'passed': passed,
        'phases': phases,
        'next_story': next_story,
        'commits': commits,
        'last_commit_elapsed_sec': elapsed,
        'ralph_running': ralph_running,
        'ralph_pid': ralph_pid,
        'stories': [{'id': s['id'], 'title': s['title'], 'passes': s.get('passes', False)} for s in stories],
    }

with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
    httpd.serve_forever()
PY

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
  echo "  run [N]   Run agent loop (default, N=max iterations)"
  echo "  status [--watch|-w]           CLI status monitor"
  echo "  dashboard [--open|-o]         Web dashboard on :$DASHBOARD_PORT"
  echo "  help                          Show this help"
}

case "${1:-run}" in
  run)        [ $# -gt 0 ] && shift; cmd_run "$@" ;;
  status)     [ $# -gt 0 ] && shift; cmd_status "$@" ;;
  dashboard)  [ $# -gt 0 ] && shift; cmd_dashboard "$@" ;;
  help|--help|-h) cmd_help ;;
  # Backwards compat: if first arg is a number, treat as `run`
  [0-9]*)
    cmd_run "$@" ;;
  *)
    echo "Unknown command: $1"
    cmd_help
    exit 1 ;;
esac
