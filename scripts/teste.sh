#!/bin/bash
# /teste - Run End2End Tests (Mock Mode)
# Runs end2end tests using mocked services (current behavior)

set -e

# Set test mode environment
export TEST_MODE=mock

# Validate environment
if [ ! -f "./run_e2e_tests.sh" ]; then
    echo "❌ Error: run_e2e_tests.sh not found. Must run from project root."
    exit 1
fi

echo "🧪 Running end-to-end tests in MOCK mode..."
echo "📊 Service Provider: MockServiceProvider"
echo "💰 Cost: $0 (no real services)"
echo ""

# Run tests with pattern if provided
if [ -n "$1" ]; then
    echo "🔍 Pattern filtering not yet implemented in run_e2e_tests.sh"
    echo "🔍 Running all end-to-end tests..."
fi

# Execute the enhanced test runner
./run_e2e_tests.sh

echo ""
echo "✅ Mock mode testing complete"
echo ""
echo "💡 For real service testing, use:"
echo "   /tester  - Real mode"
echo "   /testerc - Real mode with data capture"