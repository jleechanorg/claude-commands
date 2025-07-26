#!/bin/bash
#
# Startup script for GitHub Claude Bot Commands system.
# This script starts the local Claude bot server and provides helpful information.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=${CLAUDE_ENDPOINT_PORT:-5001}

echo "🚀 Starting GitHub Claude Bot Commands System"
echo "============================================================"

# Check if Claude Code CLI is available
# Note: When running inside Claude Code environment, the CLI may not be in PATH
# but we can check for other indicators
if command -v claude-code &> /dev/null; then
    echo "✅ Claude Code CLI found: $(which claude-code)"
elif [[ -n "$CLAUDE_CODE" ]] || [[ -n "$ANTHROPIC_CLI" ]] || [[ "$0" == *"claude"* ]]; then
    echo "✅ Claude Code environment detected"
else
    echo "⚠️  Claude Code CLI not found in PATH."
    echo "   This script is designed to work with Claude Code CLI."
    echo "   If you're running in Claude Code environment, you can continue."
    echo "   Otherwise, visit: https://docs.anthropic.com/en/docs/claude-code"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.6+."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if required files exist
if [[ ! -f "$SCRIPT_DIR/claude-bot-commands/server/claude-bot-server.py" ]]; then
    echo "❌ claude-bot-server.py not found"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/.github/workflows/slash-dispatch.yml" ]]; then
    echo "❌ GitHub workflow files not found. Make sure you're in the correct directory."
    exit 1
fi

echo "✅ All required files found"
echo ""

# Show configuration
echo "📋 Configuration:"
echo "   Local endpoint: http://127.0.0.1:$PORT"
echo "   Health check: http://127.0.0.1:$PORT/health"
echo "   Claude command: http://127.0.0.1:$PORT/claude"
echo ""

# Show setup reminders
echo "🔧 Setup Reminders:"
echo "   1. GitHub secrets configured: REPO_ACCESS_TOKEN, CLAUDE_ENDPOINT"
echo "   2. Self-hosted runner installed with 'claude' label"
echo "   3. Runner service is running and online"
echo ""

echo "▶️  Starting Claude bot server on port $PORT..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
cd "$SCRIPT_DIR"
python3 claude-bot-commands/server/claude-bot-server.py