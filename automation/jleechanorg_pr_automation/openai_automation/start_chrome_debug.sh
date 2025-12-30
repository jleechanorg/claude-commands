#!/usr/bin/env bash
#
# Start Chrome with Remote Debugging for Automation
#
# This script starts Chrome/Chromium with remote debugging enabled,
# allowing Playwright to connect without being detected as automation.
#
# Usage:
#   ./start_chrome_debug.sh [PORT]
#
# Default port: 9222

set -e

PORT="${1:-9222}"
USER_DATA_DIR="${HOME}/.chrome-automation-profile"

echo "🚀 Starting Chrome with Remote Debugging"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Port: $PORT"
echo "  User Data: $USER_DATA_DIR"
echo ""

# Detect Chrome/Chromium location
detect_chrome() {
    if [ "$(uname)" = "Darwin" ]; then
        # macOS
        if [ -d "/Applications/Google Chrome.app" ]; then
            echo "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif [ -d "/Applications/Chromium.app" ]; then
            echo "/Applications/Chromium.app/Contents/MacOS/Chromium"
        elif command -v google-chrome &> /dev/null; then
            echo "google-chrome"
        elif command -v chromium &> /dev/null; then
            echo "chromium"
        fi
    else
        # Linux
        if command -v google-chrome &> /dev/null; then
            echo "google-chrome"
        elif command -v chromium-browser &> /dev/null; then
            echo "chromium-browser"
        elif command -v chromium &> /dev/null; then
            echo "chromium"
        fi
    fi
}

CHROME_PATH=$(detect_chrome)

if [ -z "$CHROME_PATH" ]; then
    echo "❌ Could not find Chrome or Chromium"
    echo ""
    echo "Please install Chrome:"
    echo "  macOS: brew install --cask google-chrome"
    echo "  Linux: sudo apt install google-chrome-stable"
    exit 1
fi

echo "✅ Found Chrome: $CHROME_PATH"
echo ""

# Check if Chrome is already running on this port
if lsof -i ":$PORT" > /dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use"
    echo ""
    echo "Chrome may already be running in debug mode."
    echo "If you want to restart, kill the existing process and try again:"
    echo ""
    echo "  pkill -f 'remote-debugging-port=$PORT'"
    echo ""
    exit 0
fi

# Create user data directory if it doesn't exist
mkdir -p "$USER_DATA_DIR"

# Chrome flags for automation (non-detectable)
CHROME_FLAGS=(
    # Remote debugging
    "--remote-debugging-port=$PORT"

    # Use separate profile - REQUIRED for remote debugging to work
    "--user-data-dir=$USER_DATA_DIR"

    # Note: --disable-blink-features=AutomationControlled is unsupported and causes warnings
    # Removed - just use remote debugging without special flags

    # Keep extensions enabled (more like normal browsing)
    # "--disable-extensions" # Commented out to appear more normal

    # Start with specific URL
    "https://chatgpt.com/"

    # Window size
    "--window-size=1920,1080"
)

echo "🌐 Starting Chrome..."
echo ""
echo "  Flags:"
for flag in "${CHROME_FLAGS[@]}"; do
    echo "    $flag"
done
echo ""

# Start Chrome in background
"$CHROME_PATH" "${CHROME_FLAGS[@]}" &

CHROME_PID=$!

echo "✅ Chrome started (PID: $CHROME_PID)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 CDP Endpoint: http://localhost:$PORT"
echo ""
echo "📝 Next steps:"
echo "  1. Log in to OpenAI in the Chrome window that just opened"
echo "  2. Run the automation script:"
echo "     python3 automation/jleechanorg_pr_automation/openai_automation/codex_github_mentions.py"
echo ""
echo "💡 To stop Chrome:"
echo "     kill $CHROME_PID"
echo "     or: pkill -f 'remote-debugging-port=$PORT'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait a moment for Chrome to start
sleep 2

# Check if Chrome is actually listening
if lsof -i ":$PORT" > /dev/null 2>&1; then
    echo "✅ Chrome is listening on port $PORT"
else
    echo "⚠️  Chrome may not have started correctly"
    echo "   Check if port $PORT is accessible"
fi
