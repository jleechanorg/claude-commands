#!/bin/bash
# Wrapper script that sets required env vars and resolves the newest
# jleechanorg-pr-monitor binary available on PATH.

set -euo pipefail

# Source automation env vars if available
if [ -f "$HOME/.automation_env" ]; then
    # shellcheck source=/dev/null
    source "$HOME/.automation_env"
fi

# Optional explicit override (useful for debugging or pinning).
if [ -n "${JLEECHANORG_PR_MONITOR_BIN:-}" ]; then
    if [ ! -x "$JLEECHANORG_PR_MONITOR_BIN" ]; then
        echo "Wrapper error: JLEECHANORG_PR_MONITOR_BIN is not executable: $JLEECHANORG_PR_MONITOR_BIN" >&2
        exit 127
    fi
    exec "$JLEECHANORG_PR_MONITOR_BIN" "$@"
fi

if ! command -v jleechanorg-pr-monitor >/dev/null 2>&1; then
    echo "Wrapper error: jleechanorg-pr-monitor not found on PATH" >&2
    exit 127
fi

# Resolve all candidates and pick the highest semantic version.
_candidates=()
while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    _candidates+=("$candidate")
done < <(which -a jleechanorg-pr-monitor 2>/dev/null | awk '!seen[$0]++')

if [ "${#_candidates[@]}" -eq 0 ]; then
    echo "Wrapper error: unable to enumerate jleechanorg-pr-monitor candidates" >&2
    exit 127
fi
best_cmd="${_candidates[0]}"
best_ver=""

for cmd in "${_candidates[@]}"; do
    [ -x "$cmd" ] || continue

    ver_out="$("$cmd" --version 2>/dev/null || true)"
    ver="$(printf '%s' "$ver_out" | awk '{print $NF}' | tr -d '[:space:]')"

    # If version parsing fails, keep candidate as fallback only.
    if [[ ! "$ver" =~ ^[0-9]+(\.[0-9]+)*$ ]]; then
        continue
    fi

    if [ -z "$best_ver" ]; then
        best_ver="$ver"
        best_cmd="$cmd"
        continue
    fi

    highest="$(printf '%s\n%s\n' "$best_ver" "$ver" | sort -V | tail -n 1)"
    if [ "$highest" = "$ver" ] && [ "$ver" != "$best_ver" ]; then
        best_ver="$ver"
        best_cmd="$cmd"
    fi
done

exec "$best_cmd" "$@"
