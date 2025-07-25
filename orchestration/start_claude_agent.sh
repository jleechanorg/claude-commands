#!/bin/bash
# DEPRECATED: This script is legacy - use orchestrate_unified.py for dynamic agents
# Kept only for compatibility with existing workflows

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_error "DEPRECATED: start_claude_agent.sh is no longer supported"
log_error "Use dynamic agent creation instead:"
log_error "  python3 orchestration/orchestrate_unified.py 'your task description'"
log_error ""
log_error "Examples:"
log_error "  python3 orchestration/orchestrate_unified.py 'Fix all failing tests'"
log_error "  python3 orchestration/orchestrate_unified.py 'Remove dead code'"
log_error "  python3 orchestration/orchestrate_unified.py 'Add user authentication'"
exit 1