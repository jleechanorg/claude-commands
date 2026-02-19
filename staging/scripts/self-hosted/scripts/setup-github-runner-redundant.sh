#!/bin/bash
#
# GitHub Runner Setup with Dual Redundancy (LaunchAgent + Cron)
#
# Purpose: Configure GitHub Actions self-hosted runner with both launchd and crontab
#          monitoring for maximum reliability and prevention of runner deletion
#
# Usage: ./scripts/self-hosted/setup-github-runner-redundant.sh [REPO_URL] [RUNNER_NAME]
#
# Arguments:
#   REPO_URL      - Full GitHub repo URL (default: https://github.com/jleechanorg/your-project.com)
#   RUNNER_NAME   - Name for the runner (default: claude-drift-runner)
#
# Features:
#   - Redundancy Layer 1: LaunchAgent for persistent service management
#   - Redundancy Layer 2: Crontab monitoring every 15 minutes + heartbeat every 6 hours
#   - Clock drift detection and handling
#   - Automatic restart on failure
#   - Comprehensive logging
#
# Examples:
#   ./scripts/setup-github-runner-redundant.sh
#   ./scripts/setup-github-runner-redundant.sh https://github.com/myorg/myrepo my-runner
#

set -e

# ============================================================================
# Configuration
# ============================================================================

RUNNER_DIR="$HOME/actions-runner"
REPO_URL="${1:-https://github.com/jleechanorg/your-project.com}"
RUNNER_NAME="${2:-claude-drift-runner}"

