#!/bin/bash
# Enhanced Claude Code startup script with reliable MCP server detection and orchestration
# Always uses --dangerously-skip-permissions and prompts for model choice
# Uses simplified model names (opus/sonnet) that auto-select latest versions
# Orchestration support added: July 16th, 2025

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
FORCE_CLEAN=false
MODE=""
REMAINING_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            FORCE_CLEAN=true
            shift
            ;;
        -w|--worker)
            MODE="worker"
            shift
            ;;
        -d|--default)
            MODE="default"
            shift
            ;;
        -s|--supervisor)
            MODE="supervisor"
            shift
            ;;
        -q|--qwen)
            MODE="qwen"
            shift
            ;;
        --qwen-local)
            MODE="qwen-local"
            shift
            ;;
        --cerebras)
            MODE="cerebras"
            shift
            ;;
        *)
            REMAINING_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore remaining arguments
set -- "${REMAINING_ARGS[@]}"

# Check for required dependencies
if [ "$MODE" = "qwen" ] || [ "$MODE" = "cerebras" ]; then
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${RED}❌ jq is required but not installed${NC}"
        echo "Please install jq: sudo apt-get install jq (or equivalent for your OS)"
        echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
        read -p ""
        echo -e "${BLUE}Falling back to default mode...${NC}"
        MODE="default"
    fi
fi

# Removed: Self-hosted LLM helper functions
# These are now handled by the dedicated claude_llm_proxy repository
# See: https://github.com/jleechanorg/claude_llm_proxy

# SSH tunnel PID file
SSH_TUNNEL_PID_FILE="/tmp/cerebras_ssh_tunnel.pid"

