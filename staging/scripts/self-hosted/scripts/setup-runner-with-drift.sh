#!/bin/bash
#
# GitHub Runner Setup with Clock Drift Support
# Temporarily syncs clock during registration, then restores drift
#
# Usage: ./scripts/setup-runner-with-drift.sh [REPO_URL] [RUNNER_NAME]
#
# Arguments:
#   REPO_URL      - Full GitHub repo URL (default: https://github.com/jleechanorg/your-project.com)
#   RUNNER_NAME   - Name for the runner (default: claude-drift-runner)
#
# Examples:
#   ./scripts/setup-runner-with-drift.sh
#   ./scripts/setup-runner-with-drift.sh https://github.com/myorg/myrepo my-runner
#

set -e

# Parse arguments or use defaults
RUNNER_DIR="$HOME/actions-runner"
REPO_URL="${1:-https://github.com/jleechanorg/your-project.com}"
RUNNER_NAME="${2:-claude-drift-runner}"
DRIFT_MINUTES=10

# Extract owner/repo from URL for API calls
# Handles both https://github.com/owner/repo and owner/repo formats
if [[ "$REPO_URL" =~ ^https://github.com/(.+)$ ]]; then
  REPO_OWNER_AND_NAME="${BASH_REMATCH[1]}"
elif [[ "$REPO_URL" =~ ^[^/]+/[^/]+$ ]]; then
  # If just owner/repo provided, construct full URL
  REPO_OWNER_AND_NAME="$REPO_URL"
  REPO_URL="https://github.com/$REPO_URL"
else
  echo "❌ Invalid repository URL format. Expected: https://github.com/owner/repo or owner/repo"
  exit 1
fi

echo "🕐 GitHub Runner Setup with Clock Drift Support"
echo "================================================================"
echo "Repository:    $REPO_URL"
echo "Runner Name:   $RUNNER_NAME"
echo "Runner Dir:    $RUNNER_DIR"
echo "================================================================"
echo ""

# Uninstall existing service
echo "▶️  Stopping existing runner service..."
cd "$RUNNER_DIR"
./svc.sh uninstall 2>&1 | tail -2 || echo "  (no service to uninstall)"
echo ""

# Sync clock
echo "▶️  Syncing clock with NTP (requires sudo)..."
sudo sntp -sS time.apple.com
SYNCED_TIME=$(date)
echo "  ✅ Clock synced: $SYNCED_TIME"
echo ""

# Get token
echo "▶️  Getting registration token..."
TOKEN=$(gh api -X POST repos/$REPO_OWNER_AND_NAME/actions/runners/registration-token --jq '.token')
echo "  ✅ Token obtained"
echo ""

# Remove old configuration
echo "▶️  Removing old runner configuration..."
./config.sh remove --token "$TOKEN" 2>&1 | tail -5 || echo "  (no old config)"
rm -f .credentials .credentials_rsaparams .runner
echo "  ✅ Old config removed"
echo ""

# Configure runner (while clock is synced)
echo "▶️  Configuring runner with synced clock..."
./config.sh --url "$REPO_URL" \
  --token "$TOKEN" \
  --name "$RUNNER_NAME" \
  --labels self-hosted,claude \
  --unattended
echo "  ✅ Runner configured"
echo ""

# Install and start service (while synced)
echo "▶️  Installing service..."
./svc.sh install
echo ""

echo "▶️  Starting service..."
./svc.sh start
echo "  ✅ Service started"
echo ""

# Wait for runner to establish session
echo "▶️  Waiting for runner to connect to GitHub (12 seconds)..."
sleep 12

# Check if runner is online
RUNNER_STATUS=$(gh api repos/$REPO_OWNER_AND_NAME/actions/runners --jq ".runners[] | select(.name == \"$RUNNER_NAME\") | .status")

if [ "$RUNNER_STATUS" = "online" ]; then
  echo "  ✅ Runner is ONLINE!"
else
  echo "  ⚠️  Runner status: $RUNNER_STATUS (may still be connecting...)"
  echo "  Waiting additional 10 seconds..."
  sleep 10
  RUNNER_STATUS=$(gh api repos/$REPO_OWNER_AND_NAME/actions/runners --jq ".runners[] | select(.name == \"$RUNNER_NAME\") | .status")
  echo "  Runner status now: $RUNNER_STATUS"
fi
echo ""

echo "🎉 Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Restore your clock drift:"
echo "   ./self-hosted/scripts/restore-clock-drift.sh"
echo ""
echo "2. Test the runner:"
echo "   gh workflow run test-self-hosted-runner.yml"
echo "   gh run watch"
echo ""
echo "🔧 Service management:"
echo "   cd $RUNNER_DIR"
echo "   ./svc.sh status   # Check status"
echo "   ./svc.sh stop     # Stop service"
echo "   ./svc.sh start    # Start service"
echo ""
