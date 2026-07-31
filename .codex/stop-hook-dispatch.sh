#!/usr/bin/env bash
# stop-hook-dispatch.sh — Codex Stop hook dispatcher (cross-CLI, 2026-07-30)
#
# Replaces the legacy version that ONLY fell back to a per-repo
# stop-git-header-json.sh. This version:
#
# 1. Always runs the cross-CLI status hook first so every Codex session
#    produces a normalized record at ~/.claude/var/cross_cli_status/last.json.
# 2. Then runs mem0_save.py to preserve the legacy memory behavior.
#
# The legacy per-repo stop-git-header-json.sh fallback is retained as a
# tertiary call: only fires when the cross-cli status hook is absent so we
# do not break repos that still rely on the first-line status output.
#
# When all three are wired the response is {"continue":true} (Codex Stop
# hooks must always continue; this hook is purely informational).
set -euo pipefail

input="$(cat)"
log_file="/tmp/codex_hooks_run.log"

printf 'CALLED %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$log_file"

cwd=""
if command -v jq >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | jq -r '.cwd // ""' 2>/dev/null || true)"
fi
printf 'cwd=%s\n---\n' "${cwd:-}" >> "$log_file"

json_continue='{"continue":true}'

# 1. Cross-CLI status hook (primary, always run).
cross_cli_status=""

# 1a. Look in the project cwd first.
if [ -n "$cwd" ]; then
  for cand in \
    "$cwd/.claude/hooks/cross_cli_status.py" \
    "$cwd/.codex/hooks/cross_cli_status.py" \
    "$cwd/codex_hooks/cross_cli_status.py"; do
    if [ -x "$cand" ]; then
      cross_cli_status="$cand"
      break
    fi
  done
fi

# 1b. Fall back to the home hooks dir.
if [ -z "$cross_cli_status" ]; then
  for cand in \
    "$HOME/.claude/hooks/cross_cli_status.py" \
    "$HOME/.codex/hooks/cross_cli_status.py"; do
    if [ -x "$cand" ]; then
      cross_cli_status="$cand"
      break
    fi
  done
fi

if [ -n "$cross_cli_status" ]; then
  printf 'cross-cli: %s\n' "$cross_cli_status" >> "$log_file"
  # Feed the Stop payload through cross_cli_status.py. Stdout is the
  # normalized record; the script writes ~/.claude/var/cross_cli_status/last.json
  # itself. We discard stdout to keep the Codex response clean.
  printf '%s' "$input" | HERMES_HOOK_CLI=codex HERMES_HOOK_EVENT=Stop \
      python3 "$cross_cli_status" >/dev/null 2>&1 || \
      printf 'cross-cli: FAIL (ignored)\n' >> "$log_file"
fi

# 2. mem0 save (legacy behavior — preserves memories across turns).
mem0_save=""
for cand in \
  "$cwd/.codex/hooks/mem0_save.py" \
  "$HOME/.codex/hooks/mem0_save.py"; do
  if [ -x "$cand" ]; then
    mem0_save="$cand"
    break
  fi
done
if [ -n "$mem0_save" ]; then
  printf 'mem0_save: %s\n' "$mem0_save" >> "$log_file"
  source ~/.profile 2>/dev/null || true
  printf '%s' "$input" | python3 "$mem0_save" >/dev/null 2>&1 || \
    printf 'mem0_save: FAIL (ignored)\n' >> "$log_file"
fi

# 3. Legacy stop-git-header-json.sh fallback (preserves first-line status
#    output for repos that still rely on it). Only runs when the cross-cli
#    hook was NOT present so we do not duplicate work.
if [ -z "$cross_cli_status" ] && [ -n "$cwd" ] && \
   [ -x "$cwd/.codex/hooks/stop-git-header-json.sh" ]; then
  printf 'legacy: stop-git-header-json.sh\n' >> "$log_file"
  legacy_response="$(printf '%s' "$input" | \
    "$cwd/.codex/hooks/stop-git-header-json.sh" 2>/dev/null || true)"
  case "$legacy_response" in
    \{*continue*) printf '%s\n' "$legacy_response" ;;
    *) printf '%s\n' "$json_continue" ;;
  esac
  exit 0
fi

printf '%s\n' "$json_continue"
