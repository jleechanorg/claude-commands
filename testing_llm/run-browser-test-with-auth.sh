#!/bin/bash
# Run browser tests with proper authentication credentials
# This script ensures test credentials are loaded before running tests

# Enable strict error handling
set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load test credentials
echo "🔐 Loading test credentials..."
if ! source "$SCRIPT_DIR/load-test-credentials.sh"; then
    echo "❌ Failed to load test credentials"
    exit 1
fi

# Verify credentials are available
if ! verify_test_credentials; then
    echo "❌ Test credentials validation failed"
    exit 1
fi

# Export credentials for Playwright/Puppeteer
export TEST_EMAIL
export TEST_PASSWORD

echo ""
echo "🌐 Starting browser test with authentication..."
echo "   Using email: $TEST_EMAIL"
echo ""

# Pass all arguments to the test command
# This allows usage like: ./run-browser-test-with-auth.sh /testuif
if [ $# -eq 0 ]; then
    echo "Usage: $0 <test-command> [arguments]"
    echo "Example: $0 /testuif"
    echo "Example: $0 ./run_ui_tests.sh mock"
    exit 1
fi

# Execute the test command with credentials available
echo "🚀 Executing: $*"
exec "$@"
