#!/usr/bin/env bash
# Example 2: Visual Regression Workflow
#
# Demonstrates: Visual regression testing with Playwright
# Duration: ~8-12 seconds per page
# Use case: PR visual verification, design system testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-compare}"  # baseline or compare

echo "🎨 Visual Regression Workflow with Playwright"
echo "=============================================="
echo "Mode: $MODE"
echo ""

cd "$SCRIPT_DIR/.."

if [ "$MODE" == "baseline" ]; then
  echo "📸 Capturing baseline screenshots..."
  node run.js examples/visual-regression-complete.js --baseline
else
  echo "🔍 Comparing against baselines..."
  node run.js examples/visual-regression-complete.js
fi

echo ""
echo "✅ Visual regression $MODE completed"
echo ""
echo "💡 Why Playwright?"
echo "   - Built-in screenshot comparison"
echo "   - Multi-viewport support (desktop/tablet/mobile)"
echo "   - Baseline management system"
echo "   - Automated diff generation"
echo ""
echo "📊 Captured viewports:"
echo "   Desktop: 1920x1080"
echo "   Tablet:  768x1024"
echo "   Mobile:  375x667"
echo ""
echo "📁 Screenshots: /tmp/playwright-baselines/"
echo "📁 Diffs:       /tmp/playwright-diffs/"
