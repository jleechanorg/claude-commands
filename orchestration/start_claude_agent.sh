#!/bin/bash
# Start a real Claude Code CLI agent with autonomous PR creation capabilities
# This script starts a Claude agent in headless mode with a specific task

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
AGENT_TYPE="${1:-testing}"
TASK_CONTEXT="${2:-}"
PROJECT_ROOT="${3:-$(pwd)}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Agent-specific prompts
case "$AGENT_TYPE" in
    "dead-code")
        AGENT_NAME="Dead Code Agent"
        if [ -f "orchestration/dead_code_agent_prompt.txt" ]; then
            TASK_PROMPT=$(cat orchestration/dead_code_agent_prompt.txt)
        else
            TASK_PROMPT="You are a Dead Code Cleanup Specialist. Create branch fix/remove-dead-code-cleanup and remove any unused code, then use /pr to create a pull request."
        fi
        ;;
    "testing")
        AGENT_NAME="Testing Agent"
        TASK_PROMPT="You are a Testing Specialist. Your task is to run all tests using ./run_tests.sh and fix any failures. Once all tests pass, use /pr to create a pull request documenting the fixes."
        ;;
    "frontend")
        AGENT_NAME="Frontend Agent"
        TASK_PROMPT="You are a Frontend Specialist. Monitor tasks/frontend_tasks.txt for assignments. Complete each task and use /pr to create pull requests for your changes."
        ;;
    "backend")
        AGENT_NAME="Backend Agent"
        TASK_PROMPT="You are a Backend Specialist. Monitor tasks/backend_tasks.txt for assignments. Complete each task and use /pr to create pull requests for your changes."
        ;;
    *)
        log_error "Unknown agent type: $AGENT_TYPE"
        exit 1
        ;;
esac

# Add context if provided
if [ -n "$TASK_CONTEXT" ]; then
    TASK_PROMPT="$TASK_PROMPT

Additional Context:
$TASK_CONTEXT"
fi

# Add PR creation instructions
TASK_PROMPT="$TASK_PROMPT

IMPORTANT: Before starting work:
1. Use /nb command to create a clean branch from latest main
2. This ensures your PR only contains your intended changes

After completing your task:
1. Ensure all tests pass (run ./run_tests.sh)
2. Use the /pr command to create a pull request
3. The PR should include:
   - Clear title describing what was done
   - Detailed description of changes
   - Test results showing all tests pass
   - Any relevant context or findings

Remember to work in the current directory: $PROJECT_ROOT"

log_info "Starting $AGENT_NAME in headless mode..."
log_info "Working directory: $PROJECT_ROOT"

# Start Claude in headless mode with the task
cd "$PROJECT_ROOT"

# Create a unique session name
SESSION_NAME="${AGENT_TYPE}-agent-$(date +%s)"

# Start in tmux for monitoring
# Use configurable path to claude executable
CLAUDE_PATH="${CLAUDE_PATH:-/home/jleechan/.claude/local/claude}"
if [ ! -f "$CLAUDE_PATH" ]; then
    log_error "Claude executable not found at $CLAUDE_PATH. Please set CLAUDE_PATH environment variable."
    exit 1
fi

# Configure security flags (use --dangerously-skip-permissions only if explicitly enabled)
SKIP_PERMISSIONS_FLAG=""
if [ "${CLAUDE_SKIP_PERMISSIONS:-false}" = "true" ]; then
    SKIP_PERMISSIONS_FLAG="--dangerously-skip-permissions"
    log_info "⚠️  Security warning: Running with --dangerously-skip-permissions"
fi

# Default to sonnet for cost efficiency (can override with CLAUDE_AGENT_MODEL env var)
AGENT_MODEL="${CLAUDE_AGENT_MODEL:-claude-sonnet-4-20250514}"

tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_ROOT" \
    "$CLAUDE_PATH -p '$TASK_PROMPT' --output-format stream-json --verbose --model $AGENT_MODEL $SKIP_PERMISSIONS_FLAG; echo 'Agent completed. Press Enter to exit...'; read"

log_info "$AGENT_NAME started in session: $SESSION_NAME"
log_info "Model: $AGENT_MODEL"
log_info "Monitor with: tmux attach -t $SESSION_NAME"

# Return session name for tracking
echo "$SESSION_NAME"