#!/bin/bash
# WorldArchitect MCP Server Startup Script
# Starts the MCP server with configurable transport options

set -e

# Default configuration
PORT=8081
MODE="dual"  # dual, http-only, stdio-only
TIMEOUT=30

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
    echo "  --timeout SECONDS  Startup timeout (default: 30)"
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
        --timeout)
            TIMEOUT="$2"
            shift 2
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

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MCP_SERVER_PATH="$PROJECT_ROOT/mvp_site/mcp_api.py"

# Validate MCP server exists
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo -e "${RED}❌ Error: MCP server not found at $MCP_SERVER_PATH${NC}" >&2
    exit 1
fi

# Get Python executable
PYTHON_EXEC="${PYTHON_EXEC:-python3}"
if ! command -v "$PYTHON_EXEC" &> /dev/null; then
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
