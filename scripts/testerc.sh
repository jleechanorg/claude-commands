#!/bin/bash
# ⚠️ REQUIRES PROJECT ADAPTATION
# This script contains project-specific paths and may need modification

#!/bin/bash
# /testerc - Run End2End Tests (Real Mode + Capture)
# Runs end2end tests using real services AND captures data for mock generation

set -e

# Set test mode environment
export TEST_MODE=capture

# Check for required environment variables (updated naming)
if [[ -z "$TEST_GEMINI_API_KEY" ]]; then
    echo "❌ ERROR: TEST_GEMINI_API_KEY not set"
    echo "💡 Set up test environment:"
    echo "   export TEST_GEMINI_API_KEY=your_test_api_key"
    echo "   export TEST_FIRESTORE_PROJECT=worldarchitect-test  # optional"
    exit 1
fi

# Validate environment
if [ ! -f "./run_e2e_tests.sh" ]; then
    echo "❌ Error: run_e2e_tests.sh not found. Must run from project root."
    exit 1
fi

# Create capture directory with timestamp
CAPTURE_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CAPTURE_DIR="/tmp/test_captures/$CAPTURE_TIMESTAMP"
export TEST_CAPTURE_DIR="$CAPTURE_DIR"

echo "📡 Running end-to-end tests in CAPTURE mode..."
echo "📊 Service Provider: RealServiceProvider (with capture)"
echo "🔧 Firestore Project: ${TEST_FIRESTORE_PROJECT:-worldarchitect-test}"
echo "🤖 Gemini API: Configured"
echo "📁 Capture Directory: $CAPTURE_DIR"
echo ""

# Warning about costs and data capture
echo "⚠️  WARNING: Capture mode will use real APIs (costs) and record all interactions"
echo "   - Gemini API calls will cost money"
echo "   - Firestore writes will create real data"
echo "   - All service interactions will be captured and stored"
echo "   - Test cleanup will run automatically"
echo ""

# Confirmation prompt
read -p "Continue with real service testing and data capture? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Capture mode testing cancelled"
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
echo "✅ Capture mode testing complete"
echo "📁 Captured data available in: $CAPTURE_DIR"

# Generate analysis report if possible
echo "📊 Analysis and cleanup handled by run_e2e_tests.sh"
echo ""
echo "📋 Next Steps:"
echo "   - Review captured data in $CAPTURE_DIR"
echo "   - Use data to improve mock implementations"
echo "   - Run /teste to validate mock accuracy"
