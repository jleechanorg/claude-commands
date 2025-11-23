#!/usr/bin/env bash
# Example 1: Quick Smoke Test
#
# Demonstrates: Fast smoke testing with Superpowers Chrome
# Duration: ~15-30 seconds
# Use case: CI/CD fast feedback, daily development checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_URL="${1:-http://localhost:5000}"

echo "🚀 Quick Smoke Test with Superpowers Chrome"
echo "============================================"
echo "URL: $BASE_URL"
echo ""

# Use the WorldArchitect wrapper
"$SCRIPT_DIR/../worldarchitect-chrome.sh" smoke "$BASE_URL"

echo ""
echo "✅ Smoke test completed in ~15-30 seconds"
echo ""
echo "💡 Why Superpowers Chrome?"
echo "   - Zero dependencies"
echo "   - Reuses existing Chrome (no fresh launch)"
echo "   - CLI-friendly for scripts"
echo "   - 3x faster than Playwright for smoke tests"
echo ""
echo "📊 Comparison:"
echo "   Superpowers Chrome: 15-30s"
echo "   Playwright:         45-60s"
