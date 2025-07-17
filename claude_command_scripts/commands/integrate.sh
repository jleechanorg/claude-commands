#!/bin/bash
# integrate.sh - Integration command wrapper for Claude Code
# Calls the main ./integrate.sh script with proper argument handling

set -euo pipefail

# Get the project root directory (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function that matches the main script's capabilities
show_help() {
    echo "integrate.sh - Integration command wrapper for Claude Code"
    echo ""
    echo "Usage: $0 [branch-name] [--force]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message"
    echo "  branch-name     Optional custom branch name (default: dev{timestamp})"
    echo "  --force         Override safety checks for uncommitted/unpushed changes"
    echo ""
    echo "Description:"
    echo "  This wrapper calls the main ./integrate.sh script which provides:"
    echo "  1. Stops test server for current branch (if running)"
    echo "  2. Checks for uncommitted/unpushed changes (with --force override)"
    echo "  3. Updates main branch from origin"
    echo "  4. Creates new branch from latest main"
    echo "  5. Cleans up merged branches automatically"
    echo "  6. Provides comprehensive status reporting"
    echo ""
    echo "Examples:"
    echo "  $0                          # Creates dev{timestamp} branch"
    echo "  $0 feature/my-feature       # Creates feature/my-feature branch"  
    echo "  $0 --force                  # Force mode with dev{timestamp}"
    echo "  $0 newbranch --force        # Creates newbranch in force mode"
    echo ""
    echo "Notes:"
    echo "  - Will stop with errors for uncommitted/unpushed changes (unless --force)"
    echo "  - Automatically deletes clean merged branches"
    echo "  - Sets up proper upstream tracking"
    echo "  - Integrates with test server management"
    exit 0
}

# Parse command line arguments to handle help
if [[ $# -gt 0 ]]; then
    case "$1" in
        -h|--help)
            show_help
            ;;
    esac
fi

echo -e "${BLUE}🔄 /integrate - Integration Command Wrapper${NC}"
echo "============================================="
echo ""

# Change to project root to ensure proper execution context
cd "$PROJECT_ROOT"

# Call the main integrate.sh script with all arguments passed through
echo -e "${GREEN}📞 Calling main integration script: ./integrate.sh${NC}"
if [[ $# -gt 0 ]]; then
    echo "   Arguments: $*"
fi
echo ""

# Execute the main integrate.sh script with all arguments
exec "$PROJECT_ROOT/integrate.sh" "$@"