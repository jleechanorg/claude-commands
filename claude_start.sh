#!/bin/bash
# Enhanced Claude Code startup script with reliable MCP server detection
# Always uses --dangerously-skip-permissions and prompts for model choice
# Model updated: July 12th, 2025

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
FORCE_CLEAN=false
REMAINING_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            FORCE_CLEAN=true
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

# Memory backup system checks
echo -e "${BLUE}🧠 Checking Memory MCP backup system...${NC}"

# Check if memory backup script exists and is current
MEMORY_BACKUP_SCRIPT="$HOME/backup_memory.sh"
REPO_BACKUP_SCRIPT="./memory/backup_memory.sh"
MEMORY_SETUP_SCRIPT="./memory/setup.sh"

BACKUP_ISSUES=()

# Check if backup script exists
if [ ! -f "$MEMORY_BACKUP_SCRIPT" ]; then
    BACKUP_ISSUES+=("❌ Backup script not found at $MEMORY_BACKUP_SCRIPT")
elif [ ! -x "$MEMORY_BACKUP_SCRIPT" ]; then
    BACKUP_ISSUES+=("❌ Backup script not executable")
fi

# Check if backup script is current (version check)
if [ -f "$MEMORY_BACKUP_SCRIPT" ] && [ -f "$REPO_BACKUP_SCRIPT" ]; then
    DEPLOYED_VERSION=$(grep "# VERSION:" "$MEMORY_BACKUP_SCRIPT" 2>/dev/null | cut -d' ' -f3 || echo "unknown")
    REPO_VERSION=$(grep "# VERSION:" "$REPO_BACKUP_SCRIPT" 2>/dev/null | cut -d' ' -f3 || echo "unknown")
    
    if [ "$DEPLOYED_VERSION" != "$REPO_VERSION" ]; then
        BACKUP_ISSUES+=("⚠️ Backup script version mismatch (deployed: $DEPLOYED_VERSION, repo: $REPO_VERSION)")
    fi
fi

# Check if cron job exists
if ! crontab -l 2>/dev/null | grep -q "backup_memory.sh"; then
    BACKUP_ISSUES+=("❌ Cron job not configured for memory backups")
fi

# Check if memory directory exists
if [ ! -d "$HOME/.cache/mcp-memory" ]; then
    BACKUP_ISSUES+=("❌ Memory cache directory not found")
fi

# Check if backup worktree exists
if [ ! -d "$HOME/worldarchitect-backup" ]; then
    BACKUP_ISSUES+=("❌ Backup worktree not found")
fi

# Report status and offer to fix
if [ ${#BACKUP_ISSUES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ Memory backup system is properly configured${NC}"
else
    echo -e "${YELLOW}⚠️ Memory backup system issues detected:${NC}"
    for issue in "${BACKUP_ISSUES[@]}"; do
        echo -e "${YELLOW}  $issue${NC}"
    done
    
    if [ -f "$MEMORY_SETUP_SCRIPT" ]; then
        echo -e "${BLUE}💡 Would you like to run the setup script to fix these issues? (y/N)${NC}"
        read -t 10 -p "Choice: " setup_choice
        
        case ${setup_choice:-n} in
            y|Y|yes|YES)
                echo -e "${BLUE}🔧 Running memory setup script...${NC}"
                if bash "$MEMORY_SETUP_SCRIPT"; then
                    echo -e "${GREEN}✅ Memory backup system setup completed${NC}"
                else
                    echo -e "${RED}❌ Setup failed. Please check the logs and try again.${NC}"
                fi
                ;;
            *)
                echo -e "${YELLOW}📝 Continuing without setup. You can run ./memory/setup.sh manually later.${NC}"
                ;;
        esac
    else
        echo -e "${YELLOW}📝 Setup script not found. Please check the memory/ directory.${NC}"
    fi
fi

echo ""

# Enhanced model date checking
LAST_UPDATE="2025-07-12"  # Updated date
CURRENT_DATE=$(date +%Y-%m-%d)

# Check if date commands work (some systems might have different date formats)
if command -v date >/dev/null 2>&1; then
    if LAST_UPDATE_EPOCH=$(date -d "$LAST_UPDATE" +%s 2>/dev/null) && CURRENT_EPOCH=$(date -d "$CURRENT_DATE" +%s 2>/dev/null); then
        DAYS_DIFF=$(( (CURRENT_EPOCH - LAST_UPDATE_EPOCH) / 86400 ))
        
        if [ $DAYS_DIFF -gt 30 ]; then
            echo -e "${YELLOW}⚠️ WARNING: Model was last updated on $LAST_UPDATE (${DAYS_DIFF} days ago)${NC}"
            echo -e "${YELLOW}   Consider checking if claude-sonnet-4-20250514 is still the latest model${NC}"
            echo ""
        fi
    else
        echo -e "${YELLOW}⚠️ Unable to check model update date${NC}"
    fi
fi

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
echo -e "${BLUE}Select mode:${NC}"
echo -e "${GREEN}1) Worker (Sonnet 4)${NC}"
echo -e "${BLUE}2) Default${NC}"
read -p "Choice [2]: " choice

case ${choice:-2} in
    1) 
        MODEL="claude-sonnet-4-20250514"
        echo -e "${GREEN}🚀 Starting Claude Code in worker mode with $MODEL...${NC}"
        claude --model "$MODEL" $FLAGS "$@"
        ;;
    2) 
        echo -e "${BLUE}🚀 Starting Claude Code with default settings...${NC}"
        claude $FLAGS "$@"
        ;;
    *) 
        echo -e "${YELLOW}Invalid choice, using default${NC}"
        claude $FLAGS "$@"
        ;;
esac