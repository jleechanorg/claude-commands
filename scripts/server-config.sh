#!/bin/bash
# server-config.sh - Centralized server configuration for WorldArchitect.AI
# Single source of truth for all server ports and settings

# Default port configuration
export DEFAULT_FLASK_PORT=${DEFAULT_FLASK_PORT:-8081}
export DEFAULT_REACT_PORT=${DEFAULT_REACT_PORT:-3002}
export DEFAULT_CLAUDE_BOT_PORT=${DEFAULT_CLAUDE_BOT_PORT:-5001}

# Port ranges for different services
export FLASK_PORT_RANGE_START=${FLASK_PORT_RANGE_START:-8081}
export FLASK_PORT_RANGE_END=${FLASK_PORT_RANGE_END:-8090}

export REACT_PORT_RANGE_START=${REACT_PORT_RANGE_START:-3001}
export REACT_PORT_RANGE_END=${REACT_PORT_RANGE_END:-3010}

# Test server configuration
export TEST_BROWSER_PORT_BASE=${TEST_BROWSER_PORT_BASE:-8081}
export TEST_HTTP_PORT_BASE=${TEST_HTTP_PORT_BASE:-8086}
export TEST_INTEGRATION_PORT_BASE=${TEST_INTEGRATION_PORT_BASE:-8088}

# Common environment variables
export TESTING=${TESTING:-true}
export FLASK_ENV=${FLASK_ENV:-development}
export PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-1}

# Logging configuration
export LOG_DIR_BASE=${LOG_DIR_BASE:-"/tmp/worldarchitect.ai"}

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Emojis for consistent output
export EMOJI_ROCKET="🚀"
export EMOJI_CHECK="✅"
export EMOJI_ERROR="❌"
export EMOJI_WARNING="⚠️"
export EMOJI_INFO="ℹ️"
export EMOJI_PYTHON="🐍"
export EMOJI_GEAR="⚙️"
export EMOJI_TARGET="🎯"
export EMOJI_SEARCH="🔍"
export EMOJI_SWORD="⚔️"
export EMOJI_CLOCK="⏱️"

# Validation: Ensure configuration is loaded
if [ -z "$DEFAULT_FLASK_PORT" ]; then
    echo "${EMOJI_ERROR} ERROR: Server configuration failed to load properly"
    exit 1
fi

echo "${EMOJI_INFO} Server configuration loaded: Flask:$DEFAULT_FLASK_PORT, React:$DEFAULT_REACT_PORT"