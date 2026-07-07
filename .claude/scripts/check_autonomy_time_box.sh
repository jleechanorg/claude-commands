#!/usr/bin/env bash
# check_autonomy_time_box.sh — enforce max 3-hour autonomy time-box
# Policy: ~/.claude/CLAUDE.md "Autonomy time-box — max 3 hours without explicit re-approval"
# Returns 0 if within budget, 1 if any tracked flow/worker exceeded 10,800 s.
# Sources of truth (in priority order):
#   1. ~/.hermes/runtime/<flow>-<id>.started_at  — started_at epoch written by /converge, /eloop,
#                                                  /goal_harness, /auton, /f, /goal, /babysit
#   2. tmux session creation epoch for `ao-*` workers (tmux list-sessions -F '#{session_created}')
# Each entry has a companion `.approved_until` file (epoch) that lifts the cap when present.
# Bypass: explicit `CONTINUE N HORUS` / `EXTEND TO N HORUS` in the live user message writes
# `approved_until` = now + N*3600.
set -euo pipefail

MAX_SECONDS=${MAX_AUTONOMY_SECONDS:-10800}
RUNTIME_DIR=${RUNTIME_DIR:-$HOME/.hermes/runtime}
NOW=$(date +%s)
EXCEEDED=()
DETAIL=""

# 1) Started-at markers
if [ -d "$RUNTIME_DIR" ]; then
  for f in "$RUNTIME_DIR"/*.started_at; do
    [ -e "$f" ] || continue
    name=$(basename "$f" .started_at)
    started_at=$(cat "$f" 2>/dev/null || echo "$NOW")
    age=$(( NOW - started_at ))
    approved_until_file="$RUNTIME_DIR/$name.approved_until"
    if [ -e "$approved_until_file" ]; then
      approved_until=$(cat "$approved_until_file" 2>/dev/null || echo 0)
      if [ "$NOW" -lt "$approved_until" ]; then
        DETAIL+="  [OK-extended] $name age=${age}s (approved_until=${approved_until})\n"
        continue
      fi
    fi
    if [ "$age" -gt "$MAX_SECONDS" ]; then
      EXCEEDED+=("$name age=${age}s")
    else
      DETAIL+="  [OK] $name age=${age}s\n"
    fi
  done
fi

# 2) tmux AO workers — check creation epoch
if command -v tmux >/dev/null 2>&1; then
  while IFS=$'\t' read -r session_name created_epoch; do
    case "$session_name" in
      ao-*) ;;
      *) continue ;;
    esac
    age=$(( NOW - created_epoch ))
    if [ "$age" -gt "$MAX_SECONDS" ]; then
      EXCEEDED+=("tmux:$session_name age=${age}s")
    else
      DETAIL+="  [OK-tmux] $session_name age=${age}s\n"
    fi
  done < <(tmux list-sessions -F '#{session_name}	#{session_created}' 2>/dev/null || true)
fi

if [ "${#EXCEEDED[@]}" -gt 0 ]; then
  printf "TIME-BOX EXCEEDED (max=%ss):\n" "$MAX_SECONDS"
  for e in "${EXCEEDED[@]}"; do
    printf "  - %s\n" "$e"
  done
  printf "Detail:\n%b" "$DETAIL"
  printf "Re-approval phrase required in live user message: CONTINUE <N> HORUS or EXTEND TO <N> HORUS\n"
  exit 1
fi

printf "All autonomy flows within %ss budget:\n%b" "$MAX_SECONDS" "$DETAIL"
exit 0
