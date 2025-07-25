#!/bin/bash
# Simple agent orchestration system startup script

set -e

# Capture original working directory before changing to script directory
ORIGINAL_PWD="$(pwd)"
readonly ORIGINAL_PWD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in quiet mode
QUIET_MODE=false
if [ "$1" = "--quiet" ]; then
    QUIET_MODE=true
    shift  # Remove --quiet from arguments
fi

log_info() {
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${GREEN}[INFO]${NC} $1"
    fi
}

log_warn() {
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${YELLOW}[WARN]${NC} $1"
    fi
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if Redis is running
check_redis() {
    if ! command -v redis-cli &> /dev/null; then
        log_error "Redis CLI not found. Please install Redis first."
        exit 1
    fi

    if ! redis-cli ping &> /dev/null; then
        log_warn "Redis not running. Starting Redis server..."
        redis-server --daemonize yes --bind 127.0.0.1 --protected-mode yes
        sleep 2

        if ! redis-cli ping &> /dev/null; then
            log_error "Failed to start Redis server"
            exit 1
        fi
    fi

    log_info "Redis server is running"
}

# Check if tmux is available
check_tmux() {
    if ! command -v tmux &> /dev/null; then
        log_error "tmux not found. Please install tmux first."
        exit 1
    fi
    log_info "tmux is available"
}

# Check Python dependencies
check_dependencies() {
    if ! python3 -c "import redis" &> /dev/null; then
        log_error "Redis Python module not found. Install with: pip install redis"
        exit 1
    fi
    log_info "Python dependencies available"
}

# Create task directories
setup_directories() {
    # Use TASK_DIR if set (from start_claude_agents), otherwise fallback to relative path for compatibility
    local task_base="${TASK_DIR:-tasks}"
    local log_base="${TASK_DIR:+${TASK_DIR%/tasks}/logs}"
    log_base="${log_base:-logs}"

    mkdir -p "${task_base}"/{pending,active,completed}
    mkdir -p "${log_base}"

    # Create task assignment files for real Claude agents
    touch "${task_base}/frontend_tasks.txt"
    touch "${task_base}/backend_tasks.txt"
    touch "${task_base}/testing_tasks.txt"
    touch "${task_base}/shared_status.txt"

    # Initialize status file
    echo "=== Agent Status Dashboard ===" > "${task_base}/shared_status.txt"
    echo "Updated: $(date)" >> "${task_base}/shared_status.txt"
    echo "" >> "${task_base}/shared_status.txt"

    log_info "Directories and task files created"
}

# Start the Opus master agent
start_opus() {
    log_info "Starting Opus master agent with natural language interface..."

    # Check if opus_terminal.py exists
    if [ -f "$SCRIPT_DIR/opus_terminal.py" ]; then
        tmux new-session -d -s opus-master -c "$SCRIPT_DIR" \
            "python3 opus_terminal.py; read -p 'Press Enter to exit...'"
    else
        log_warn "opus_terminal.py not found. Creating placeholder session..."
        tmux new-session -d -s opus-master -c "$SCRIPT_DIR" \
            'echo "Opus terminal not available. Use Claude agents directly."; read -p "Press Enter to exit..."'
    fi

    log_info "Opus master agent started in tmux session 'opus-master'"
    log_info "💬 Natural language interface ready - use: tmux attach -t opus-master"
}

# Start real Claude Code CLI agents
start_claude_agents() {
    log_info "Starting specialized Claude Code CLI agents..."

    # Use original working directory as project root (respects worktrees)
    PROJECT_ROOT="$ORIGINAL_PWD"

    # Ensure all task/log paths are resolved inside the project root the user invoked from
    export TASK_DIR="$PROJECT_ROOT/tasks"

    # Create directories explicitly in the project root
    mkdir -p "$TASK_DIR" "$PROJECT_ROOT/logs"

    # Validate we're working in the correct directory
    if [[ "$PROJECT_ROOT" == *"worktree"* ]]; then
        log_info "Using worktree: $PROJECT_ROOT"
    else
        log_warn "Not in a worktree. Agents will work in: $PROJECT_ROOT"
        log_info "Consider running from a worktree for isolated development"
    fi

    # Verify orchestration is running from project directory, not system hooks
    if [[ "$(basename "$PROJECT_ROOT")" == "worktree_hooks" ]]; then
        log_error "ERROR: Running from system hooks directory. Please run from a valid worktree:"
        log_error "  Use 'git worktree list' to find available worktrees, then navigate to one and run:"
        log_error "  cd <path-to-worktree> && ./orchestration/start_system.sh"
        exit 1
    fi

    # Check if we have the agent startup script
    if [ ! -f "$SCRIPT_DIR/start_claude_agent.sh" ]; then
        log_error "Agent startup script not found. Creating agents manually..."
        start_claude_agents_manual
        return
    fi

    # Start agents using the new headless script if specific tasks are requested
    if [ "$1" == "dead-code" ]; then
        log_info "Starting Dead Code Cleanup Agent in headless mode..."
        SESSION_NAME=$("$SCRIPT_DIR/start_claude_agent.sh" dead-code "" "$PROJECT_ROOT")
        log_info "Dead Code Agent started in session: $SESSION_NAME"
        echo "dead-code:$SESSION_NAME" >> "${TASK_DIR:-tasks}/agent_sessions.txt"
    elif [ "$1" == "testing" ]; then
        log_info "Starting Testing Agent in headless mode..."
        SESSION_NAME=$("$SCRIPT_DIR/start_claude_agent.sh" testing "" "$PROJECT_ROOT")
        log_info "Testing Agent started in session: $SESSION_NAME"
        echo "testing:$SESSION_NAME" >> "${TASK_DIR:-tasks}/agent_sessions.txt"
    else
        # Dynamic agents only - no predefined agents
        log_info "Dynamic agent system ready. Use orchestrate_unified.py to create task-specific agents."
    fi
}

# Manual agent startup (DEPRECATED - kept for compatibility)
start_claude_agents_manual() {
    log_warn "Generic agents are deprecated. Use dynamic agents via orchestrate_unified.py instead."
    log_info "To create agents, run: python3 orchestration/orchestrate_unified.py 'your task description'"
    return 0

    # DEPRECATED CODE BELOW - DO NOT USE
    # log_info "Starting interactive Claude agents..."
    # # PROJECT_ROOT already set above - no need to reassign
    #
    # # Start Frontend Agent
    # log_info "Starting Frontend Agent (UI/React specialist)..."
    # CLAUDE_PATH="${CLAUDE_PATH:-/home/jleechan/.claude/local/claude}"
    # if [ ! -f "$CLAUDE_PATH" ]; then
    #     log_error "Claude executable not found at $CLAUDE_PATH. Please set CLAUDE_PATH environment variable."
    #     exit 1
    # fi
    # tmux new-session -d -s frontend-agent -c "$PROJECT_ROOT" "$CLAUDE_PATH"
    sleep 2
    tmux send-keys -t frontend-agent "I am the Frontend Agent. I specialize in:" Enter
    tmux send-keys -t frontend-agent "- React components and UI development" Enter
    tmux send-keys -t frontend-agent "- CSS styling and responsive design" Enter
    tmux send-keys -t frontend-agent "- User experience and interface optimization" Enter
    tmux send-keys -t frontend-agent "- Frontend testing and validation" Enter
    tmux send-keys -t frontend-agent "" Enter
    tmux send-keys -t frontend-agent "I monitor ${TASK_DIR:-tasks}/frontend_tasks.txt for assignments." Enter
    tmux send-keys -t frontend-agent "Ready for frontend development tasks!" Enter

    # Start Backend Agent
    log_info "Starting Backend Agent (API/Database specialist)..."
    CLAUDE_PATH="${CLAUDE_PATH:-/home/jleechan/.claude/local/claude}"
    if [ ! -f "$CLAUDE_PATH" ]; then
        log_error "Claude executable not found at $CLAUDE_PATH. Please set CLAUDE_PATH environment variable."
        exit 1
    fi
    tmux new-session -d -s backend-agent -c "$PROJECT_ROOT" "$CLAUDE_PATH"
    sleep 2
    tmux send-keys -t backend-agent "I am the Backend Agent. I specialize in:" Enter
    tmux send-keys -t backend-agent "- API development and Flask/FastAPI backends" Enter
    tmux send-keys -t backend-agent "- Database design and Firestore integration" Enter
    tmux send-keys -t backend-agent "- Server logic and authentication systems" Enter
    tmux send-keys -t backend-agent "- Performance optimization and caching" Enter
    tmux send-keys -t backend-agent "" Enter
    tmux send-keys -t backend-agent "I monitor ${TASK_DIR:-tasks}/backend_tasks.txt for assignments." Enter
    tmux send-keys -t backend-agent "Ready for backend development tasks!" Enter

    # Start Testing Agent
    log_info "Starting Testing Agent (Quality Assurance specialist)..."
    CLAUDE_PATH="${CLAUDE_PATH:-/home/jleechan/.claude/local/claude}"
    if [ ! -f "$CLAUDE_PATH" ]; then
        log_error "Claude executable not found at $CLAUDE_PATH. Please set CLAUDE_PATH environment variable."
        exit 1
    fi
    tmux new-session -d -s testing-agent -c "$PROJECT_ROOT" "$CLAUDE_PATH"
    sleep 2
    tmux send-keys -t testing-agent "I am the Testing Agent. I specialize in:" Enter
    tmux send-keys -t testing-agent "- Comprehensive test suite development" Enter
    tmux send-keys -t testing-agent "- UI testing with Puppeteer and Playwright" Enter
    tmux send-keys -t testing-agent "- API testing and integration testing" Enter
    tmux send-keys -t testing-agent "- Code quality and security analysis" Enter
    tmux send-keys -t testing-agent "" Enter
    tmux send-keys -t testing-agent "I monitor ${TASK_DIR:-tasks}/testing_tasks.txt for assignments." Enter
    tmux send-keys -t testing-agent "Ready for testing and quality assurance tasks!" Enter

    # Update shared status
    {
        echo "=== Agent Status Dashboard ==="
        echo "Updated: $(date)"
        echo ""
        echo "🎨 Frontend Agent: ACTIVE (tmux: frontend-agent)"
        echo "⚙️  Backend Agent: ACTIVE (tmux: backend-agent)"
        echo "🧪 Testing Agent: ACTIVE (tmux: testing-agent)"
        echo "🎯 Opus Master: ACTIVE (tmux: opus-master)"
        echo ""
        echo "Connection commands:"
        echo "  tmux attach -t frontend-agent"
        echo "  tmux attach -t backend-agent"
        echo "  tmux attach -t testing-agent"
        echo "  tmux attach -t opus-master"
    } > "${TASK_DIR:-tasks}/shared_status.txt"

    log_info "✅ All Claude agents started successfully!"
    log_info "🔗 Connect to agents:"
    log_info "   Frontend: tmux attach -t frontend-agent"
    log_info "   Backend:  tmux attach -t backend-agent"
    log_info "   Testing:  tmux attach -t testing-agent"
}

# Show system status
show_status() {
    echo
    log_info "Real Claude Agent System Status:"
    echo "├── Redis: $(redis-cli ping 2>/dev/null || echo 'Not running')"
    echo "├── Claude Agents:"

    # Check for dynamic agents
    dynamic_agents=$(tmux list-sessions 2>/dev/null | grep -E "(task-|dev-|script-|security-|test-)" | wc -l || echo "0")
    if [ "$dynamic_agents" -gt 0 ]; then
        echo "│   Dynamic Agents: $dynamic_agents active"
        tmux list-sessions 2>/dev/null | grep -E "(task-|dev-|script-|security-|test-)" | while read session; do
            session_name=$(echo "$session" | cut -d: -f1)
            echo "│     - $session_name"
        done
    else
        echo "│   Dynamic Agents: None active"
    fi

    # Check Opus master
    if tmux has-session -t "opus-master" 2>/dev/null; then
        echo "│   🎯 Opus Master: ✅ ACTIVE"
    else
        echo "│   🎯 Opus Master: ❌ STOPPED"
    fi

    echo "├── Task Files:"
    if [ -f "${TASK_DIR:-tasks}/frontend_tasks.txt" ]; then
        frontend_count=$(wc -l < "${TASK_DIR:-tasks}/frontend_tasks.txt" 2>/dev/null || echo "0")
        echo "│   Frontend tasks: $frontend_count pending"
    fi
    if [ -f "${TASK_DIR:-tasks}/backend_tasks.txt" ]; then
        backend_count=$(wc -l < "${TASK_DIR:-tasks}/backend_tasks.txt" 2>/dev/null || echo "0")
        echo "│   Backend tasks: $backend_count pending"
    fi
    if [ -f "${TASK_DIR:-tasks}/testing_tasks.txt" ]; then
        testing_count=$(wc -l < "${TASK_DIR:-tasks}/testing_tasks.txt" 2>/dev/null || echo "0")
        echo "│   Testing tasks: $testing_count pending"
    fi

    echo "└── Quick Commands:"
    echo "    python3 orchestration/orchestrate_unified.py 'task'  # Create dynamic agents"
    echo "    tmux list-sessions                                   # List all agents"
    echo "    tmux attach -t [agent-name]                          # Connect to agent"
    echo "    ls orchestration/results/                            # View agent results"
    echo

    # Show shared status if available
    if [ -f "${TASK_DIR:-tasks}/shared_status.txt" ]; then
        echo "📊 Agent Status Dashboard:"
        cat "${TASK_DIR:-tasks}/shared_status.txt" | sed 's/^/   /'
        echo
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  start     - Start the orchestration system"
    echo "  stop      - Stop all agents and cleanup"
    echo "  status    - Show system status"
    echo "  logs      - Show system logs"
    echo "  test      - Run basic functionality test"
    echo
    echo "Interactive usage after start:"
    echo "  tmux attach -t opus-master  # Connect to Opus agent"
    echo "  tmux list-sessions          # List all agent sessions"
}

# Stop all agents
stop_system() {
    log_info "Stopping orchestration system..."

    # Kill all agent tmux sessions (including new Claude agents)
    tmux list-sessions -f "#{session_name}" 2>/dev/null | grep -E "(opus|sonnet|subagent|frontend-agent|backend-agent|testing-agent)" | while read session; do
        tmux kill-session -t "$session" 2>/dev/null || true
        log_info "Stopped session: $session"
    done

    # Also kill by exact session names to ensure cleanup
    for session in opus-master frontend-agent backend-agent testing-agent; do
        if tmux has-session -t "$session" 2>/dev/null; then
            tmux kill-session -t "$session" 2>/dev/null || true
            log_info "Stopped Claude agent session: $session"
        fi
    done

    # Clear Redis agent data
    redis-cli flushdb &> /dev/null || true
    log_info "Cleared Redis data"

    # Update status file
    echo "=== Agent Status Dashboard ===" > "${TASK_DIR:-tasks}/shared_status.txt"
    echo "Updated: $(date)" >> "${TASK_DIR:-tasks}/shared_status.txt"
    echo "" >> "${TASK_DIR:-tasks}/shared_status.txt"
    echo "All agents stopped." >> "${TASK_DIR:-tasks}/shared_status.txt"

    log_info "System stopped"
}

# Run basic functionality test
run_test() {
    log_info "Running basic functionality test..."

    # Start system
    check_redis
    check_tmux
    check_dependencies
    setup_directories
    start_opus

    # Wait for agent to start
    sleep 3

    # Test Redis connectivity
    if redis-cli ping &> /dev/null; then
        log_info "✓ Redis connectivity test passed"
    else
        log_error "✗ Redis connectivity test failed"
        return 1
    fi

    # Test agent registration
    if redis-cli keys "agent:*" | grep -q "opus-master"; then
        log_info "✓ Agent registration test passed"
    else
        log_error "✗ Agent registration test failed"
        return 1
    fi

    # Test tmux session
    if tmux has-session -t opus-master 2>/dev/null; then
        log_info "✓ tmux session test passed"
    else
        log_error "✗ tmux session test failed"
        return 1
    fi

    log_info "All basic tests passed!"
    show_status
}

# Main command handling
case "${1:-start}" in
    start)
        log_info "Starting AI Agent Orchestration System..."
        check_redis
        check_tmux
        check_dependencies
        setup_directories
        start_opus
        # Check if specific agent type requested
        if [ -n "$2" ]; then
            start_claude_agents "$2"
        else
            start_claude_agents
        fi
        show_status

        if [ "$QUIET_MODE" = false ]; then
            echo
            log_info "🎉 Dynamic Agent Orchestration System started successfully!"
            echo "🤖 Create agents with: python3 orchestration/orchestrate_unified.py 'your task'"
            echo "🔍 Monitor agents:    tmux list-sessions | grep -E '(task-|dev-|script-)'"
            echo "📁 View results:      ls orchestration/results/"
        fi
        echo "   Opus:     tmux attach -t opus-master"
        echo ""
        echo "📝 Examples:"
        echo "   python3 orchestration/orchestrate_unified.py 'Fix all failing tests'"
        echo "   python3 orchestration/orchestrate_unified.py 'Add user authentication'"
        echo "   python3 orchestration/orchestrate_unified.py 'Update documentation'"
        echo ""
        echo "View status: $0 status"
        echo "Stop system: $0 stop"
        ;;
    stop)
        stop_system
        ;;
    status)
        show_status
        ;;
    logs)
        log_info "System logs (last 50 lines):"
        tail -n 50 logs/*.log 2>/dev/null || echo "No logs available"
        ;;
    test)
        run_test
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