# Cleanup function for SSH tunnels
cleanup_ssh_tunnel() {
    if [ -f "$SSH_TUNNEL_PID_FILE" ]; then
        local PID=$(cat "$SSH_TUNNEL_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null || true
            echo -e "${BLUE}🧹 Cleaned up SSH tunnel (PID: $PID)${NC}"
        fi
        rm -f "$SSH_TUNNEL_PID_FILE"
    fi
}

# Set up trap for cleanup on exit
trap cleanup_ssh_tunnel EXIT

# Function to check if orchestration is running
is_orchestration_running() {
    # File-based A2A system - Redis no longer required
    # Check if agent monitor process is running (primary indicator)
    if pgrep -f "agent_monitor.py" > /dev/null 2>&1; then
        return 0
    fi

    # Alternative: Check for any active task agents
    if tmux list-sessions 2>/dev/null | grep -q "task-agent-"; then
        return 0
    fi

    return 1
}

# Function to start orchestration in background
start_orchestration_background() {
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Check if orchestration directory exists
    if [ ! -d "$SCRIPT_DIR/orchestration" ]; then
        return 1
    fi

    # Check if start script exists
    if [ ! -f "$SCRIPT_DIR/orchestration/start_system.sh" ]; then
        return 1
    fi

    # Start orchestration silently in background
    # NOTE: start_system.sh starts long-running services, so we don't use timeout on it
    (
        cd "$SCRIPT_DIR/orchestration"

        # File-based A2A system - Redis no longer required
        # Start orchestration agents in quiet mode
        ./start_system.sh --quiet start &> /dev/null
    ) &

    # Store the background process PID for monitoring
    local START_PID=$!

    # Wait for startup with timeout (maximum 10 seconds)
    local max_wait=10
    local wait_time=0
    local startup_success=false

    while [ $wait_time -lt $max_wait ]; do
        # Check if the orchestration monitor is running
        if pgrep -f "agent_monitor.py" > /dev/null 2>&1; then
            # Wait a bit more to ensure it's stable
            sleep 2
            if pgrep -f "agent_monitor.py" > /dev/null 2>&1; then
                startup_success=true
                break
            fi
        fi

        # Also check if the start script is still running
        if ! kill -0 $START_PID 2>/dev/null; then
            # Start script exited, check if it was successful
            wait $START_PID
            local exit_code=$?
            if [ $exit_code -ne 0 ]; then
                # Start script failed
                return 1
            fi
        fi

        sleep 1
        wait_time=$((wait_time + 1))
    done

    if [ "$startup_success" = true ]; then
        return 0
    else
        # Timeout reached or startup failed
        return 1
    fi
}

# Function to setup all required cron jobs
setup_cron_jobs() {
    echo -e "${BLUE}🔍 Verifying cron job configuration...${NC}"

    # Ensure wrapper scripts directory exists
    mkdir -p "$HOME/.local/bin"

    local cron_entries_added=0
    local current_crontab=$(crontab -l 2>/dev/null || echo "")

    # 1. Claude Backup Cron (every 4 hours)
    if ! echo "$current_crontab" | grep -q "claude_backup_cron.sh"; then
        echo -e "${YELLOW}⚠️  Claude backup cron job missing - adding it${NC}"

        # Create wrapper for claude backup
        cat > "$HOME/.local/bin/claude_backup_wrapper.sh" << 'EOF'
#!/bin/bash
# Claude backup wrapper - looks for backup script
if [ -f "$HOME/.local/bin/claude_backup_cron.sh" ]; then
    "$HOME/.local/bin/claude_backup_cron.sh" "$HOME/Library/CloudStorage/Dropbox"
else
    echo "$(date): claude_backup_cron.sh not found" >> /tmp/backup_errors.log
fi
EOF
        chmod +x "$HOME/.local/bin/claude_backup_wrapper.sh"

        # Add to cron
        (echo "$current_crontab"; echo '0 */4 * * * "$HOME/.local/bin/claude_backup_wrapper.sh" 2>&1') | crontab -
        cron_entries_added=$((cron_entries_added + 1))
    fi

    # 2. TMux Cleanup (every 15 minutes)
    if ! echo "$current_crontab" | grep -q "cleanup_completed_agents.py\|tmux_cleanup"; then
        echo -e "${YELLOW}⚠️  TMux cleanup cron job missing - adding it${NC}"

        # Create tmux cleanup wrapper
        cat > "$HOME/.local/bin/tmux_cleanup_wrapper.sh" << 'EOF'
#!/bin/bash
# Find any available WorldArchitect worktree with orchestration
for worktree in "$HOME/projects/worldarchitect.ai" "$HOME/projects/worktree_"*; do
    if [ -f "$worktree/orchestration/cleanup_completed_agents.py" ]; then
        cd "$worktree" && python3 orchestration/cleanup_completed_agents.py
        exit $?
    fi
done
# Fallback: if no worktree found, log the issue
echo "$(date): No WorldArchitect worktree with orchestration found" >> /tmp/tmux_cleanup.log
exit 1
EOF
        chmod +x "$HOME/.local/bin/tmux_cleanup_wrapper.sh"

        # Add to cron
        current_crontab=$(crontab -l 2>/dev/null || echo "")
        (echo "$current_crontab"; echo "*/15 * * * * \$HOME/.local/bin/tmux_cleanup_wrapper.sh >> /tmp/tmux_cleanup.log 2>&1") | crontab -
        cron_entries_added=$((cron_entries_added + 1))
    fi

    # 3. Agent Monitor Disabled (commenting out the problematic entry)
    echo -e "${BLUE}💡 Agent monitor is disabled as requested${NC}"

    # Remove any existing agent monitor cron entries
    current_crontab=$(crontab -l 2>/dev/null || echo "")
    if echo "$current_crontab" | grep -q "agent_monitor.py"; then
        echo -e "${YELLOW}⚠️  Removing existing agent monitor cron entries${NC}"
        # Filter out agent monitor entries
        echo "$current_crontab" | grep -v "agent_monitor.py" | crontab -
    fi

    # Display results
    if [ $cron_entries_added -gt 0 ]; then
        echo -e "${GREEN}✅ Added $cron_entries_added cron job(s) successfully${NC}"
    else
        echo -e "${GREEN}✅ All required cron jobs already configured${NC}"
    fi

    echo -e "${BLUE}📋 Current cron configuration:${NC}"
    crontab -l 2>/dev/null | grep -E "(claude_backup|tmux_cleanup|cleanup_completed_agents)" || echo "  (no matching entries)"
}

# Function to check and start orchestration for non-worker modes
check_orchestration() {
    echo -e "${BLUE}🔍 Verifying orchestration system status...${NC}"

    # First check tmux cleanup automation
    setup_cron_jobs

    if is_orchestration_running; then
        echo -e "${GREEN}✅ Orchestration system already running (no restart needed)${NC}"
    else
        echo -e "${BLUE}🚀 Starting orchestration system...${NC}"
        if start_orchestration_background; then
            echo -e "${GREEN}✅ Orchestration system started successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  Orchestration startup timed out or failed - continuing without it${NC}"
            echo -e "${YELLOW}💡 You can manually start it later with: ./orchestration/start_system.sh start${NC}"
        fi
    fi
}

# Check development environment setup (only if needed)
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found - setting up development environment...${NC}"
    if [ -f "scripts/setup-dev-env.sh" ]; then
        ./scripts/setup-dev-env.sh
        echo -e "${GREEN}✅ Development environment setup complete${NC}"
    else
        echo -e "${YELLOW}⚠️  setup-dev-env.sh not found - you may need to run it manually${NC}"
    fi
else
    # Check if FastMCP is installed in the virtual environment (any Python version)
    if [ -f "venv/bin/activate" ]; then
        if source venv/bin/activate 2>/dev/null; then
            if ! python -c "import fastmcp" >/dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  FastMCP not found in virtual environment - installing MCP dependencies...${NC}"
                if [ -f "mcp_servers/slash_commands/requirements.txt" ]; then
                    if pip install -r mcp_servers/slash_commands/requirements.txt; then
                        echo -e "${GREEN}✅ MCP dependencies installed successfully${NC}"
                    else
                        echo -e "${RED}❌ Failed to install MCP dependencies${NC}"
                        echo -e "${YELLOW}💡 Try running: ./scripts/setup-dev-env.sh${NC}"
                    fi
                else
                    echo -e "${YELLOW}⚠️  Cannot auto-install MCP dependencies - you may need to run setup-dev-env.sh${NC}"
                fi
            fi
        else
            echo -e "${YELLOW}⚠️  Cannot check FastMCP - virtual environment activation failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Virtual environment activate script not found${NC}"
    fi
fi

# Enhanced MCP server detection with better error handling
echo -e "${BLUE}🔍 Checking MCP servers...${NC}"

# Check if claude command is available
if ! command -v claude >/dev/null 2>&1; then
    echo -e "${RED}❌ Claude CLI not found. Please install Claude CLI first.${NC}"
    echo -e "${YELLOW}⚠️  Cannot continue without Claude CLI. Press Enter to exit...${NC}"
    read -p ""
    echo -e "${BLUE}Script cannot function without Claude CLI. Please install it first.${NC}"
    return 1 2>/dev/null || exit 1
fi

# Get MCP server list with better error handling
MCP_LIST=""
if MCP_LIST=$(claude mcp list 2>/dev/null); then
    MCP_SERVERS=$(echo "$MCP_LIST" | grep -E "^[a-zA-Z].*:" | wc -l)

    if [ "$MCP_SERVERS" -eq 0 ]; then
        echo -e "${YELLOW}⚠️ No MCP servers detected${NC}"
        if [ -f "./claude_mcp.sh" ]; then
            echo -e "${BLUE}💡 To install MCP servers, run: ./claude_mcp.sh${NC}"
        else
            echo -e "${BLUE}💡 To setup MCP servers, you can install claude_mcp.sh script${NC}"
        fi
        echo -e "${YELLOW}📝 Continuing with Claude startup (MCP features will be limited)...${NC}"
    else
        echo -e "${GREEN}✅ Found $MCP_SERVERS MCP servers installed:${NC}"

        # Show server list with better formatting
        echo "$MCP_LIST" | head -5 | while read -r line; do
            if [[ "$line" =~ ^([^:]+):.* ]]; then
                server_name="${BASH_REMATCH[1]}"
                echo -e "${GREEN}  ✅ $server_name${NC}"
            fi
        done

        if [ "$MCP_SERVERS" -gt 5 ]; then
            echo -e "${BLUE}  ... and $((MCP_SERVERS - 5)) more${NC}"
        fi
    fi
else
    echo -e "${RED}⚠️ Unable to check MCP servers (claude mcp list failed)${NC}"
    echo -e "${YELLOW}📝 Continuing with Claude startup...${NC}"
fi

echo ""

# Claude Bot Server auto-start (configurable via CLAUDE_BOT_AUTOSTART)
echo -e "${BLUE}🤖 Checking Claude Bot Server status...${NC}"

# Function to check if Claude bot server is running
is_claude_bot_running() {
    if curl -s http://127.0.0.1:5001/health &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start Claude bot server in background
start_claude_bot_background() {
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Check if start script exists
    if [ -f "$SCRIPT_DIR/start-claude-bot.sh" ]; then
        echo -e "${BLUE}🚀 Starting Claude bot server in background...${NC}"

        # Start the server in background, redirecting output to log file
        nohup "$SCRIPT_DIR/start-claude-bot.sh" > "$HOME/.claude-bot-server.log" 2>&1 &

        # Store the PID
        echo $! > "$HOME/.claude-bot-server.pid"

        # Wait a moment for startup
        sleep 3

        return 0
    else
        echo -e "${YELLOW}⚠️  start-claude-bot.sh not found${NC}"
        return 1
    fi
}

# Check and start Claude bot server (disabled by default, set CLAUDE_BOT_AUTOSTART=1 to enable)
if [ "${CLAUDE_BOT_AUTOSTART:-0}" = "1" ]; then
    if is_claude_bot_running; then
        echo -e "${GREEN}✅ Claude bot server already running on port 5001${NC}"
    else
        echo -e "${YELLOW}⚠️  Claude bot server not running${NC}"

        if start_claude_bot_background; then
            # Give it a moment to start up
            sleep 2

            if is_claude_bot_running; then
                echo -e "${GREEN}✅ Claude bot server started successfully${NC}"
                echo -e "${BLUE}📋 Server info:${NC}"
                echo -e "   • Health check: http://127.0.0.1:5001/health"
                echo -e "   • Bot endpoint: http://127.0.0.1:5001/claude"
                echo -e "   • Log file: $HOME/.claude-bot-server.log"
                echo -e "   • PID file: $HOME/.claude-bot-server.pid"
            else
                echo -e "${RED}❌ Failed to start Claude bot server${NC}"
                echo -e "${BLUE}💡 Check log: tail -f $HOME/.claude-bot-server.log${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Could not start Claude bot server automatically${NC}"
            echo -e "${BLUE}💡 To start manually: ./start-claude-bot.sh${NC}"
        fi
    fi
else
    echo -e "${BLUE}💡 Claude bot server auto-start disabled (set CLAUDE_BOT_AUTOSTART=1 to enable)${NC}"
fi


# Memory backup system checks
echo -e "${BLUE}🧠 Verifying Memory MCP backup system status...${NC}"

# Check if memory backup script exists (dedicated repository format)
MEMORY_BACKUP_SCRIPT="$HOME/projects/worldarchitect-memory-backups/scripts/daily_backup.sh"

BACKUP_ISSUES=()

# Check if backup script exists
if [ ! -f "$MEMORY_BACKUP_SCRIPT" ]; then
    BACKUP_ISSUES+=("❌ Backup script not found at $MEMORY_BACKUP_SCRIPT")
elif [ ! -x "$MEMORY_BACKUP_SCRIPT" ]; then
    BACKUP_ISSUES+=("❌ Backup script not executable")
fi


# Check if cron job exists (new dedicated repository format)
if ! crontab -l 2>/dev/null | grep -q "worldarchitect-memory-backups/scripts/daily_backup.sh"; then
    BACKUP_ISSUES+=("❌ Cron job not configured for memory backups")
fi

# Check if memory directory exists
if [ ! -d "$HOME/.cache/mcp-memory" ]; then
    BACKUP_ISSUES+=("❌ Memory cache directory not found")
fi

# Check if backup repository exists (new dedicated repository format)
if [ ! -d "$HOME/projects/worldarchitect-memory-backups" ]; then
    BACKUP_ISSUES+=("❌ Backup repository not found")
fi

# Report status and offer to fix
if [ ${#BACKUP_ISSUES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ Memory backup system is properly configured${NC}"
else
    echo -e "${YELLOW}⚠️ Memory backup system issues detected:${NC}"
    for issue in "${BACKUP_ISSUES[@]}"; do
        echo -e "${YELLOW}  $issue${NC}"
    done

    echo -e "${YELLOW}📝 For setup, use the dedicated memory backup repository at $HOME/projects/worldarchitect-memory-backups${NC}"
fi

echo ""

# Enhanced conversation detection
PROJECT_DIR_NAME=$(pwd | sed 's/[\/._]/-/g')
CLAUDE_PROJECT_DIR="$HOME/.claude/projects/${PROJECT_DIR_NAME}"

# Check if --clean flag was passed
if [ "$FORCE_CLEAN" = true ]; then
    echo -e "${BLUE}🧹 Starting fresh conversation (--clean flag detected)${NC}"
    FLAGS="--dangerously-skip-permissions"
else
    # Enhanced conversation detection with better error handling
    if [ -d "$HOME/.claude/projects" ]; then
        if find "$HOME/.claude/projects" -maxdepth 1 -type d -name "${PROJECT_DIR_NAME}" 2>/dev/null | grep -q .; then
            if find "$HOME/.claude/projects/${PROJECT_DIR_NAME}" -name "*.jsonl" -type f 2>/dev/null | grep -q .; then
                echo -e "${GREEN}📚 Found existing conversation(s) in this project directory${NC}"
                FLAGS="--dangerously-skip-permissions --continue"
            else
                echo -e "${BLUE}📁 Project directory exists but no conversations found${NC}"
                FLAGS="--dangerously-skip-permissions"
            fi
        else
            echo -e "${BLUE}🆕 No existing conversations found for this project${NC}"
            FLAGS="--dangerously-skip-permissions"
        fi
    else
        echo -e "${YELLOW}⚠️ Claude projects directory not found${NC}"
        FLAGS="--dangerously-skip-permissions"
    fi
fi

echo ""

# If mode is specified via command line, use it directly
if [ -n "$MODE" ]; then
    case $MODE in
        worker)
            # Worker mode intentionally skips orchestration check
            # Workers are meant to be lightweight and don't interact with orchestration
            MODEL="sonnet"
            echo -e "${GREEN}🚀 Starting Claude Code in worker mode with $MODEL...${NC}"
            claude --model "$MODEL" $FLAGS "$@"
            ;;
        default)
            # Check orchestration for non-worker modes
            check_orchestration

            # Show orchestration info if available
            if is_orchestration_running; then
                echo ""
                echo -e "${GREEN}💡 Orchestration commands available:${NC}"
                echo -e "   • /orch status     - Check orchestration status"
                echo -e "   • /orch Build X    - Delegate task to AI agents"
                echo -e "   • /orch help       - Show orchestration help"
            fi

            echo -e "${BLUE}🚀 Starting Claude Code with default settings...${NC}"
            claude $FLAGS "$@"
            ;;
        supervisor)
            # Check orchestration for non-worker modes
            check_orchestration

            # Show orchestration info if available
            if is_orchestration_running; then
                echo ""
                echo -e "${GREEN}💡 Orchestration commands available:${NC}"
                echo -e "   • /orch status     - Check orchestration status"
                echo -e "   • /orch Build X    - Delegate task to AI agents"
                echo -e "   • /orch help       - Show orchestration help"
            fi

            MODEL="opus"
            echo -e "${YELLOW}🚀 Starting Claude Code with $MODEL (Latest Opus)...${NC}"
            claude --model "$MODEL" $FLAGS "$@"
            ;;
        qwen)
            echo -e "${BLUE}🤖 Qwen mode selected - using Qwen3-Coder via vast.ai${NC}"
            echo -e "${BLUE}💡 Features: Remote Qwen3-Coder model via vast.ai GPU instances${NC}"
            echo -e "${BLUE}💡 Model: qwen3-coder (optimized for coding tasks)${NC}"
            echo ""

            # Check if API proxy is available
            # TERMINAL SESSION PRESERVATION: Never exit terminal on errors - let users Ctrl+C to go back
            API_PROXY_PATH="$HOME/projects/claude_llm_proxy/api_proxy.py"
            if [ ! -f "$API_PROXY_PATH" ]; then
                echo -e "${RED}❌ LLM self-hosting repository not found${NC}"
                echo -e "${BLUE}💡 LLM proxy (for Qwen and Cerebras) is maintained in the separate claude_llm_proxy repository${NC}"
                echo -e "${BLUE}💡 Clone it with: cd ~/projects && git clone https://github.com/jleechanorg/claude_llm_proxy.git${NC}"
                echo -e "${BLUE}💡 Repository: https://github.com/jleechanorg/claude_llm_proxy${NC}"
                echo -e "${YELLOW}⚠️  Cannot continue without repository. Press Enter to return to default mode...${NC}"
                read -p ""
                echo -e "${BLUE}Falling back to default mode...${NC}"
                MODEL=""
                FLAGS="--dangerously-skip-permissions"
                claude $FLAGS "$@"
                return
            fi

            # Check for Redis environment variables
            if [ -z "$REDIS_HOST" ] || [ -z "$REDIS_PASSWORD" ]; then
                echo -e "${YELLOW}⚠️  Redis credentials not found in environment${NC}"
                echo -e "${BLUE}💡 Set Redis environment variables:${NC}"
                echo -e "${BLUE}   export REDIS_HOST='your-redis-host.redis-cloud.com'${NC}"
                echo -e "${BLUE}   export REDIS_PORT='14339'${NC}"
                echo -e "${BLUE}   export REDIS_PASSWORD='your-redis-password'${NC}"
                echo ""
                echo -e "${YELLOW}⚠️  Continuing without Redis caching...${NC}"
            else
                echo -e "${GREEN}✅ Redis configuration found${NC}"
            fi

            # Automatic vast.ai workflow
            echo -e "${BLUE}🔍 Checking for existing connections...${NC}"

            # Check for existing proxies first
            if curl -s --connect-timeout 3 http://localhost:8000/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Found existing Qwen API proxy on localhost:8000${NC}"
                API_BASE_URL="http://localhost:8000"
            elif curl -s --connect-timeout 3 http://localhost:8001/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Found existing Qwen API proxy on localhost:8001${NC}"
                API_BASE_URL="http://localhost:8001"
            else
                echo -e "${YELLOW}⚠️  No existing proxy found, connecting to vast.ai...${NC}"

                # Check if vastai CLI is installed
                if ! command -v vastai >/dev/null 2>&1; then
                    echo -e "${RED}❌ Vast.ai CLI not found${NC}"
                    echo -e "${BLUE}💡 Install with: pip install vastai${NC}"
                    echo -e "${BLUE}💡 Set API key with: vastai set api-key YOUR_KEY${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                # Check API key
                if ! vastai show user >/dev/null 2>&1; then
                    echo -e "${RED}❌ Vast.ai API key not configured${NC}"
                    echo -e "${BLUE}💡 Set API key with: vastai set api-key YOUR_KEY${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                echo -e "${GREEN}✅ Vast.ai CLI configured${NC}"

                # Look for existing running instances first
                echo -e "${BLUE}🔍 Looking for existing qwen instances...${NC}"
                EXISTING_INSTANCES=$(vastai show instances --raw | jq -r '.[] | select(.actual_status == "running" and (.label // "" | contains("qwen"))) | .id' 2>/dev/null || echo "")

                if [ -n "$EXISTING_INSTANCES" ]; then
                    # Try instances from newest to oldest until one works
                    for INSTANCE_ID in $(echo "$EXISTING_INSTANCES" | tac); do
                        echo -e "${GREEN}✅ Found existing qwen instance: $INSTANCE_ID${NC}"

                        # Get connection details
                        INSTANCE_DETAILS=$(vastai show instance $INSTANCE_ID --raw)
                        SSH_HOST=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_host')
                        SSH_PORT=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_port')

                        echo -e "${BLUE}🔗 Connecting to existing instance $INSTANCE_ID at $SSH_HOST:$SSH_PORT${NC}"

                        # Kill any existing tunnels on port 8000
                        pkill -f "ssh.*8000" 2>/dev/null || true
                        sleep 1

                        # Create SSH tunnel (bypass host key verification for automation)
                        # Clean up any existing tunnel first
                        cleanup_ssh_tunnel
                        ssh -N -L 8000:localhost:8000 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$SSH_PORT" root@"$SSH_HOST" 2>/dev/null &
                        local TUNNEL_PID=$!
                        echo $TUNNEL_PID > "$SSH_TUNNEL_PID_FILE"

                        # Test connection
                        sleep 3
                        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                            echo -e "${GREEN}✅ Connected to existing vast.ai instance $INSTANCE_ID${NC}"
                            API_BASE_URL="http://localhost:8000"
                            break
                        else
                            echo -e "${YELLOW}⚠️  Instance $INSTANCE_ID not responding, trying next...${NC}"
                        fi
                    done

                    if [ -z "$API_BASE_URL" ]; then
                        echo -e "${YELLOW}⚠️  No existing instances responding, will create new one${NC}"
                        INSTANCE_ID=""
                    fi
                fi

                # Create new instance if no existing one found or connection failed
                if [ -z "$API_BASE_URL" ]; then
                    echo -e "${BLUE}🚀 Creating new vast.ai GPU instance...${NC}"
                    echo -e "${BLUE}🔍 Searching for available GPU instances...${NC}"

                    # Fix: Get full results then slice with jq to avoid JSON truncation
                    SEARCH_RESULTS=$(vastai search offers 'cuda_vers >= 12.0 gpu_name:RTX_4090 inet_down >= 50' --raw 2>/dev/null | jq '.[0:10]' 2>/dev/null || echo "[]")

                    # Debug: Check if search results are valid JSON and not empty array
                    if [ -z "$SEARCH_RESULTS" ] || [ "$SEARCH_RESULTS" = "[]" ] || ! echo "$SEARCH_RESULTS" | jq empty 2>/dev/null; then
                        echo -e "${YELLOW}⚠️  No RTX 4090 instances found or invalid response, trying broader search...${NC}"
                        SEARCH_RESULTS=$(vastai search offers 'cuda_vers >= 11.8 gpu_ram >= 8' --raw 2>/dev/null | jq '.[0:10]' 2>/dev/null || echo "[]")

                        if [ -z "$SEARCH_RESULTS" ] || [ "$SEARCH_RESULTS" = "[]" ] || ! echo "$SEARCH_RESULTS" | jq empty 2>/dev/null; then
                            echo -e "${RED}❌ No suitable instances found or vast.ai API error${NC}"
                            echo -e "${BLUE}💡 Try again later or check vast.ai marketplace${NC}"
                            echo -e "${YELLOW}Debug: Search results: $SEARCH_RESULTS${NC}"
                            echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                            read -p ""
                            echo -e "${BLUE}Falling back to default mode...${NC}"
                            MODEL=""
                            FLAGS="--dangerously-skip-permissions"
                            claude $FLAGS "$@"
                            return
                        fi
                    fi

                    # Get the best instance (lowest price) with error handling
                    BEST_INSTANCE=$(echo "$SEARCH_RESULTS" | jq -r '.[0].id // empty' 2>/dev/null)
                    BEST_PRICE=$(echo "$SEARCH_RESULTS" | jq -r '.[0].avail_vol_dph // empty' 2>/dev/null)
                    GPU_NAME=$(echo "$SEARCH_RESULTS" | jq -r '.[0].gpu_name // "Unknown"' 2>/dev/null)

                    # Validate extracted values
                    if [ -z "$BEST_INSTANCE" ] || [ -z "$BEST_PRICE" ]; then
                        echo -e "${RED}❌ Failed to parse instance data from vast.ai response${NC}"
                        echo -e "${YELLOW}Debug: Search results: $SEARCH_RESULTS${NC}"
                        echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                        read -p ""
                        echo -e "${BLUE}Falling back to default mode...${NC}"
                        MODEL=""
                        FLAGS="--dangerously-skip-permissions"
                        claude $FLAGS "$@"
                        return
                    fi

                    echo -e "${GREEN}✅ Selected instance: ID $BEST_INSTANCE ($GPU_NAME) at \$${BEST_PRICE}/hour${NC}"

                    # Prepare environment variables for instance
                    ENV_VARS=""
                    if [ -n "$REDIS_HOST" ]; then
                        ENV_VARS="--env REDIS_HOST=$REDIS_HOST --env REDIS_PORT=${REDIS_PORT:-14339} --env REDIS_PASSWORD=$REDIS_PASSWORD"
                    fi

                    # Create the instance with qwen label
                    echo -e "${BLUE}🏗️  Creating vast.ai instance...${NC}"

                    INSTANCE_CMD="vastai create instance $BEST_INSTANCE --image pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel --disk 60 --ssh --label qwen-$(date +%Y%m%d-%H%M) $ENV_VARS --env GIT_REPO=https://github.com/jleechanorg/claude_llm_proxy.git --onstart-cmd 'git clone \$GIT_REPO /app && cd /app && bash startup_llm.sh'"

                    INSTANCE_RESULT=$(eval $INSTANCE_CMD)
                    # Handle both JSON and Python dict formats for new_contract
                    INSTANCE_ID=$(echo "$INSTANCE_RESULT" | grep -o "'new_contract': [0-9]*" | grep -o '[0-9]*' || echo "$INSTANCE_RESULT" | grep -o '"new_contract": [0-9]*' | grep -o '[0-9]*')

                    if [ -z "$INSTANCE_ID" ]; then
                        echo -e "${RED}❌ Failed to create instance${NC}"
                        echo "Result: $INSTANCE_RESULT"
                        echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                        read -p ""
                        echo -e "${BLUE}Falling back to default mode...${NC}"
                        MODEL=""
                        FLAGS="--dangerously-skip-permissions"
                        claude $FLAGS "$@"
                        return
                    fi

                    echo -e "${GREEN}✅ Instance created: $INSTANCE_ID${NC}"
                    echo -e "${BLUE}⏳ Waiting for instance to start (2-3 minutes)...${NC}"

                    # Wait for instance to start
                    for i in {1..20}; do
                        STATUS=$(vastai show instance $INSTANCE_ID --raw | jq -r '.actual_status')
                        if [ "$STATUS" = "running" ]; then
                            echo -e "${GREEN}✅ Instance is running!${NC}"
                            break
                        fi
                        echo "Status: $STATUS (attempt $i/20)"
                        sleep 15
                    done

                    if [ "$STATUS" != "running" ]; then
                        echo -e "${RED}❌ Instance failed to start within 5 minutes${NC}"
                        echo -e "${BLUE}💡 Check status with: vastai show instance $INSTANCE_ID${NC}"
                        echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                        read -p ""
                        echo -e "${BLUE}Falling back to default mode...${NC}"
                        MODEL=""
                        FLAGS="--dangerously-skip-permissions"
                        claude $FLAGS "$@"
                        return
                    fi

                    # Get SSH connection details
                    INSTANCE_DETAILS=$(vastai show instance $INSTANCE_ID --raw)
                    SSH_HOST=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_host')
                    SSH_PORT=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_port')

                    echo -e "${BLUE}🔗 Connection: $SSH_HOST:$SSH_PORT${NC}"

                    # Wait for startup script to complete
                    echo -e "${BLUE}⏳ Waiting for qwen3-coder setup (5-10 minutes)...${NC}"
                    sleep 60  # Give initial setup time

                    # Test API endpoint availability
                    echo -e "${BLUE}🔍 Testing API endpoint...${NC}"
                    for i in {1..30}; do
                        if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$SSH_PORT" root@"$SSH_HOST" 'curl -s http://localhost:8000/health' 2>/dev/null | grep -q "healthy"; then
                            echo -e "${GREEN}✅ Qwen API is ready!${NC}"
                            break
                        fi
                        echo "Testing API... (attempt $i/30)"
                        sleep 20
                    done

                    # Create SSH tunnel
                    echo -e "${BLUE}🔗 Creating SSH tunnel...${NC}"
                    # Clean up any existing tunnel first
                    cleanup_ssh_tunnel
                    ssh -N -L 8000:localhost:8000 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$SSH_PORT" root@"$SSH_HOST" &
                    TUNNEL_PID=$!
                    echo $TUNNEL_PID > "$SSH_TUNNEL_PID_FILE"

                    # Test connection
                    sleep 2
                    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                        echo -e "${GREEN}✅ SSH tunnel established successfully${NC}"
                        API_BASE_URL="http://localhost:8000"

                        echo -e "${YELLOW}💰 Cost: ~\$${BEST_PRICE}/hour${NC}"
                        echo -e "${YELLOW}⚠️  Instance will continue running. Stop with: vastai stop instance $INSTANCE_ID${NC}"
                    else
                        echo -e "${RED}❌ Failed to establish SSH tunnel${NC}"
                        echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                        read -p ""
                        echo -e "${BLUE}Falling back to default mode...${NC}"
                        MODEL=""
                        FLAGS="--dangerously-skip-permissions"
                        claude $FLAGS "$@"
                        return
                    fi
                fi
            fi

            # Set environment variables to redirect Claude CLI to our proxy
            export ANTHROPIC_BASE_URL="$API_BASE_URL"
            export ANTHROPIC_MODEL="qwen3-coder"

            echo -e "${GREEN}🔧 Environment: ANTHROPIC_BASE_URL=$API_BASE_URL${NC}"
            echo -e "${GREEN}🔧 Model: qwen3-coder${NC}"
            echo -e "${GREEN}🚀 Launching Claude CLI with Qwen3-Coder backend...${NC}"
            echo ""

            # Launch Claude CLI with our proxy
            claude --model "qwen3-coder" $FLAGS "$@"
            ;;
        qwen-local)
            echo -e "${BLUE}🤖 Qwen-local mode selected - using local Qwen3-Coder${NC}"
            echo -e "${BLUE}💡 Features: Local Qwen3-Coder model via Ollama${NC}"
            echo -e "${BLUE}💡 Model: qwen3-coder (optimized for coding tasks)${NC}"
            echo ""

            # Check if API proxy is available
            API_PROXY_PATH="$HOME/projects/claude_llm_proxy/api_proxy.py"
            if [ ! -f "$API_PROXY_PATH" ]; then
                echo -e "${RED}❌ LLM self-hosting repository not found${NC}"
                echo -e "${BLUE}💡 Clone it with: cd ~/projects && git clone https://github.com/jleechanorg/claude_llm_proxy.git${NC}"
                echo -e "${YELLOW}⚠️  Cannot continue without repository. Press Enter to return to default mode...${NC}"
                read -p ""
                echo -e "${BLUE}Falling back to default mode...${NC}"
                MODEL=""
                FLAGS="--dangerously-skip-permissions"
                claude $FLAGS "$@"
                return
            fi

            # Check for existing local proxy first
            if curl -s --connect-timeout 3 http://localhost:8000/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Found existing Qwen API proxy on localhost:8000${NC}"
                API_BASE_URL="http://localhost:8000"
            elif curl -s --connect-timeout 3 http://localhost:8001/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Found existing Qwen API proxy on localhost:8001${NC}"
                API_BASE_URL="http://localhost:8001"
            else
                echo -e "${BLUE}🚀 Starting local Qwen API proxy...${NC}"

                # Kill any existing proxy processes
                pkill -f "api_proxy.py" 2>/dev/null || true

                # Use python3 from PATH or check for venv in current directory
                if [ -f "./venv/bin/python" ]; then
                    PYTHON_CMD="./venv/bin/python"
                else
                    PYTHON_CMD="python3"
                fi

                # Start proxy with environment variables
                cd "$HOME/projects/claude_llm_proxy"
                "$PYTHON_CMD" api_proxy.py &
                PROXY_PID=$!

                # Wait for proxy to start
                sleep 5

                # Test proxy health
                if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                    echo -e "${GREEN}✅ Local Qwen API proxy started successfully${NC}"
                    API_BASE_URL="http://localhost:8000"
                    echo $PROXY_PID > /tmp/cerebras_proxy.pid
                else
                    echo -e "${RED}❌ Failed to start local proxy${NC}"
                    echo -e "${BLUE}💡 Check if Ollama is running and qwen3-coder model is available${NC}"
                    echo -e "${BLUE}💡 Install Ollama: curl -fsSL https://ollama.com/install.sh | sh${NC}"
                    echo -e "${BLUE}💡 Pull model: ollama pull qwen2.5-coder:7b${NC}"
                    kill $PROXY_PID 2>/dev/null || true
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi
            fi

            # Set environment variables to redirect Claude CLI to our proxy
            export ANTHROPIC_BASE_URL="$API_BASE_URL"
            export ANTHROPIC_MODEL="qwen3-coder"

            echo -e "${GREEN}🔧 Environment: ANTHROPIC_BASE_URL=$API_BASE_URL${NC}"
            echo -e "${GREEN}🔧 Model: qwen3-coder${NC}"
            echo -e "${GREEN}🚀 Launching Claude CLI with local Qwen3-Coder backend...${NC}"
            echo ""

            # Launch Claude CLI with our proxy
            claude --model "qwen3-coder" $FLAGS "$@"
            ;;
        cerebras)
            echo -e "${YELLOW}🧠 Cerebras mode selected - using optimized Qwen3-Coder-480B${NC}"
            echo -e "${BLUE}💡 Features: Up to 2,000 tokens/second via Cerebras inference${NC}"
            echo -e "${BLUE}💡 Model: qwen-3-coder-480b (optimized by Cerebras AI)${NC}"
            echo ""

            # Check if API key is provided, source bashrc if needed
            if [ -z "$CEREBRAS_API_KEY" ]; then
                # Try to source bashrc to get the API key
                if [ -f ~/.bashrc ]; then
                    source ~/.bashrc
                fi
            fi

            if [ -z "$CEREBRAS_API_KEY" ]; then
                echo -e "${RED}❌ CEREBRAS_API_KEY environment variable not set${NC}"
                echo -e "${BLUE}💡 Get your API key from: https://cerebras.ai${NC}"
                echo -e "${BLUE}💡 Set it with: export CEREBRAS_API_KEY='your-key-here'${NC}"
                echo -e "${BLUE}💡 Example: CEREBRAS_API_KEY='csk-...' ./claude_start.sh --cerebras${NC}"
                echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                read -p ""
                echo -e "${BLUE}Falling back to default mode...${NC}"
                MODEL=""
                FLAGS="--dangerously-skip-permissions"
                claude $FLAGS "$@"
                return
            fi

            # Test API key validity
            echo -e "${BLUE}🔍 Testing Cerebras API connection...${NC}"
            RESPONSE=$(curl -s -H "Authorization: Bearer $CEREBRAS_API_KEY" https://api.cerebras.ai/v1/models)
            if echo "$RESPONSE" | grep -q "Wrong API Key\|invalid_request_error"; then
                echo -e "${RED}❌ Cerebras API key validation failed${NC}"
                echo -e "${BLUE}💡 Please verify your API key is correct${NC}"
                echo -e "${BLUE}💡 Get a valid key from: https://cerebras.ai${NC}"
                echo -e "${YELLOW}Response: $RESPONSE${NC}"
                echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                read -p ""
                echo -e "${BLUE}Falling back to default mode...${NC}"
                MODEL=""
                FLAGS="--dangerously-skip-permissions"
                claude $FLAGS "$@"
                return
            else
                echo -e "${GREEN}✅ Cerebras API key validated${NC}"
                echo -e "${BLUE}💡 Available models: $(echo "$RESPONSE" | jq -r '.data[]?.id // "qwen-3-coder-480b"' | head -3 | tr '\n' ' ')${NC}"
            fi

            # Check if claude_llm_proxy repo is available
            LLM_SELFHOST_PROXY="$HOME/projects/claude_llm_proxy/cerebras_proxy.py"
            if [ ! -f "$LLM_SELFHOST_PROXY" ]; then
                echo -e "${RED}❌ LLM self-hosting repository not found${NC}"
                echo -e "${BLUE}💡 Cerebras proxy is maintained in the separate claude_llm_proxy repository${NC}"
                echo -e "${BLUE}💡 Clone it with: cd ~/projects && git clone https://github.com/jleechanorg/claude_llm_proxy.git${NC}"
                echo -e "${BLUE}💡 Repository: https://github.com/jleechanorg/claude_llm_proxy${NC}"
                echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                read -p ""
                echo -e "${BLUE}Falling back to default mode...${NC}"
                MODEL=""
                FLAGS="--dangerously-skip-permissions"
                claude $FLAGS "$@"
                return
            fi

            # Start Cerebras API proxy in background
            echo -e "${BLUE}🚀 Starting Cerebras API proxy from claude_llm_proxy repo...${NC}"

            # Kill any existing proxy on port 8002
            pkill -f "cerebras_proxy.py" 2>/dev/null || true

            # Start proxy with Cerebras API key (using external repo)
            # Use python3 from PATH or check for venv in current directory
            if [ -f "./venv/bin/python" ]; then
                PYTHON_CMD="./venv/bin/python"
            else
                PYTHON_CMD="python3"
            fi

            CEREBRAS_API_KEY="$CEREBRAS_API_KEY" "$PYTHON_CMD" "$LLM_SELFHOST_PROXY" &
            PROXY_PID=$!

            # Wait for proxy to start
            sleep 3

            # Test proxy health
            if curl -s http://localhost:8002/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Cerebras API proxy started successfully${NC}"
            else
                echo -e "${RED}❌ Failed to start Cerebras API proxy${NC}"
                kill $PROXY_PID 2>/dev/null || true
                echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                read -p ""
                echo -e "${BLUE}Falling back to default mode...${NC}"
                MODEL=""
                FLAGS="--dangerously-skip-permissions"
                claude $FLAGS "$@"
                return
            fi

            # Store proxy PID for cleanup
            echo $PROXY_PID > /tmp/cerebras_proxy.pid

            # Set environment variables to redirect Claude CLI to our proxy
            export ANTHROPIC_BASE_URL="http://localhost:8002"
            export ANTHROPIC_MODEL="qwen-3-coder-480b"

            echo -e "${GREEN}🔧 Environment: ANTHROPIC_BASE_URL=http://localhost:8002${NC}"
            echo -e "${GREEN}🔧 Model: qwen-3-coder-480b${NC}"
            echo -e "${GREEN}🚀 Launching Claude CLI with Cerebras backend via proxy...${NC}"
            echo ""

            # Launch Claude CLI with our proxy
            claude --model "qwen-3-coder-480b" $FLAGS "$@"
            ;;
    esac
else
    # If no mode specified, show interactive menu
    echo -e "${BLUE}Select mode:${NC}"
    echo -e "${GREEN}1) Worker (Sonnet 4)${NC}"
    echo -e "${BLUE}2) Default${NC}"
    echo -e "${YELLOW}3) Supervisor (Opus 4)${NC}"
    echo -e "${BLUE}4) Qwen (Self-hosted API)${NC}"
    echo -e "${YELLOW}5) Cerebras (Qwen3-Coder-480B - 2000 tokens/sec)${NC}"
    read -p "Choice [2]: " choice

    case ${choice:-2} in
    1)
        # Worker mode intentionally skips orchestration check
        # Workers are meant to be lightweight and don't interact with orchestration
        MODEL="sonnet"
        echo -e "${GREEN}🚀 Starting Claude Code in worker mode with $MODEL...${NC}"
        claude --model "$MODEL" $FLAGS "$@"
        ;;
    2)
        # Check orchestration for non-worker modes
        check_orchestration

        # Show orchestration info if available
        if is_orchestration_running; then
            echo ""
            echo -e "${GREEN}💡 Orchestration commands available:${NC}"
            echo -e "   • /orch status     - Check orchestration status"
            echo -e "   • /orch Build X    - Delegate task to AI agents"
            echo -e "   • /orch help       - Show orchestration help"
        fi

        echo -e "${BLUE}🚀 Starting Claude Code with default settings...${NC}"
        claude $FLAGS "$@"
        ;;
    3)
        # Check orchestration for non-worker modes
        check_orchestration

        # Show orchestration info if available
        if is_orchestration_running; then
            echo ""
            echo -e "${GREEN}💡 Orchestration commands available:${NC}"
            echo -e "   • /orch status     - Check orchestration status"
            echo -e "   • /orch Build X    - Delegate task to AI agents"
            echo -e "   • /orch help       - Show orchestration help"
        fi

        MODEL="opus"
        echo -e "${YELLOW}🚀 Starting Claude Code with $MODEL (Latest Opus)...${NC}"
        claude --model "$MODEL" $FLAGS "$@"
        ;;
    4)
        echo -e "${BLUE}🤖 Qwen mode selected - using self-hosted Qwen3-Coder${NC}"
        echo -e "${BLUE}💡 Features: Local Qwen3-Coder model via vast.ai GPU instances${NC}"
        echo -e "${BLUE}💡 Model: qwen3-coder (optimized for coding tasks)${NC}"
        echo ""

        # Check if API proxy is available
        API_PROXY_PATH="$HOME/projects/claude_llm_proxy/api_proxy.py"
        if [ ! -f "$API_PROXY_PATH" ]; then
            echo -e "${RED}❌ LLM self-hosting repository not found${NC}"
            echo -e "${BLUE}💡 LLM proxy (for Qwen and Cerebras modes) is maintained in the separate claude_llm_proxy repository${NC}"
            echo -e "${BLUE}💡 Clone it with: cd ~/projects && git clone https://github.com/jleechanorg/claude_llm_proxy.git${NC}"
            echo -e "${BLUE}💡 Repository: https://github.com/jleechanorg/claude_llm_proxy${NC}"
            echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
            read -p ""
            echo -e "${BLUE}Falling back to default mode...${NC}"
            MODEL=""
            FLAGS="--dangerously-skip-permissions"
            claude $FLAGS "$@"
            return
        fi

        # Check for Redis environment variables
        if [ -z "$REDIS_HOST" ] || [ -z "$REDIS_PASSWORD" ]; then
            echo -e "${YELLOW}⚠️  Redis credentials not found in environment${NC}"
            echo -e "${BLUE}💡 Set Redis environment variables:${NC}"
            echo -e "${BLUE}   export REDIS_HOST='your-redis-host.redis-cloud.com'${NC}"
            echo -e "${BLUE}   export REDIS_PORT='14339'${NC}"
            echo -e "${BLUE}   export REDIS_PASSWORD='your-redis-password'${NC}"
            echo ""
            echo -e "${YELLOW}⚠️  Continuing without Redis caching...${NC}"
        else
            echo -e "${GREEN}✅ Redis configuration found${NC}"
        fi

        # Qwen Instance Setup Menu
        echo -e "${BLUE}🔍 Checking for available Qwen instances...${NC}"

        # Check for existing proxies first
        if curl -s --connect-timeout 3 http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Found existing Qwen API proxy on localhost:8000${NC}"
            API_BASE_URL="http://localhost:8000"
        elif curl -s --connect-timeout 3 http://localhost:8001/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Found existing Qwen API proxy on localhost:8001${NC}"
            API_BASE_URL="http://localhost:8001"
        else
            echo -e "${YELLOW}⚠️  No existing proxy found${NC}"
            echo ""
            echo -e "${BLUE}Select Qwen setup option:${NC}"
            echo -e "${GREEN}1) Start local proxy (requires Ollama + qwen3-coder)${NC}"
            echo -e "${BLUE}2) Create new vast.ai GPU instance${NC}"
            echo -e "${YELLOW}3) Connect to existing vast.ai instance${NC}"
            echo -e "${RED}4) Exit${NC}"
            read -p "Choice [1]: " qwen_choice

            case ${qwen_choice:-1} in
            1)
                echo -e "${BLUE}🚀 Starting local Qwen API proxy...${NC}"

                # Kill any existing proxy processes
                pkill -f "api_proxy.py" 2>/dev/null || true

                # Use python3 from PATH or check for venv in current directory
                if [ -f "./venv/bin/python" ]; then
                    PYTHON_CMD="./venv/bin/python"
                else
                    PYTHON_CMD="python3"
                fi

                # Start proxy with environment variables
                cd "$HOME/projects/claude_llm_proxy"
                "$PYTHON_CMD" api_proxy.py &
                PROXY_PID=$!

                # Wait for proxy to start
                sleep 5

                # Test proxy health
                if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                    echo -e "${GREEN}✅ Local Qwen API proxy started successfully${NC}"
                    API_BASE_URL="http://localhost:8000"
                    echo $PROXY_PID > /tmp/cerebras_proxy.pid
                else
                    echo -e "${RED}❌ Failed to start local proxy${NC}"
                    echo -e "${BLUE}💡 Check if Ollama is running and qwen3-coder model is available${NC}"
                    kill $PROXY_PID 2>/dev/null || true
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi
                ;;
            2)
                echo -e "${BLUE}🚀 Creating new vast.ai GPU instance...${NC}"

                # Check if vastai CLI is installed
                if ! command -v vastai >/dev/null 2>&1; then
                    echo -e "${RED}❌ Vast.ai CLI not found${NC}"
                    echo -e "${BLUE}💡 Install with: pip install vastai${NC}"
                    echo -e "${BLUE}💡 Set API key with: vastai set api-key YOUR_KEY${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                # Check API key
                if ! vastai show user >/dev/null 2>&1; then
                    echo -e "${RED}❌ Vast.ai API key not configured${NC}"
                    echo -e "${BLUE}💡 Set API key with: vastai set api-key YOUR_KEY${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                echo -e "${GREEN}✅ Vast.ai CLI configured${NC}"
                echo -e "${BLUE}🔍 Searching for available GPU instances...${NC}"

                SEARCH_RESULTS=$(vastai search offers 'cuda_vers >= 12.0 gpu_name:RTX_4090 inet_down >= 50' --raw | head -10)

                if [ -z "$SEARCH_RESULTS" ]; then
                    echo -e "${RED}❌ No suitable instances found${NC}"
                    echo -e "${BLUE}💡 Try broader search: vastai search offers 'cuda_vers >= 11.8'${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                echo -e "${GREEN}✅ Found available instances:${NC}"
                echo "$SEARCH_RESULTS" | jq -r '.[] | "ID: \(.id) | GPU: \(.gpu_name) | Price: $\(.dph_total)/hr | RAM: \(.gpu_ram)GB"' | head -5

                # Get the best instance (lowest price)
                BEST_INSTANCE=$(echo "$SEARCH_RESULTS" | jq -r '.[0].id')
                BEST_PRICE=$(echo "$SEARCH_RESULTS" | jq -r '.[0].dph_total')

                echo ""
                echo -e "${BLUE}💰 Best instance: ID $BEST_INSTANCE at $${BEST_PRICE}/hour${NC}"

                read -p "Create instance? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    echo "Cancelled."
                    exit 0
                fi

                # Prepare environment variables for instance
                ENV_VARS=""
                if [ -n "$REDIS_HOST" ]; then
                    ENV_VARS="--env REDIS_HOST=$REDIS_HOST --env REDIS_PORT=${REDIS_PORT:-14339} --env REDIS_PASSWORD=$REDIS_PASSWORD"
                fi

                # Create the instance
                echo -e "${BLUE}🏗️  Creating vast.ai instance...${NC}"

                INSTANCE_CMD="vastai create instance $BEST_INSTANCE \\
                    --image pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel \\
                    --disk 60 \\
                    --ssh \\
                    $ENV_VARS \\
                    --env GIT_REPO=https://github.com/jleechanorg/claude_llm_proxy.git \\
                    --onstart-cmd 'git clone \$GIT_REPO /app && cd /app && bash startup_llm.sh'"

                INSTANCE_RESULT=$(eval $INSTANCE_CMD)
                INSTANCE_ID=$(echo "$INSTANCE_RESULT" | grep -o '"new_contract": [0-9]*' | grep -o '[0-9]*')

                if [ -z "$INSTANCE_ID" ]; then
                    echo -e "${RED}❌ Failed to create instance${NC}"
                    echo "Result: $INSTANCE_RESULT"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                echo -e "${GREEN}✅ Instance created: $INSTANCE_ID${NC}"
                echo -e "${BLUE}⏳ Waiting for instance to start (this may take 2-3 minutes)...${NC}"

                # Wait for instance to start
                for i in {1..20}; do
                    STATUS=$(vastai show instance $INSTANCE_ID --raw | jq -r '.actual_status')
                    if [ "$STATUS" = "running" ]; then
                        echo -e "${GREEN}✅ Instance is running!${NC}"
                        break
                    fi
                    echo "Status: $STATUS (attempt $i/20)"
                    sleep 15
                done

                if [ "$STATUS" != "running" ]; then
                    echo -e "${RED}❌ Instance failed to start within 5 minutes${NC}"
                    echo -e "${BLUE}💡 Check status with: vastai show instance $INSTANCE_ID${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                # Get SSH connection details
                INSTANCE_DETAILS=$(vastai show instance $INSTANCE_ID --raw)
                SSH_HOST=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_host')
                SSH_PORT=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_port')

                echo ""
                echo -e "${BLUE}🔗 Connection Details:${NC}"
                echo "Instance ID: $INSTANCE_ID"
                echo "SSH Host: $SSH_HOST"
                echo "SSH Port: $SSH_PORT"

                # Wait for startup script to complete
                echo -e "${BLUE}⏳ Waiting for qwen3-coder model download and setup (5-10 minutes)...${NC}"
                echo -e "${YELLOW}💡 You can monitor progress with: ssh -p $SSH_PORT root@$SSH_HOST 'tail -f /tmp/startup.log'${NC}"

                sleep 60  # Give initial setup time

                # Test API endpoint availability
                echo -e "${BLUE}🔍 Testing API endpoint availability...${NC}"

                for i in {1..30}; do
                    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$SSH_PORT" root@"$SSH_HOST" 'curl -s http://localhost:8000/health' 2>/dev/null | grep -q "healthy"; then
                        echo -e "${GREEN}✅ Qwen API is ready!${NC}"
                        break
                    fi
                    echo "Testing API... (attempt $i/30)"
                    sleep 20
                done

                # Create SSH tunnel
                echo -e "${BLUE}🔗 Creating SSH tunnel...${NC}"
                ssh -f -N -L 8000:localhost:8000 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$SSH_PORT" root@"$SSH_HOST"

                # Test connection
                sleep 2
                if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                    echo -e "${GREEN}✅ SSH tunnel established successfully${NC}"
                    API_BASE_URL="http://localhost:8000"

                    # Save connection script for later use
                    cat > "qwen_instance_$INSTANCE_ID.sh" << EOF
