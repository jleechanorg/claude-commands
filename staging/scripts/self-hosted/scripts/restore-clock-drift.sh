#!/bin/bash
#
# Restore Clock Drift for GitHub Actions Runner
# Restores +10 minute clock drift after runner setup
#

set -e

DRIFT_MINUTES=10

echo "🕐 Restoring Clock Drift"
echo "================================================================"
echo ""

echo "Current time: $(date)"
echo ""

echo "▶️  Restoring clock drift (+${DRIFT_MINUTES} minutes)..."
echo "   (This requires sudo)"
sudo date -v+${DRIFT_MINUTES}M
echo "  ✅ Clock restored: $(date)"
echo ""

echo "▶️  Verifying runner still online..."
sleep 3
RUNNER_STATUS=$(gh api repos/jleechanorg/your-project.com/actions/runners --jq '.runners[] | select(.name == "claude-drift-runner")')

if [ -n "$RUNNER_STATUS" ]; then
  echo "  Runner status:"
  echo "$RUNNER_STATUS" | jq '{name, status, busy}'
  echo ""

  STATUS=$(echo "$RUNNER_STATUS" | jq -r '.status')
  if [ "$STATUS" = "online" ]; then
    echo "✅ SUCCESS: Runner remains online with clock drift restored!"
  else
    echo "⚠️  WARNING: Runner status is $STATUS"
    echo "   This is expected - the runner should come back online shortly"
  fi
else
  echo "⚠️  Runner not found. Checking all runners..."
  gh api repos/jleechanorg/your-project.com/actions/runners --jq '.runners[] | {name, status}'
fi

echo ""
echo "🎉 Clock drift restored to +${DRIFT_MINUTES} minutes"
echo ""
