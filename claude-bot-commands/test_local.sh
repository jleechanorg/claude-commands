#!/bin/bash
# Local testing script for Claude bot server
# Tests the actual EBADF fixes to ensure they work

set -e

echo "🧪 Testing Claude Bot Server Locally"
echo "====================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if Claude CLI is available
echo "🔍 Checking Claude CLI availability..."
CLAUDE_FOUND=false
CLAUDE_PATH=""

# Test possible Claude CLI locations
POSSIBLE_PATHS=(
    "$HOME/.claude/local/claude"
    "/usr/local/bin/claude"
    "/opt/homebrew/bin/claude"
    "claude"
)

for path in "${POSSIBLE_PATHS[@]}"; do
    if command -v "$path" &> /dev/null || [[ -x "$path" ]]; then
        if timeout 5 "$path" --version &> /dev/null; then
            CLAUDE_FOUND=true
            CLAUDE_PATH="$path"
            echo "✅ Found Claude CLI: $path"
            break
        fi
    fi
done

if [ "$CLAUDE_FOUND" = false ]; then
    echo "⚠️  Claude CLI not found. Server will return error messages."
    echo "   Install Claude CLI: https://docs.anthropic.com/en/docs/claude-code"
else
    echo "✅ Claude CLI ready: $CLAUDE_PATH"
fi

# Change to server directory
cd "$(dirname "$0")/server"

echo ""
echo "🚀 Starting Claude bot server..."
echo "   (Press Ctrl+C to stop)"

# Function to cleanup background process
cleanup() {
    if [[ -n $SERVER_PID ]]; then
        echo ""
        echo "🛑 Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Start server in background
python3 claude-bot-server.py &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Server failed to start"
    exit 1
fi

echo "✅ Server started (PID: $SERVER_PID)"
echo ""

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -s "http://127.0.0.1:5001/health" | grep -q "Claude endpoint server is running"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

echo ""
echo "🧪 Testing Claude endpoint..."

# Test cases
declare -a test_cases=(
    "hello"
    "what is 2+2?"
    "help me with Python"
)

for prompt in "${test_cases[@]}"; do
    echo ""
    echo "📝 Testing prompt: '$prompt'"
    echo "---"

    # Make request and capture response
    response=$(curl -s -X POST -d "prompt=$prompt" "http://127.0.0.1:5001/claude")

    # Check for EBADF errors
    if echo "$response" | grep -q "EBADF"; then
        echo "❌ EBADF ERROR DETECTED: $response"
        echo "   This indicates the fix didn't work properly"
    elif echo "$response" | grep -q "❌ Claude CLI error"; then
        echo "⚠️  CLI Error: $response"
        echo "   This is expected if Claude CLI has issues, but no EBADF"
    elif echo "$response" | grep -q "❌ Claude CLI not found"; then
        echo "⚠️  CLI Not Found: $response"
        echo "   This is expected if Claude CLI isn't installed"
    elif echo "$response" | grep -q "❌ Claude CLI timed out"; then
        echo "⏰ Timeout: Claude CLI took too long (>30s)"
        echo "   This is acceptable - no EBADF errors"
    elif [[ ${#response} -gt 10 ]]; then
        echo "✅ SUCCESS: Got response (${#response} chars)"
        echo "   First 100 chars: ${response:0:100}..."
        echo "   🎉 EBADF fix working - Claude CLI responded!"
    else
        echo "❓ Unexpected response: $response"
    fi
done

echo ""
echo "📊 Test Summary:"
echo "- No EBADF errors = ✅ Fix working"
echo "- CLI errors/timeouts = ⚠️  Expected, but no EBADF"
echo "- Actual responses = 🎉 Full success"
echo ""
echo "🏁 Testing complete. Check results above."
echo "   Server is still running - press Ctrl+C to stop"

# Keep server running for manual testing
wait $SERVER_PID
