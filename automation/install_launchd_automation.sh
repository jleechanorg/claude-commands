#!/bin/bash
set -euo pipefail

# Install launchd automation for macOS PR processing
# This script sets up the safety-wrapped automation system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLIST_SOURCE="$SCRIPT_DIR/com.worldarchitect.pr-automation.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.worldarchitect.pr-automation.plist"
LOG_DIR="$HOME/Library/Logs/worldarchitect-automation"

echo "🚀 Installing WorldArchitect PR Automation for macOS"
echo "   Project: $PROJECT_ROOT"
echo "   Safety: Max 5 attempts per PR, 50 total runs before approval"

# Create log directory
mkdir -p "$LOG_DIR"
echo "📁 Created log directory: $LOG_DIR"

# Update plist with correct paths
echo "🔧 Updating plist paths..."
sed "s|/Users/$USER/projects/worktree_worker2|$PROJECT_ROOT|g" "$PLIST_SOURCE" > "$PLIST_DEST"

# Update username in plist
CURRENT_USER=$(whoami)
sed -i '' "s|$USER|$CURRENT_USER|g" "$PLIST_DEST"

echo "📄 Installed plist: $PLIST_DEST"

# Make scripts executable
chmod +x "$SCRIPT_DIR/jleechanorg_pr_automation/automation_safety_wrapper.py"
chmod +x "$SCRIPT_DIR/jleechanorg_pr_automation/automation_safety_manager.py"
chmod +x "$SCRIPT_DIR/simple_pr_batch.sh"
echo "🔐 Made scripts executable"

# Unload existing job if running
if launchctl list | grep -q "com.worldarchitect.pr-automation"; then
    echo "🔄 Unloading existing automation job..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Load the new job
echo "⚡ Loading automation job..."
launchctl load "$PLIST_DEST"

# Verify it's loaded
if launchctl list | grep -q "com.worldarchitect.pr-automation"; then
    echo "✅ Automation job loaded successfully!"
else
    echo "❌ Failed to load automation job"
    exit 1
fi

echo ""
echo "🎯 Installation Complete!"
echo ""
echo "📊 Configuration:"
echo "   • Schedule: Every 10 minutes"
echo "   • PR Limit: 5 attempts per PR"
echo "   • Global Limit: 50 total runs"
echo "   • Safety Wrapper: automation_safety_wrapper.py"
echo "   • Logs: $LOG_DIR"
echo ""
echo "🔧 Management Commands:"
echo "   • Status: launchctl list | grep worldarchitect"
echo "   • Stop: launchctl unload '$PLIST_DEST'"
echo "   • Start: launchctl load '$PLIST_DEST'"
echo "   • Logs: tail -f '$LOG_DIR/automation_safety.log'"
echo ""
echo "🚨 Safety Features:"
echo "   • Automatic email notifications at limits"
echo "   • Manual approval required after 50 runs"
echo "   • Thread-safe PR attempt tracking"
echo "   • 1-hour timeout per automation cycle"
echo ""
echo "💡 Grant manual approval when needed:"
echo "   python3 '$SCRIPT_DIR/automation_safety_manager.py' --approve user@example.com"
echo ""
echo "📈 Check status:"
echo "   python3 '$SCRIPT_DIR/automation_safety_manager.py' --status"
