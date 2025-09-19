#!/bin/bash
# localserver.sh - Run /localserver slash command
# Usage: ./localserver.sh [args]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

CANDIDATES=(
    "$PROJECT_ROOT/run_local_server.sh"
    "$PROJECT_ROOT/scripts/run_local_server.sh"
)

TARGET_SCRIPT=""
for candidate in "${CANDIDATES[@]}"; do
    if [ -f "$candidate" ]; then
        TARGET_SCRIPT="$candidate"
        break
    fi
done

if [ -z "$TARGET_SCRIPT" ]; then
    echo "❌ run_local_server.sh not found in project root or scripts/ directory."
    echo "   Expected at one of:"
    for candidate in "${CANDIDATES[@]}"; do
        echo "   - $candidate"
    done
    exit 1
fi

echo "🚀 Starting local development server via: $TARGET_SCRIPT"

if [ "$#" -gt 0 ]; then
    printf "ℹ️ Passing arguments:"
    printf " %q" "$@"
    printf '\n'
else
    echo "ℹ️ Passing arguments: (none)"
fi

if [ -x "$TARGET_SCRIPT" ]; then
    exec "$TARGET_SCRIPT" "$@"
else
    exec bash "$TARGET_SCRIPT" "$@"
fi
