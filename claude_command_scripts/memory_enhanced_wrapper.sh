#!/bin/bash
# Memory-enhanced command wrapper for Claude commands
# This demonstrates how to integrate memory context into slash commands

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get command and arguments
COMMAND="${1:-}"
shift || true
ARGS="$*"

# Function to get memory context via Python
get_memory_context() {
    local cmd="$1"
    local args="$2"

    # Use environment variables to safely pass arguments
    export MEMORY_CMD="$cmd"
    export MEMORY_ARGS="$args"

    python3 -c "
import sys
import os
sys.path.insert(0, 'mvp_site')
from memory_integration import enhance_slash_command

cmd = os.environ.get('MEMORY_CMD', '')
args = os.environ.get('MEMORY_ARGS', '')

context = enhance_slash_command(cmd, args)
if context:
    print('=== MEMORY CONTEXT ===')
    print(context)
    print('=== END MEMORY CONTEXT ===')
"
}

# Check if command should be enhanced
MEMORY_COMMANDS=("/learn" "/debug" "/think" "/analyze" "/fix")

# Check if this command should get memory enhancement
should_enhance=false
for mc in "${MEMORY_COMMANDS[@]}"; do
    if [[ "$COMMAND" == "$mc" ]]; then
        should_enhance=true
        break
    fi
done

# Get memory context if applicable
if [[ "$should_enhance" == "true" ]]; then
    echo -e "${BLUE}🧠 Retrieving relevant memory context...${NC}"
    memory_context=$(get_memory_context "$COMMAND" "$ARGS" 2>/dev/null || echo "")

    if [[ -n "$memory_context" ]]; then
        echo -e "${GREEN}✓ Found relevant memories${NC}"
        echo "$memory_context"
    else
        echo -e "${YELLOW}No relevant memories found${NC}"
    fi
fi

# Execute the actual command
echo -e "\n${BLUE}Executing command: $COMMAND $ARGS${NC}"

# Map commands to their script implementations
case "$COMMAND" in
    "/integrate")
        ./claude_command_scripts/commands/integrate.sh
        ;;
    "/push")
        ./claude_command_scripts/commands/push.sh
        ;;
    "/nb")
        ./claude_command_scripts/commands/new-branch.sh $ARGS
        ;;
    "/testui")
        ./claude_command_scripts/commands/test-ui.sh $ARGS
        ;;
    *)
        echo "Command $COMMAND not yet implemented in wrapper"
        echo "Memory context was retrieved but command execution skipped"
        ;;
esac