#!/bin/bash
# Qwen Instance $INSTANCE_ID Connection Script
# Generated on $(date)

INSTANCE_ID=$INSTANCE_ID
SSH_HOST=$SSH_HOST
SSH_PORT=$SSH_PORT

# Create SSH tunnel
echo "Creating SSH tunnel..."
ssh -f -N -L 8000:localhost:8000 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p \${SSH_PORT} root@\${SSH_HOST}

# Test connection
echo "Testing connection..."
sleep 2
curl http://localhost:8000/health

echo "Ready! Use: ./claude_start.sh --qwen"
EOF
                    chmod +x "qwen_instance_$INSTANCE_ID.sh"

                    echo -e "${GREEN}💾 Connection script saved: qwen_instance_$INSTANCE_ID.sh${NC}"
                    echo -e "${YELLOW}💰 Cost: ~$${BEST_PRICE}/hour${NC}"
                    echo -e "${YELLOW}⚠️  Remember to stop the instance when done: vastai stop instance $INSTANCE_ID${NC}"
                else
                    echo -e "${RED}❌ Failed to establish SSH tunnel${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi
                ;;
            3)
                echo -e "${BLUE}🔗 Connect to existing vast.ai instance${NC}"

                # Check if vastai CLI is installed
                if ! command -v vastai >/dev/null 2>&1; then
                    echo -e "${RED}❌ Vast.ai CLI not found${NC}"
                    echo -e "${BLUE}💡 Install with: pip install vastai${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                echo -e "${BLUE}🔍 Listing your running instances...${NC}"
                vastai show instances --raw | jq -r '.[] | select(.actual_status == "running") | "ID: \(.id) | Host: \(.ssh_host):\(.ssh_port) | GPU: \(.gpu_name)"'

                echo ""
                read -p "Enter instance ID: " INSTANCE_ID

                if [ -z "$INSTANCE_ID" ]; then
                    echo -e "${RED}❌ Instance ID required${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                # Get connection details
                INSTANCE_DETAILS=$(vastai show instance $INSTANCE_ID --raw)
                SSH_HOST=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_host')
                SSH_PORT=$(echo "$INSTANCE_DETAILS" | jq -r '.ssh_port')

                if [ "$SSH_HOST" = "null" ] || [ "$SSH_PORT" = "null" ]; then
                    echo -e "${RED}❌ Invalid instance ID or instance not running${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi

                echo -e "${BLUE}🔗 Connecting to instance $INSTANCE_ID at $SSH_HOST:$SSH_PORT${NC}"

                # Create SSH tunnel
                ssh -f -N -L 8000:localhost:8000 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$SSH_PORT" root@"$SSH_HOST"

                # Test connection
                sleep 2
                if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                    echo -e "${GREEN}✅ Connected to existing vast.ai instance${NC}"
                    API_BASE_URL="http://localhost:8000"
                else
                    echo -e "${RED}❌ Failed to connect to instance${NC}"
                    echo -e "${BLUE}💡 Make sure the instance is running and has the API proxy started${NC}"
                    echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                    read -p ""
                    echo -e "${BLUE}Falling back to default mode...${NC}"
                    MODEL=""
                    FLAGS="--dangerously-skip-permissions"
                    claude $FLAGS "$@"
                    return
                fi
                ;;
            4)
                echo -e "${YELLOW}Exiting qwen mode${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
                read -p ""
                echo -e "${BLUE}Falling back to default mode...${NC}"
                MODEL=""
                FLAGS="--dangerously-skip-permissions"
                claude $FLAGS "$@"
                return
                ;;
            esac
        fi

        # Set environment variables to redirect Claude CLI to our proxy
        export ANTHROPIC_BASE_URL="$API_BASE_URL"
        export ANTHROPIC_MODEL="qwen3-coder"

        echo -e "${GREEN}🔧 Environment: ANTHROPIC_BASE_URL=$API_BASE_URL${NC}"
        echo -e "${GREEN}🔧 Model: qwen3-coder${NC}"
        echo -e "${GREEN}🚀 Launching Claude CLI with Qwen3-Coder backend...${NC}"
        echo ""

        # Launch Claude CLI with our proxy
        claude --model "qwen3-coder" $FLAGS "$@"
        ;;
    5)
        echo -e "${YELLOW}🧠 Cerebras mode selected - using optimized Qwen3-Coder-480B${NC}"
        echo -e "${BLUE}💡 Features: Up to 2,000 tokens/second via Cerebras inference${NC}"
        echo -e "${BLUE}💡 Model: qwen-3-coder-480b (optimized by Cerebras AI)${NC}"
        echo ""

        # Check if API key is provided, source bashrc if needed
        if [ -z "$CEREBRAS_API_KEY" ]; then
            # Try to source bashrc to get the API key
            if [ -f ~/.bashrc ]; then
                source ~/.bashrc
            fi
        fi

        if [ -z "$CEREBRAS_API_KEY" ]; then
            echo -e "${RED}❌ CEREBRAS_API_KEY environment variable not set${NC}"
            echo -e "${BLUE}💡 Get your API key from: https://cerebras.ai${NC}"
            echo -e "${BLUE}💡 Set it with: export CEREBRAS_API_KEY='your-key-here'${NC}"
            echo -e "${BLUE}💡 Example: CEREBRAS_API_KEY='csk-...' ./claude_start.sh --cerebras${NC}"
            exit 0
        fi

        # Test API key validity
        echo -e "${BLUE}🔍 Testing Cerebras API connection...${NC}"
        RESPONSE=$(curl -s -H "Authorization: Bearer $CEREBRAS_API_KEY" https://api.cerebras.ai/v1/models)
        if echo "$RESPONSE" | grep -q "Wrong API Key\|invalid_request_error"; then
            echo -e "${RED}❌ Cerebras API key validation failed${NC}"
            echo -e "${BLUE}💡 Please verify your API key is correct${NC}"
            echo -e "${BLUE}💡 Get a valid key from: https://cerebras.ai${NC}"
            echo -e "${YELLOW}Response: $RESPONSE${NC}"
            echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
            read -p ""
            echo -e "${BLUE}Falling back to default mode...${NC}"
            MODEL=""
            FLAGS="--dangerously-skip-permissions"
            claude $FLAGS "$@"
            return
        else
            echo -e "${GREEN}✅ Cerebras API key validated${NC}"
            echo -e "${BLUE}💡 Available models: $(echo "$RESPONSE" | jq -r '.data[]?.id // "qwen-3-coder-480b"' | head -3 | tr '\n' ' ')${NC}"
        fi

        # Check if claude_llm_proxy repo is available
        LLM_SELFHOST_PROXY="$HOME/projects/claude_llm_proxy/cerebras_proxy.py"
        if [ ! -f "$LLM_SELFHOST_PROXY" ]; then
            echo -e "${RED}❌ LLM self-hosting repository not found${NC}"
            echo -e "${BLUE}💡 Cerebras proxy is maintained in the separate claude_llm_proxy repository${NC}"
            echo -e "${BLUE}💡 Clone it with: cd ~/projects && git clone https://github.com/jleechanorg/claude_llm_proxy.git${NC}"
            echo -e "${BLUE}💡 Repository: https://github.com/jleechanorg/claude_llm_proxy${NC}"
            echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
            read -p ""
            echo -e "${BLUE}Falling back to default mode...${NC}"
            MODEL=""
            FLAGS="--dangerously-skip-permissions"
            claude $FLAGS "$@"
            return
        fi

        # Start Cerebras API proxy in background
        echo -e "${BLUE}🚀 Starting Cerebras API proxy from claude_llm_proxy repo...${NC}"

        # Kill any existing proxy on port 8002
        pkill -f "cerebras_proxy.py" 2>/dev/null || true

        # Start proxy with Cerebras API key (using external repo)
        # Use python3 from PATH or check for venv in current directory
        if [ -f "./venv/bin/python" ]; then
            PYTHON_CMD="./venv/bin/python"
        else
            PYTHON_CMD="python3"
        fi

        CEREBRAS_API_KEY="$CEREBRAS_API_KEY" "$PYTHON_CMD" "$LLM_SELFHOST_PROXY" &
        PROXY_PID=$!

        # Wait for proxy to start
        sleep 3

        # Test proxy health
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Cerebras API proxy started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start Cerebras API proxy${NC}"
            kill $PROXY_PID 2>/dev/null || true
            echo -e "${YELLOW}⚠️  Press Enter to return to default mode...${NC}"
            read -p ""
            echo -e "${BLUE}Falling back to default mode...${NC}"
            MODEL=""
            FLAGS="--dangerously-skip-permissions"
            claude $FLAGS "$@"
            return
        fi

        # Store proxy PID for cleanup
        echo $PROXY_PID > /tmp/cerebras_proxy.pid

        # Set environment variables to redirect Claude CLI to our proxy
        export ANTHROPIC_BASE_URL="http://localhost:8002"
        export ANTHROPIC_MODEL="qwen-3-coder-480b"

        echo -e "${GREEN}🔧 Environment: ANTHROPIC_BASE_URL=http://localhost:8002${NC}"
        echo -e "${GREEN}🔧 Model: qwen-3-coder-480b${NC}"
        echo -e "${GREEN}🚀 Launching Claude CLI with Cerebras backend via proxy...${NC}"
        echo ""

        # Launch Claude CLI with our proxy
        claude --model "qwen-3-coder-480b" $FLAGS "$@"
        ;;
    *)
        echo -e "${YELLOW}Invalid choice, using default${NC}"
        # Check orchestration for non-worker modes
        check_orchestration

        # Show orchestration info if available
        if is_orchestration_running; then
            echo ""
            echo -e "${GREEN}💡 Orchestration commands available:${NC}"
            echo -e "   • /orch status     - Check orchestration status"
            echo -e "   • /orch Build X    - Delegate task to AI agents"
            echo -e "   • /orch help       - Show orchestration help"
        fi

        claude $FLAGS "$@"
        ;;
    esac
