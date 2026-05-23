#!/usr/bin/env bash
# rtk-hook-guard - skips rtk when CLAUDEM_MODE is set
# Used as PreToolUse Bash hook; claudem() sets CLAUDEM_MODE=1

if [[ "${CLAUDEM_MODE:-0}" == "1" || "${CLAUDEW_MODE:-0}" == "1" ]]; then
  # Pass through untouched - no modification
  exec cat
fi

exec rtk hook claude "$@"
