#!/bin/bash
# WorldArchitect MCP Server Startup Script
# Starts the MCP server with configurable transport options

set -e

# Default configuration
PORT=8081
MODE="dual"  # dual, http-only, stdio-only

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --port PORT        Set HTTP port (default: 8081)"
    echo "  --http-only        HTTP transport only"
    echo "  --stdio-only       Stdio transport only"
    echo "  --dual             Both HTTP and stdio (default)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --port 8082 --http-only"
    echo "  $0 --stdio-only"
    echo "  $0 --dual --port 8003"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --http-only)
            MODE="http-only"
            shift
            ;;
        --stdio-only)
            MODE="stdio-only"
            shift
            ;;
        --dual)
            MODE="dual"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

# Get script directory and resolve project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROJECT_MODULE_DIR_DEFAULT="orchestration"
if [[ -n "${WORLDARCHITECT_MODULE_DIR:-}" ]]; then
    PROJECT_MODULE_DIR="$WORLDARCHITECT_MODULE_DIR"
elif [[ -n "${PROJECT_MODULE_DIR:-}" ]]; then
    PROJECT_MODULE_DIR="$PROJECT_MODULE_DIR"
elif [[ -n "${PROJECT_ROOT:-}" && "${PROJECT_ROOT}" != /* ]]; then
    PROJECT_MODULE_DIR="$PROJECT_ROOT"
else
    PROJECT_MODULE_DIR="$PROJECT_MODULE_DIR_DEFAULT"
fi

resolve_project_root() {
    if [[ -n "${WORLDARCHITECT_PROJECT_ROOT:-}" ]]; then
        local candidate="${WORLDARCHITECT_PROJECT_ROOT}"
        if [[ -f "$candidate/$PROJECT_MODULE_DIR/mcp_api.py" || -f "$candidate/src/mcp_api.py" || -f "$candidate/mcp_api.py" ]]; then
            echo "$candidate"
            return 0
        fi
    fi

    local search_dir="$SCRIPT_DIR"
    while [[ "$search_dir" != "/" ]]; do
        if [[ -f "$search_dir/$PROJECT_MODULE_DIR/mcp_api.py" || -f "$search_dir/src/mcp_api.py" || -f "$search_dir/mcp_api.py" ]]; then
            echo "$search_dir"
            return 0
        fi
        search_dir="$(dirname "$search_dir")"
    done

    return 1
}

if PROJECT_ROOT="$(resolve_project_root)"; then
    :
else
    echo -e "${RED}❌ Error: Unable to locate project root. Set WORLDARCHITECT_PROJECT_ROOT to override.${NC}" >&2
    exit 1
fi

if [[ -z "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$PROJECT_ROOT"
else
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
fi

MCP_SERVER_ENV_DEFAULT="${MCP_SERVER_PATH:-}"

# Try multiple common MCP server locations
if [ -f "$PROJECT_ROOT/$PROJECT_MODULE_DIR/mcp_api.py" ]; then
    MCP_SERVER_PATH="$PROJECT_ROOT/$PROJECT_MODULE_DIR/mcp_api.py"
elif [ -f "$PROJECT_ROOT/src/mcp_api.py" ]; then
    MCP_SERVER_PATH="$PROJECT_ROOT/src/mcp_api.py"
elif [ -f "$PROJECT_ROOT/mcp_api.py" ]; then
    MCP_SERVER_PATH="$PROJECT_ROOT/mcp_api.py"
elif [ -n "$MCP_SERVER_ENV_DEFAULT" ]; then
    MCP_SERVER_PATH="$MCP_SERVER_ENV_DEFAULT"
else
    MCP_SERVER_PATH="$PROJECT_ROOT/src/mcp_api.py"
fi

# Validate MCP server exists
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo -e "${RED}❌ Error: MCP server not found at $MCP_SERVER_PATH${NC}" >&2
    exit 1
fi

# Get Python executable
if [[ -z "${PYTHON_EXEC:-}" ]]; then
    if [[ -x "$PROJECT_ROOT/venv/bin/python" ]]; then
        PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
    else
        PYTHON_EXEC="python3"
    fi
fi

if ! command -v "$PYTHON_EXEC" &> /dev/null && [[ ! -x "$PYTHON_EXEC" ]]; then
    echo -e "${RED}❌ Error: Python executable '$PYTHON_EXEC' not found${NC}" >&2
    exit 1
fi

echo -e "${BLUE}🏰 Starting WorldArchitect MCP Server${NC}"
echo -e "${BLUE}   Mode: $MODE${NC}"
echo -e "${BLUE}   Port: $PORT${NC}"
echo -e "${BLUE}   Server: $MCP_SERVER_PATH${NC}"

# Build command arguments
CMD_ARGS=()

case $MODE in
    "http-only")
        CMD_ARGS+=("--http" "--port" "$PORT")
        ;;
    "stdio-only")
        CMD_ARGS+=("--stdio")
        ;;
    "dual")
        CMD_ARGS+=("--http" "--port" "$PORT" "--stdio")
        ;;
    *)
        echo -e "${RED}❌ Error: Invalid mode '$MODE'${NC}" >&2
        exit 1
        ;;
esac

# Start the server
echo -e "${BLUE}🚀 Executing: $PYTHON_EXEC $MCP_SERVER_PATH ${CMD_ARGS[*]}${NC}"

# Use exec to replace the shell process with the Python process
exec "$PYTHON_EXEC" "$MCP_SERVER_PATH" "${CMD_ARGS[@]}"
