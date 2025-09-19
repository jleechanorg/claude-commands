#!/bin/bash
# deploy.sh - Run /deploy slash command
# Usage: ./deploy.sh [args]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

CANDIDATES=(
    "$PROJECT_ROOT/deploy.sh"
    "$PROJECT_ROOT/scripts/deploy.sh"
)

TARGET_SCRIPT=""
for candidate in "${CANDIDATES[@]}"; do
    if [ -f "$candidate" ]; then
        TARGET_SCRIPT="$candidate"
        break
    fi
done

if [ -z "$TARGET_SCRIPT" ]; then
    echo "❌ deploy.sh not found in project root or scripts/ directory."
    echo "   Expected at one of:"
    for candidate in "${CANDIDATES[@]}"; do
        echo "   - $candidate"
    done
    exit 1
fi

echo "🚀 Running deployment script via: $TARGET_SCRIPT"

echo "ℹ️ Passing arguments: $*"

if [ -x "$TARGET_SCRIPT" ]; then
    exec "$TARGET_SCRIPT" "$@"
else
    exec bash "$TARGET_SCRIPT" "$@"
fi
