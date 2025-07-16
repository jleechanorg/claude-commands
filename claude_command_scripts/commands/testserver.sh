#!/bin/bash
# testserver.sh - Implement /testserver slash command
# Usage: ./testserver.sh [action] [branch]

set -e

# Get the project root directory (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source shared utilities
source "$PROJECT_ROOT/claude_command_scripts/port-utils.sh"

# Change to project root
cd "$PROJECT_ROOT"

# Function to display usage
show_usage() {
    cat << 'EOF'
🔧 Test Server Management

Usage: /testserver [action] [branch]

Actions:
  start [branch]  - Start test server for branch (defaults to current branch)
  stop [branch]   - Stop test server for branch (defaults to current branch)  
  list           - List all running test servers
  cleanup        - Stop all test servers
  status         - Show status of current branch server

Examples:
  /testserver start                  # Start server for current branch
  /testserver start feature-auth     # Start server for feature-auth branch
  /testserver stop                   # Stop server for current branch
  /testserver list                   # Show all running servers
  /testserver cleanup                # Stop all servers

Features:
• Automatic port allocation (8081-8090)
• Branch-specific logging in /tmp/worldarchitectai_logs/
• Process management with PID tracking
• Conflict detection and resolution
• Integration with /push and /integrate commands

EOF
}

# Parse arguments
ACTION="${1:-help}"
BRANCH_ARG="$2"

# Delegate to test_server_manager.sh
case "$ACTION" in
    start|stop|list|cleanup)
        if [ -f "$PROJECT_ROOT/test_server_manager.sh" ]; then
            if [ -n "$BRANCH_ARG" ]; then
                exec "$PROJECT_ROOT/test_server_manager.sh" "$ACTION" "$BRANCH_ARG"
            else
                exec "$PROJECT_ROOT/test_server_manager.sh" "$ACTION"
            fi
        else
            echo -e "${RED}❌ test_server_manager.sh not found${NC}"
            exit 1
        fi
        ;;
    status)
        # Show status for current branch
        current_branch=$(git branch --show-current)
        echo -e "${BLUE}📊 Test Server Status for '$current_branch'${NC}"
        echo "=========================="
        
        if [ -f "$PROJECT_ROOT/test_server_manager.sh" ]; then
            # Check if server is running
            "$PROJECT_ROOT/test_server_manager.sh" list | grep -A 4 "^✅ $current_branch" || {
                echo -e "${YELLOW}⚠️  No server running for branch '$current_branch'${NC}"
                echo ""
                echo "💡 To start a server:"
                echo "   /testserver start"
            }
        else
            echo -e "${RED}❌ test_server_manager.sh not found${NC}"
            exit 1
        fi
        ;;
    help|--help|-h|"")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown action: $ACTION${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac