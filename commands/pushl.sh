#!/bin/bash
# pushl.sh - Alias for pushlite command
# This is a simple alias that calls the primary pushlite.sh implementation

# Enable strict error handling
set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the project root (two levels up from .claude/commands/)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Call the primary pushlite.sh implementation with all arguments
exec "$PROJECT_ROOT/claude_command_scripts/commands/pushlite.sh" "$@"
