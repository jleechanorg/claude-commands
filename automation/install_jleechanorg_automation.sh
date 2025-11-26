#!/bin/bash
set -euo pipefail

# Install jleechanorg PR automation for macOS
# This script sets up comprehensive cross-organization PR monitoring

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLIST_SOURCE="$SCRIPT_DIR/com.jleechanorg.pr-automation.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.jleechanorg.pr-automation.plist"
LOG_DIR="$HOME/Library/Logs/worldarchitect-automation"

echo "🚀 Installing jleechanorg PR Automation for macOS"
echo "   🏢 Organization: jleechanorg (all repositories)"
echo "   ⏰ Schedule: Every 10 minutes"
echo "   🛡️ Safety: Max 5 attempts per PR, 50 total runs"
echo "   🔄 Isolation: Individual worktrees per PR"

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found. Install with: brew install gh"
    exit 1
fi

# Check GitHub authentication
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI not authenticated. Run: gh auth login"
    exit 1
fi

# Check organization access
if ! gh repo list jleechanorg --limit 1 &> /dev/null; then
    echo "❌ Cannot access jleechanorg organization. Check permissions."
    exit 1
fi

echo "✅ GitHub CLI authenticated and organization accessible"

# Check Python and required modules
if ! python3 -c "import json, subprocess, pathlib" &> /dev/null; then
    echo "❌ Python3 missing required modules"
    exit 1
fi

echo "✅ Python3 environment ready"

# Create workspace directories
WORKSPACE_BASE="$HOME/tmp/jleechanorg-pr-workspaces"
mkdir -p "$WORKSPACE_BASE"
mkdir -p "$LOG_DIR"

echo "📁 Created directories:"
echo "   Workspaces: $WORKSPACE_BASE"
echo "   Logs: $LOG_DIR"

# Update plist with correct paths and user
echo "🔧 Configuring launchd service..."
CURRENT_USER=$(whoami)
sed "s|/Users/$USER/projects/worktree_worker2|$PROJECT_ROOT|g" "$PLIST_SOURCE" | \
sed "s|$USER|$CURRENT_USER|g" | \
sed "s|\\$GITHUB_TOKEN|$GITHUB_TOKEN|g" > "$PLIST_DEST"

echo "📄 Created plist: $PLIST_DEST"

# Make scripts executable
chmod +x "$SCRIPT_DIR/jleechanorg_pr_automation/jleechanorg_pr_monitor.py"
chmod +x "$SCRIPT_DIR/jleechanorg_pr_automation/automation_safety_manager.py"
echo "🔐 Made scripts executable"

# Unload existing job if running
echo "🔄 Managing launchd service..."
if launchctl list | grep -q "com.jleechanorg.pr-automation"; then
    echo "   Unloading existing service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Also unload old worldarchitect service if it exists
OLD_PLIST="$HOME/Library/LaunchAgents/com.worldarchitect.pr-automation.plist"
if [[ -f "$OLD_PLIST" ]] && launchctl list | grep -q "com.worldarchitect.pr-automation"; then
    echo "   Unloading old worldarchitect service..."
    launchctl unload "$OLD_PLIST" 2>/dev/null || true
fi

# Load the new job
echo "   Loading jleechanorg automation service..."
launchctl load "$PLIST_DEST"

# Verify it's loaded
sleep 2
if launchctl list | grep -q "com.jleechanorg.pr-automation"; then
    echo "✅ Automation service loaded successfully!"
else
    echo "❌ Failed to load automation service"
    echo "Check logs: cat $LOG_DIR/jleechanorg-launchd.err"
    exit 1
fi

# Test discovery functionality
echo ""
echo "🧪 Testing PR discovery..."
if python3 "$SCRIPT_DIR/jleechanorg_pr_automation/jleechanorg_pr_monitor.py" --dry-run --max-prs 5; then
    echo "✅ PR discovery test successful"
else
    echo "⚠️ PR discovery test failed - check configuration"
fi

echo ""
echo "🎯 Installation Complete!"
echo ""
echo "📊 Service Configuration:"
echo "   • Organization: jleechanorg (all repositories)"
echo "   • Schedule: Every 10 minutes"
echo "   • Workspace: $WORKSPACE_BASE"
echo "   • Logs: $LOG_DIR"
echo ""
echo "🛡️ Safety Features:"
echo "   • PR Limits: 5 attempts per PR before blocking"
echo "   • Global Limits: 50 total runs before manual approval"
echo "   • Worktree Isolation: Each PR processed in separate workspace"
echo "   • Email Notifications: Automatic alerts at limits"
echo ""
echo "🔧 Management Commands:"
echo "   • Status: launchctl list | grep jleechanorg"
echo "   • Stop: launchctl unload '$PLIST_DEST'"
echo "   • Start: launchctl load '$PLIST_DEST'"
echo "   • Logs: tail -f '$LOG_DIR/jleechanorg_pr_monitor.log'"
echo ""
echo "🧪 Manual Testing:"
echo "   • Dry run: python3 '$SCRIPT_DIR/jleechanorg_pr_automation/jleechanorg_pr_monitor.py' --dry-run"
echo "   • Single repo: python3 '$SCRIPT_DIR/jleechanorg_pr_automation/jleechanorg_pr_monitor.py' --dry-run --single-repo repo-name"
echo "   • Safety status: python3 '$SCRIPT_DIR/jleechanorg_pr_automation/automation_safety_manager.py' --status"
echo ""
echo "💡 Grant manual approval when needed:"
echo "   python3 '$SCRIPT_DIR/jleechanorg_pr_automation/automation_safety_manager.py' --approve user@example.com"
echo ""
echo "🔍 Monitor real-time activity:"
echo "   tail -f '$LOG_DIR/jleechanorg_pr_monitor.log'"
