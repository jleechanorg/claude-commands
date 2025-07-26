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

    # Create shared status file for dynamic agents
    touch "${task_base}/shared_status.txt"

    # Initialize status file
    echo "=== Dynamic Agent Status Dashboard ===" > "${task_base}/shared_status.txt"
    echo "Updated: $(date)" >> "${task_base}/shared_status.txt"
    echo "" >> "${task_base}/shared_status.txt"
    echo "Use 'python3 orchestration/orchestrate_unified.py \"task\"' to create agents" >> "${task_base}/shared_status.txt"

    log_info "Dynamic agent directories created"
}

# Start the Python monitoring coordinator (lightweight, no LLM)
start_monitor() {
    log_info "Starting Python monitoring coordinator..."

    # Start the agent monitor in background
    if [ -f "$SCRIPT_DIR/start_monitor.sh" ]; then
        bash "$SCRIPT_DIR/start_monitor.sh"
        log_info "🤖 Agent monitor started - pings agents every 2 minutes"
    else
        log_warn "start_monitor.sh not found. Monitor unavailable."
    fi
}



# Show system status
show_status() {
    echo
    log_info "Real Claude Agent System Status:"
    echo "├── Redis: $(redis-cli ping 2>/dev/null || echo 'Not running')"
    echo "├── Claude Agents:"

    # Check for dynamic agents
    dynamic_agents=$(tmux list-sessions 2>/dev/null | grep -E "(task-agent-)" | wc -l || echo "0")
    if [ "$dynamic_agents" -gt 0 ]; then
        echo "│   Dynamic Agents: $dynamic_agents active"
        tmux list-sessions 2>/dev/null | grep -E "(task-agent-)" | while read session; do
            session_name=$(echo "$session" | cut -d: -f1)
            echo "│     - $session_name"
        done
    else
        echo "│   Dynamic Agents: None active (use /orch to create)"
    fi

    # Check Python monitor
    if pgrep -f "agent_monitor.py" > /dev/null; then
        echo "│   🤖 Python Monitor: ✅ ACTIVE"
    else
        echo "│   🤖 Python Monitor: ❌ STOPPED"
    fi

    echo "├── Task Results:"
    if [ -d "orchestration/results" ]; then
        result_count=$(ls orchestration/results/ 2>/dev/null | wc -l || echo "0")
        echo "│   Completed tasks: $result_count results available"
    fi

    echo "└── Quick Commands:"
    echo "    /orch 'task description'                             # Create dynamic agents"
    echo "    tmux list-sessions | grep task-agent                 # List active agents"
    echo "    tmux attach -t [task-agent-name]                     # Connect to agent"
    echo "    tail -f /tmp/orchestration_logs/agent_monitor.log     # Monitor system"
    echo "    cd agent_workspace_[task-agent-name] && claude       # Manual agent session"
    echo "    ls /tmp/orchestration_results/                       # View agent results"
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
    echo "  /orch 'task description'    # Create task agents"
    echo "  tmux list-sessions          # List all agent sessions"
    echo "  tmux attach -t task-agent-X # Connect to specific agent"
}

# Stop all agents
stop_system() {
    log_info "Stopping orchestration system..."

    # Kill all agent tmux sessions (task agents only)
    tmux list-sessions -f "#{session_name}" 2>/dev/null | grep -E "(task-agent-)" | while read session; do
        tmux kill-session -t "$session" 2>/dev/null || true
        log_info "Stopped session: $session"
    done

    # Stop Python monitor
    if pgrep -f "agent_monitor.py" > /dev/null; then
        pkill -f "agent_monitor.py"
        log_info "Stopped Python monitor"
    fi

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
    start_monitor

    # Wait for system to start
    sleep 3

    # Test Redis connectivity
    if redis-cli ping &> /dev/null; then
        log_info "✓ Redis connectivity test passed"
    else
        log_error "✗ Redis connectivity test failed"
        return 1
    fi

    # Test Python monitor
    if pgrep -f "agent_monitor.py" > /dev/null; then
        log_info "✓ Python monitor test passed"
    else
        log_error "✗ Python monitor test failed"
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
        start_monitor
        show_status

        if [ "$QUIET_MODE" = false ]; then
            echo
            log_info "🎉 Dynamic Agent Orchestration System started successfully!"
            echo "🤖 Create agents with: /orch 'your task description'"
            echo "🔍 Monitor agents:    tmux list-sessions | grep task-agent"
            echo "📁 View results:      ls /tmp/orchestration_results/"
            echo "📊 Monitor logs:      tail -f /tmp/orchestration_logs/agent_monitor.log"
        fi
        echo ""
        echo "📝 Examples:"
        echo "   /orch 'Fix all failing tests'"
        echo "   /orch 'Add user authentication'"
        echo "   /orch 'Update documentation'"
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
