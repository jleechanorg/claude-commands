#!/usr/bin/env bash
# Example 3: Interactive Debug Session
#
# Demonstrates: Persistent debugging with Superpowers Chrome
# Duration: Session stays open until you close it
# Use case: Bug investigation, manual testing, exploration

set -e

URL="${1:-http://localhost:5000}"

echo "🔍 Interactive Debug Session with Superpowers Chrome"
echo "====================================================="
echo "URL: $URL"
echo ""

# Start Chrome if not running
if ! chrome-ws tabs &> /dev/null; then
  echo "🚀 Starting Chrome with remote debugging..."
  chrome-ws start
  sleep 2
fi

# Open the URL
echo "🌐 Opening $URL in new tab..."
chrome-ws new "$URL"
TAB=0

echo ""
echo "✅ Debug session ready!"
echo ""
echo "💡 Why Superpowers Chrome?"
echo "   - Persistent session (stays open)"
echo "   - CLI for interactive exploration"
echo "   - Direct CDP access"
echo "   - No test infrastructure needed"
echo ""
echo "📋 Useful Commands:"
echo ""
echo "  # Extract data"
echo "  chrome-ws extract $TAB \".campaign-name\""
echo "  chrome-ws eval $TAB \"document.title\""
echo ""
echo "  # Interact"
echo "  chrome-ws click $TAB \"button.submit\""
echo "  chrome-ws fill $TAB \"#input\" \"text\""
echo ""
echo "  # Capture"
echo "  chrome-ws screenshot $TAB > debug.png"
echo "  chrome-ws markdown $TAB > debug.md"
echo ""
echo "  # Navigate"
echo "  chrome-ws navigate $TAB \"/campaigns\""
echo "  chrome-ws wait-for $TAB \"selector\""
echo ""
echo "  # Inspect"
echo "  chrome-ws html $TAB \"main\""
echo "  chrome-ws attr $TAB \"a.link\" \"href\""
echo ""
echo "🔗 Chrome DevTools: http://localhost:9222"
echo ""
echo "⏸️  Session will stay open - use ctrl+c to exit"
echo "   Or run: chrome-ws close $TAB"
echo ""

# Keep script running
read -p "Press Enter to close debug session..."
chrome-ws close $TAB