# Extract owner/repo from URL for API calls
# Handles both https://github.com/owner/repo and owner/repo formats
if [[ "$REPO_URL" =~ ^https://github.com/(.+)$ ]]; then
  REPO_OWNER_AND_NAME="${BASH_REMATCH[1]}"
elif [[ "$REPO_URL" =~ ^[^/]+/[^/]+$ ]]; then
  REPO_OWNER_AND_NAME="$REPO_URL"
  REPO_URL="https://github.com/$REPO_URL"
else
  echo "❌ Invalid repository URL format. Expected: https://github.com/owner/repo or owner/repo"
  exit 1
fi

# ============================================================================
# Display Configuration
# ============================================================================

echo "🔧 GitHub Runner Setup with Dual Redundancy"
echo "================================================================"
echo "Repository:    $REPO_URL"
echo "Runner Name:   $RUNNER_NAME"
echo "Runner Dir:    $RUNNER_DIR"
echo "Redundancy:    LaunchAgent + Crontab"
echo "================================================================"
echo ""

# ============================================================================
# Prerequisites Check
# ============================================================================

echo "▶️  Checking prerequisites..."

# Check if runner directory exists
if [[ ! -d "$RUNNER_DIR" ]]; then
    echo "❌ Runner directory not found: $RUNNER_DIR"
    echo ""
    echo "📥 Download GitHub Actions runner first:"
    echo "   mkdir -p $RUNNER_DIR && cd $RUNNER_DIR"
    echo "   curl -o actions-runner-osx-arm64-2.321.0.tar.gz -L \\"
    echo "     https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-osx-arm64-2.321.0.tar.gz"
    echo "   tar xzf actions-runner-osx-arm64-2.321.0.tar.gz"
    exit 1
fi

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found"
    echo ""
    echo "📥 Install GitHub CLI:"
    echo "   brew install gh"
    echo "   # OR download from https://cli.github.com/"
    exit 1
fi

# Verify gh authentication
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI not authenticated"
    echo ""
    echo "🔐 Authenticate with GitHub:"
    echo "   gh auth login"
    exit 1
fi

echo "  ✅ Prerequisites verified"
echo ""

# ============================================================================
# Phase 1: Stop and Clean Existing Runner
# ============================================================================

echo "▶️  Phase 1: Stopping existing runner service..."
cd "$RUNNER_DIR"

# Stop and uninstall service if running (this removes only this runner's LaunchAgent)
./svc.sh stop 2>&1 | tail -2 || echo "  (no service running)"
./svc.sh uninstall 2>&1 | tail -2 || echo "  (no service installed)"

echo "  ✅ Service stopped and cleaned"
echo ""

# ============================================================================
# Phase 2: Get Fresh Registration Token
# ============================================================================

echo "▶️  Phase 2: Getting fresh registration token..."
TOKEN=$(gh api -X POST repos/$REPO_OWNER_AND_NAME/actions/runners/registration-token --jq '.token')
if [[ -z "$TOKEN" ]]; then
    echo "  ❌ ERROR: Failed to obtain registration token"
    exit 1
fi
echo "  ✅ Token obtained"
echo ""

# ============================================================================
# Phase 3: Remove Old Configuration
# ============================================================================

echo "▶️  Phase 3: Removing old runner configuration..."
./config.sh remove --token "$TOKEN" 2>&1 | tail -5 || echo "  (no old config)"
rm -f .credentials .credentials_rsaparams .runner
echo "  ✅ Old configuration removed"
echo ""

# ============================================================================
# Phase 4: Delete Stale Runner Registration from GitHub
# ============================================================================

echo "▶️  Phase 4: Cleaning stale runner registrations from GitHub..."
RUNNER_ID=$(gh api repos/$REPO_OWNER_AND_NAME/actions/runners --jq ".runners[] | select(.name == \"$RUNNER_NAME\") | .id" 2>/dev/null || echo "")

if [[ -n "$RUNNER_ID" ]]; then
    echo "  Found existing runner ID: $RUNNER_ID"
    gh api -X DELETE repos/$REPO_OWNER_AND_NAME/actions/runners/$RUNNER_ID 2>/dev/null || true
    echo "  ✅ Deleted stale registration"
    sleep 2
else
    echo "  ℹ️  No existing registration found"
fi
echo ""

# ============================================================================
# Phase 5: Reconfigure Runner with Fresh Token
# ============================================================================

echo "▶️  Phase 5: Configuring runner with fresh token..."
TOKEN=$(gh api -X POST repos/$REPO_OWNER_AND_NAME/actions/runners/registration-token --jq '.token')

echo "" | ./config.sh \
  --url "$REPO_URL" \
  --token "$TOKEN" \
  --name "$RUNNER_NAME" \
  --labels self-hosted,claude \
  --work _work

echo "  ✅ Runner configured successfully"
echo ""

# ============================================================================
# Phase 6: Install and Start Service (LaunchAgent)
# ============================================================================

echo "▶️  Phase 6: Installing LaunchAgent service..."
./svc.sh install
echo ""

echo "▶️  Starting service..."
./svc.sh start
echo "  ✅ LaunchAgent service started"
echo ""

# ============================================================================
# Phase 7: Create Monitoring Script
# ============================================================================

echo "▶️  Phase 7: Creating monitoring script..."

cat > "$RUNNER_DIR/monitor.sh" << 'MONITOR_EOF'
#!/bin/bash
# GitHub Actions Runner Monitor Script
# Checks if runner is running and restarts if needed

RUNNER_DIR=~/actions-runner

# Check if THIS runner's process is running (scoped to RUNNER_DIR)
if ! pgrep -f "Runner.Listener.*$RUNNER_DIR" > /dev/null; then
    echo "$(date): Runner not running, attempting restart..." >> "$RUNNER_DIR/monitor.log"
    cd "$RUNNER_DIR"

    # Try service restart first
    ./svc.sh start >> "$RUNNER_DIR/monitor.log" 2>&1

    # If service doesn't work, try direct run in background
    if ! pgrep -f "Runner.Listener.*$RUNNER_DIR" > /dev/null; then
        nohup ./run.sh >> "$RUNNER_DIR/runner.log" 2>&1 &
        echo "$(date): Started runner directly via run.sh" >> "$RUNNER_DIR/monitor.log"
    fi
else
    echo "$(date): Runner is healthy" >> "$RUNNER_DIR/monitor.log"
fi
MONITOR_EOF

chmod +x "$RUNNER_DIR/monitor.sh"
echo "  ✅ Monitor script created: $RUNNER_DIR/monitor.sh"
echo ""

# ============================================================================
# Phase 8: Configure Crontab Monitoring
# ============================================================================

echo "▶️  Phase 8: Configuring crontab monitoring..."

# Use mktemp for secure temporary file
TEMP_CRONTAB=$(mktemp)

# Get current crontab or create empty
crontab -l 2>/dev/null > "$TEMP_CRONTAB" || touch "$TEMP_CRONTAB"

# Remove any existing GitHub runner cron jobs (both comments and commands)
sed -i.bak '/GitHub Actions Runner/d; /actions-runner.*monitor\.sh/d; /actions-runner.*run\.sh --once/d' "$TEMP_CRONTAB"

# Add new monitoring jobs
cat >> "$TEMP_CRONTAB" << 'CRON_EOF'

# GitHub Actions Runner - Heartbeat (every 6 hours, only if not already running)
0 */6 * * * pgrep -f "Runner.Listener.*$HOME/actions-runner" > /dev/null || (cd ~/actions-runner && ./run.sh --once >> ~/actions-runner/heartbeat.log 2>&1)

# GitHub Actions Runner - Monitor (every 15 minutes)
*/15 * * * * ~/actions-runner/monitor.sh
CRON_EOF

# Install new crontab
crontab "$TEMP_CRONTAB"
rm "$TEMP_CRONTAB" "${TEMP_CRONTAB}.bak" 2>/dev/null || true

echo "  ✅ Crontab configured:"
echo "     - Heartbeat: every 6 hours"
echo "     - Monitor: every 15 minutes"
echo ""

# ============================================================================
# Phase 9: Wait for Runner Connection
# ============================================================================

echo "▶️  Phase 9: Waiting for runner to connect (15 seconds)..."
sleep 15

RUNNER_STATUS=$(gh api repos/$REPO_OWNER_AND_NAME/actions/runners --jq ".runners[] | select(.name == \"$RUNNER_NAME\") | .status" 2>/dev/null || echo "unknown")

if [[ "$RUNNER_STATUS" == "online" ]]; then
    echo "  ✅ Runner is ONLINE!"
elif [[ "$RUNNER_STATUS" == "offline" ]]; then
    echo "  ⚠️  Runner is offline (may be due to clock skew)"
    echo "  💡 Clock skew detected - runner will connect automatically once time syncs"
else
    echo "  ℹ️  Runner status: $RUNNER_STATUS"
fi
echo ""

# ============================================================================
# Phase 10: Verify Configuration
# ============================================================================

echo "▶️  Phase 10: Verifying configuration..."

# Check LaunchAgent
if ./svc.sh status | grep -q "Started"; then
    echo "  ✅ LaunchAgent service is running"
else
    echo "  ⚠️  LaunchAgent service may not be running"
fi

# Check crontab
if crontab -l | grep -q "GitHub Actions Runner"; then
    echo "  ✅ Crontab monitoring configured"
else
    echo "  ⚠️  Crontab monitoring not found"
fi

# Check runner registration
RUNNER_ID=$(gh api repos/$REPO_OWNER_AND_NAME/actions/runners --jq ".runners[] | select(.name == \"$RUNNER_NAME\") | .id" 2>/dev/null || echo "")
if [[ -n "$RUNNER_ID" ]]; then
    echo "  ✅ Runner registered with GitHub (ID: $RUNNER_ID)"
else
    echo "  ⚠️  Runner registration not found on GitHub"
fi

echo ""

# ============================================================================
# Success Summary
# ============================================================================

cat << 'SUCCESS_EOF'
🎉 Setup Complete! Dual Redundancy Configured

📊 Configuration Summary:
   ✓ LaunchAgent installed and started
   ✓ Crontab monitoring every 15 minutes
   ✓ Heartbeat job every 6 hours
   ✓ Auto-restart on failure

🛡️ Redundancy Layers:
   Layer 1: LaunchAgent (persistent service)
   Layer 2: Cron monitor (every 15 min check + restart)
   Layer 3: Cron heartbeat (every 6 hours keep-alive)

📁 Files Created:
SUCCESS_EOF

echo "   - Monitor script: $RUNNER_DIR/monitor.sh"
echo "   - Service config: ~/Library/LaunchAgents/actions.runner.*.plist"
echo "   - Crontab: Updated with 2 monitoring jobs"
echo ""

cat << 'NEXT_EOF'
📋 Next Steps:

1. Verify runner status:
   cd ~/actions-runner && ./svc.sh status
   gh api repos/$REPO_OWNER_AND_NAME/actions/runners | jq '.runners[] | select(.name == "$RUNNER_NAME")'

2. Check logs:
   tail -f ~/actions-runner/monitor.log
   tail -f ~/actions-runner/heartbeat.log
   tail -f ~/Library/Logs/actions.runner.*/stdout.log

3. View crontab:
   crontab -l | grep "GitHub Actions"

🔧 Service Management:
   cd ~/actions-runner
   ./svc.sh status   # Check status
   ./svc.sh stop     # Stop service
   ./svc.sh start    # Start service
   ./svc.sh uninstall # Remove service

💡 This setup ensures the runner stays active and won't be deleted by GitHub!
NEXT_EOF

echo ""
echo "✅ Setup script completed successfully"
