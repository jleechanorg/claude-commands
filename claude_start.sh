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
        *)
            REMAINING_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore remaining arguments
set -- "${REMAINING_ARGS[@]}"

# Function to check if orchestration is running
is_orchestration_running() {
    # Check if Redis is accessible
    if ! command -v redis-cli >/dev/null 2>&1 || ! redis-cli ping &> /dev/null; then
        return 1
    fi
    
    # Check if orchestration agents exist
    if tmux has-session -t opus-master 2>/dev/null; then
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
    (
        cd "$SCRIPT_DIR/orchestration"
        
        # Start Redis if not running
        if ! redis-cli ping &> /dev/null; then
            redis-server --daemonize yes --bind 127.0.0.1 --protected-mode yes &> /dev/null || true
            sleep 1
        fi
        
        # Start orchestration agents in quiet mode
        ./start_system.sh --quiet start &> /dev/null &
    )
    
    # Wait a moment for startup
    sleep 2
    
    return 0
}

# Function to check and start orchestration for non-worker modes
check_orchestration() {
    echo -e "${BLUE}🔍 Verifying orchestration system status...${NC}"
    if is_orchestration_running; then
        echo -e "${GREEN}✅ Orchestration system already running (no restart needed)${NC}"
    else
        if start_orchestration_background; then
            if is_orchestration_running; then
                echo -e "${GREEN}✅ Orchestration system started${NC}"
            else
                echo -e "${YELLOW}⚠️  Orchestration optional - continuing without it${NC}"
            fi
        else
            echo -e "${YELLOW}ℹ️  Orchestration not available${NC}"
        fi
    fi
}

# Enhanced MCP server detection with better error handling
echo -e "${BLUE}🔍 Checking MCP servers...${NC}"

# Check if claude command is available
if ! command -v claude >/dev/null 2>&1; then
    echo -e "${RED}❌ Claude CLI not found. Please install Claude CLI first.${NC}"
    exit 1
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

# Claude Bot Server auto-start
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

# Check and start Claude bot server
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

echo ""

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
    esac
else
    # If no mode specified, show interactive menu
    echo -e "${BLUE}Select mode:${NC}"
    echo -e "${GREEN}1) Worker (Sonnet 4)${NC}"
    echo -e "${BLUE}2) Default${NC}"
    echo -e "${YELLOW}3) Supervisor (Opus 4)${NC}"
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
    start_claude_bot_background
    sleep 3
    if is_claude_bot_running; then
        echo -e "${GREEN}✅ Claude bot server restarted successfully${NC}"
    else
        echo -e "${RED}❌ Failed to restart Claude bot server${NC}"
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