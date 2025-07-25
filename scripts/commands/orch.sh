#!/bin/bash
# orch.sh - Orchestration command wrapper (alias for orchestrate)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Execute the orchestrate.py script
exec python3 "$PROJECT_ROOT/.claude/commands/orchestrate.py" "$@"