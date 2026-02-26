#!/bin/bash
# Ralph Status Monitor - nice formatted output
# Usage: ./status.sh or ./ralph/status.sh [--watch]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD="$SCRIPT_DIR/prd.json"
PROGRESS="$SCRIPT_DIR/progress.txt"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

show_status() {
  clear
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║            🐺 RALPH STATUS MONITOR                     ║"
  echo "╠══════════════════════════════════════════════════════════╣"
  echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                    ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  echo ""

  # Count stories
  TOTAL=$(jq '.userStories | length' "$PRD" 2>/dev/null || echo 0)
  TOTAL=${TOTAL:-0}
  if [ "$TOTAL" -eq 0 ]; then
    PASSED=0
    FAILED=0
    PCT=0
    FILLED=0
    EMPTY=40
  else
    PASSED=$(jq '[.userStories[] | select(.passes == true)] | length' "$PRD")
    FAILED=$((TOTAL - PASSED))
    PCT=$((PASSED * 100 / TOTAL))
    FILLED=$((PCT * 40 / 100))
    EMPTY=$((40 - FILLED))
  fi

  # Progress bar (avoid printf with seq 1 0 which prints one char; guard FILLED/EMPTY)
  BAR_LEN=40
  BAR=""
  [ "$FILLED" -gt 0 ] && BAR=$(printf '%0.s█' $(seq 1 $FILLED 2>/dev/null))
  [ "$EMPTY" -gt 0 ] && BAR+=$(printf '%0.s░' $(seq 1 $EMPTY 2>/dev/null))
  [ -z "$BAR" ] && BAR=$(printf '%0.s░' $(seq 1 $BAR_LEN 2>/dev/null))
  echo "  Progress: [$BAR] $PCT% ($PASSED/$TOTAL)"
  echo ""

  # Phase breakdown (derived from story ID prefixes)
  echo "  ┌─────────────────────────────────┬────────┬────────┐"
  echo "  │ Phase                           │ Status │ Count  │"
  echo "  ├─────────────────────────────────┼────────┼────────┤"

  PREFIXES=$(jq -r '[.userStories[].id | split("-")[0] + "-"] | unique | sort | .[]' "$PRD" 2>/dev/null)
  for PREFIX in $PREFIXES; do
    [ -z "$PREFIX" ] && continue
    LABEL=$(printf "%-31s" "$PREFIX")
    P_TOTAL=$(jq "[.userStories[] | select(.id | startswith(\"$PREFIX\"))] | length" "$PRD")
    P_DONE=$(jq "[.userStories[] | select(.id | startswith(\"$PREFIX\")) | select(.passes == true)] | length" "$PRD")
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

  # Current / next story
  NEXT=$(jq -r '[.userStories[] | select(.passes == false)][0] | "\(.id): \(.title)"' "$PRD")
  echo "  Next story: $NEXT"
  echo ""

  # Recent commits with timestamps
  echo "  Recent commits:"
  git -C "$REPO_ROOT" log --format="    %C(yellow)%h%Creset %C(cyan)%ar%Creset (%ci) %s" -8 2>/dev/null
  echo ""

  # Elapsed time since last commit
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

  # Ralph process info
  RALPH_PIDS=$(pgrep -f "ralph/ralph.sh" 2>/dev/null)
  CLAUDE_PIDS=$(pgrep -f "claude.*--dangerously-skip-permissions" 2>/dev/null | head -3)

  if [ -n "$RALPH_PIDS" ]; then
    RALPH_PID=$(echo "$RALPH_PIDS" | head -1)
    # Get ralph.sh start time
    RALPH_START=$(ps -o lstart= -p "$RALPH_PID" 2>/dev/null | xargs)
    echo "  Ralph: RUNNING (PID $RALPH_PID, started: $RALPH_START)"

    if [ -n "$CLAUDE_PIDS" ]; then
      for CPID in $CLAUDE_PIDS; do
        CTIME=$(ps -o etime= -p "$CPID" 2>/dev/null | xargs)
        CCPU=$(ps -o %cpu= -p "$CPID" 2>/dev/null | xargs)
        CMEM=$(ps -o rss= -p "$CPID" 2>/dev/null | xargs)
        if [ -n "$CMEM" ]; then
          CMEM_MB=$(( CMEM / 1024 ))
        else
          CMEM_MB="?"
        fi
        echo "    └─ Claude worker PID $CPID (elapsed: $CTIME, cpu: ${CCPU}%, mem: ${CMEM_MB}MB)"
      done
    else
      echo "    └─ No active Claude worker (between iterations or starting up)"
    fi
  else
    echo "  Ralph: NOT RUNNING"
  fi

  echo ""

  # Last 15 lines of progress.txt with timestamps highlighted
  echo "  ── Last progress entries ──────────────────────────────"
  tail -15 "$PROGRESS" 2>/dev/null | while IFS= read -r line; do
    # Highlight section headers
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
  # Portable find (no GNU -printf); exclude node_modules
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

if [ "$1" = "--watch" ] || [ "$1" = "-w" ]; then
  while true; do
    show_status
    sleep "${RALPH_REFRESH:-3}"
  done
else
  show_status
fi
