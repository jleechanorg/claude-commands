#!/bin/bash
# ⚠️ REQUIRES PROJECT ADAPTATION
# This script contains project-specific paths and may need modification

#!/bin/bash
# /tester - Run End2End Tests (Real Mode)
# Runs end2end tests using actual services (Firestore, Gemini)

set -e

# Set test mode environment
export TEST_MODE=real

# Check for required environment variables
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "❌ ERROR: GEMINI_API_KEY not set"
    echo "💡 Set up test environment:"
    echo "   export GEMINI_API_KEY=your_api_key"
    echo "   export TEST_FIRESTORE_PROJECT=worldarchitect-test  # optional"
    exit 1
fi

# Validate environment
if [ ! -f "./run_e2e_tests.sh" ]; then
    echo "❌ Error: run_e2e_tests.sh not found. Must run from project root."
    exit 1
fi

echo "🚀 Running end-to-end tests in REAL mode..."
echo "📊 Service Provider: RealServiceProvider"
echo "🔧 Firestore Project: ${TEST_FIRESTORE_PROJECT:-worldarchitect-test}"
echo "🤖 Gemini API: Configured"
echo ""

# Warning about costs
echo "⚠️  WARNING: Real service mode will use actual APIs and may incur costs"
echo "   - Gemini API calls will cost money"
echo "   - Firestore writes will create real data"
echo "   - Test cleanup will run automatically"
echo ""

# Confirmation prompt
read -p "Continue with real service testing? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Real service testing cancelled"
    exit 1
fi

# Run tests with pattern if provided
if [ -n "$1" ]; then
    echo "🔍 Pattern filtering not yet implemented in run_e2e_tests.sh"
    echo "🔍 Running all end-to-end tests..."
fi

# Execute the enhanced test runner
./run_e2e_tests.sh

echo ""
echo "✅ Real mode testing complete"
echo ""
echo "💡 To capture data for mock updates:"
echo "   /testerc - Real mode with data capture"
