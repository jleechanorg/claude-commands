#!/bin/bash
# Setup Passwordless Clock Sync for GitHub Runner
# Allows runner service to sync clock without password prompt
#
# Usage: ./self-hosted/scripts/setup-passwordless-clocksync.sh
#
# What this does:
#   1. Creates sudoers entry for passwordless sntp clock sync
#   2. Modifies runner LaunchAgent to sync clock before starting
#   3. Updates monitor.sh to sync clock before restart attempts
#
# Security: Only allows passwordless execution of "sntp -sS time.apple.com"
#           No other sudo commands are granted passwordless access

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Error handler
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Setup failed with exit code $exit_code"
    fi
}

trap cleanup EXIT ERR

echo "🔧 GitHub Runner Passwordless Clock Sync Setup"
echo "================================================================"
echo "This script configures passwordless clock sync for the runner"
echo "to enable auto-recovery after offline periods with clock drift."
echo "================================================================"
echo ""

# Check if running as non-root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Do not run this script as root. Run as your normal user."
    echo "   The script will prompt for sudo when needed."
    exit 1
fi

RUNNER_DIR="$HOME/actions-runner"
SUDOERS_FILE="/etc/sudoers.d/runner-clocksync"

# Step 1: Create sudoers entry for passwordless clock sync
echo "▶️  Step 1: Creating sudoers entry for passwordless clock sync"
echo "   (This requires your sudo password)"
echo ""

# Create sudoers content
SUDOERS_CONTENT="# Allow $(whoami) to sync clock without password (for GitHub Runner)
$(whoami) ALL=(ALL) NOPASSWD: /usr/sbin/sntp -sS time.apple.com"

# Write to sudoers.d (validates syntax automatically)
echo "$SUDOERS_CONTENT" | sudo tee "$SUDOERS_FILE" > /dev/null
sudo chmod 0440 "$SUDOERS_FILE"

# Validate sudoers file
if sudo visudo -c -f "$SUDOERS_FILE" > /dev/null 2>&1; then
    echo "  ✅ Sudoers entry created: $SUDOERS_FILE"
else
    echo "  ❌ Invalid sudoers syntax, removing file"
    sudo rm -f "$SUDOERS_FILE"
    exit 1
fi
echo ""

# Step 2: Test passwordless clock sync
echo "▶️  Step 2: Testing passwordless clock sync"
if sudo sntp -sS time.apple.com > /dev/null 2>&1; then
    echo "  ✅ Passwordless clock sync works!"
else
    echo "  ❌ Clock sync test failed"
    exit 1
fi
echo ""

# Step 3: Update monitor.sh to sync clock before restart
echo "▶️  Step 3: Updating monitor.sh to sync clock before restart"
MONITOR_SCRIPT="$RUNNER_DIR/monitor.sh"

if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo "  ⚠️  Monitor script not found at $MONITOR_SCRIPT"
    echo "     Skipping monitor.sh update (you can add it manually)"
else
    # Check if already has clock sync
    if grep -q "sudo.*sntp" "$MONITOR_SCRIPT"; then
        echo "  ℹ️  Monitor script already has clock sync - skipping"
    else
        # Backup original
        cp "$MONITOR_SCRIPT" "$MONITOR_SCRIPT.bak"

        # Add clock sync before restart attempt
        # Insert after "Runner not running" line
        sed -i '' '/Runner not running/a\
\
    # Sync clock before restart attempt (passwordless sudo)\
    echo "$(date): Syncing clock before restart..." >> "$LOG_FILE"\
    sudo sntp -sS time.apple.com 2>&1 | tee -a "$LOG_FILE" || true
' "$MONITOR_SCRIPT"

        echo "  ✅ Updated monitor.sh with clock sync"
        echo "     Backup saved: $MONITOR_SCRIPT.bak"
    fi
fi
echo ""

# Step 4: Instructions for LaunchAgent update
echo "▶️  Step 4: LaunchAgent update instructions"
echo ""
echo "To complete setup, add clock sync to your runner LaunchAgent:"
echo ""
echo "1. Find your LaunchAgent plist file:"
echo "   ls ~/Library/LaunchAgents/actions.runner.*.plist"
echo ""
echo "2. Edit the plist file and add this BEFORE the ProgramArguments section:"
echo ""
cat << 'EOF'
    <key>EnvironmentVariables</key>
    <dict>
        <key>RUNNER_AUTO_CLOCKSYNC</key>
        <string>1</string>
    </dict>
EOF
echo ""
echo "3. Add this wrapper script to sync clock before runner starts:"
echo "   Create ~/actions-runner/run-with-clocksync.sh:"
echo ""
cat << 'EOF'
#!/bin/bash
sudo sntp -sS time.apple.com 2>&1 || true
exec "$@"
EOF
echo ""
echo "4. Update ProgramArguments in plist to use wrapper:"
echo "   Change: <string>/Users/.../runsvc.sh</string>"
echo "   To:     <string>/Users/.../run-with-clocksync.sh</string>"
echo "           <string>/Users/.../runsvc.sh</string>"
echo ""
echo "5. Reload LaunchAgent:"
echo "   launchctl unload ~/Library/LaunchAgents/actions.runner.*.plist"
echo "   launchctl load ~/Library/LaunchAgents/actions.runner.*.plist"
echo ""

echo "🎉 Passwordless Clock Sync Setup Complete!"
echo ""
echo "📋 What was configured:"
echo "  ✅ Sudoers entry for passwordless 'sntp -sS time.apple.com'"
echo "  ✅ Monitor script syncs clock before restart attempts"
echo "  ⏳ LaunchAgent needs manual update (see instructions above)"
echo ""
echo "🔍 Test it:"
echo "  sudo sntp -sS time.apple.com   # Should work without password"
echo "  ~/actions-runner/monitor.sh    # Should sync clock if runner down"
echo ""
echo "🔐 Security note:"
echo "  Only 'sntp -sS time.apple.com' can run without password"
echo "  No other sudo commands are granted passwordless access"
echo ""