fi

# Add helper functions for Claude bot server management
# (These functions are available after claude_start.sh runs)

# Function to stop Claude bot server
stop_claude_bot() {
    if [ -f "$HOME/.claude-bot-server.pid" ]; then
        local PID=$(cat "$HOME/.claude-bot-server.pid")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${BLUE}🛑 Stopping Claude bot server (PID: $PID)...${NC}"
            kill "$PID"
            rm -f "$HOME/.claude-bot-server.pid"
            echo -e "${GREEN}✅ Claude bot server stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  Process not running, cleaning up PID file${NC}"
            rm -f "$HOME/.claude-bot-server.pid"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found${NC}"
    fi
}

# Function to restart Claude bot server
restart_claude_bot() {
    echo -e "${BLUE}🔄 Restarting Claude bot server...${NC}"
    stop_claude_bot
    sleep 2

    if start_claude_bot_background; then
        sleep 3
        if is_claude_bot_running; then
            echo -e "${GREEN}✅ Claude bot server restarted successfully${NC}"
        else
            echo -e "${RED}❌ Failed to restart Claude bot server${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to start Claude bot server during restart${NC}"
    fi
}

# Function to show Claude bot server status
claude_bot_status() {
    if is_claude_bot_running; then
        echo -e "${GREEN}✅ Claude bot server is running on port 5001${NC}"
        if [ -f "$HOME/.claude-bot-server.pid" ]; then
            local PID=$(cat "$HOME/.claude-bot-server.pid")
            echo -e "${BLUE}📋 PID: $PID${NC}"
        fi
        echo -e "${BLUE}📋 Health check: curl http://127.0.0.1:5001/health${NC}"
    else
        echo -e "${RED}❌ Claude bot server is not running${NC}"
    fi
}


# Export functions so they're available in the shell
export -f stop_claude_bot restart_claude_bot claude_bot_status is_claude_bot_running start_claude_bot_background
