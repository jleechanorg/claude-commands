#!/bin/bash
# Memory-enhanced command wrapper for Claude commands

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND="${1:-}"
shift || true
ARGS=("$@")

get_memory_context() {
    local cmd="$1"
    local args="$2"

    MEMORY_CMD="$cmd" MEMORY_ARGS="$args" python3 - <<'PY'
import os

try:
    from memory_integration import get_memory_context_for_command
except Exception:
    raise SystemExit(0)

cmd = os.environ.get("MEMORY_CMD", "")
args = os.environ.get("MEMORY_ARGS", "")
context = get_memory_context_for_command(cmd, args)
if context:
    print("=== MEMORY CONTEXT ===")
    print(context)
    print("=== END MEMORY CONTEXT ===")
PY
}

MEMORY_COMMANDS=("/headless" "/orch" "/list")
should_enhance=false
for mc in "${MEMORY_COMMANDS[@]}"; do
    if [[ "$COMMAND" == "$mc" ]]; then
        should_enhance=true
        break
    fi
done

if [[ "$should_enhance" == "true" ]]; then
    echo -e "${BLUE}🧠 Retrieving relevant memory context...${NC}"
    memory_context="$(get_memory_context "$COMMAND" "${ARGS[*]:-}" 2>/dev/null || true)"
    if [[ -n "$memory_context" ]]; then
        echo -e "${GREEN}✓ Found relevant memories${NC}"
        echo "$memory_context"
    else
        echo -e "${YELLOW}No relevant memories found or memory integration is unavailable${NC}"
    fi
fi

echo -e "\n${BLUE}Executing command: $COMMAND ${ARGS[*]:-}${NC}"

case "$COMMAND" in
    "/headless")
        "$SCRIPT_DIR/headless.sh" "${ARGS[@]}"
        ;;
    "/orch")
        "$SCRIPT_DIR/orch.sh" "${ARGS[@]}"
        ;;
    "/list")
        "$SCRIPT_DIR/list.sh" "${ARGS[@]}"
        ;;
    "/teste")
        "$SCRIPT_DIR/teste.sh" "${ARGS[@]}"
        ;;
    "/tester")
        "$SCRIPT_DIR/tester.sh" "${ARGS[@]}"
        ;;
    "/testerc")
        "$SCRIPT_DIR/testerc.sh" "${ARGS[@]}"
        ;;
    *)
        echo "Command $COMMAND is not mapped in memory_enhanced_wrapper.sh"
        echo "Available commands: /headless, /orch, /list, /teste, /tester, /testerc"
        exit 1
        ;;
esac
