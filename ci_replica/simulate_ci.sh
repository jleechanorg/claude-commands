#!/bin/bash
# Script to simulate GitHub Actions CI environment locally

echo "🔍 Simulating CI environment..."

# Save current environment
export GOOGLE_APPLICATION_CREDENTIALS_BACKUP="$GOOGLE_APPLICATION_CREDENTIALS"
export FIREBASE_CONFIG_BACKUP="$FIREBASE_CONFIG"

# Clear Firebase credentials to simulate CI
unset GOOGLE_APPLICATION_CREDENTIALS
unset FIREBASE_CONFIG
unset GCLOUD_PROJECT
unset FIREBASE_PROJECT_ID
unset GOOGLE_CLOUD_PROJECT

# Set CI flags
export CI=true
export GITHUB_ACTIONS=true
export TESTING=true

echo "✅ Environment variables cleared - simulating CI"
echo "🧪 Running test that fails in CI..."

# Run the failing test (follow guideline: execute Python from project root)
# Find project root first
PROJECT_ROOT="$(cd "$(dirname "$0")/.."; pwd)"
cd "$PROJECT_ROOT" && python mvp_site/test_integration/test_integration_mock.py

exit_code=$?

# Restore environment
echo "🔄 Restoring local environment..."
export GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_APPLICATION_CREDENTIALS_BACKUP"
export FIREBASE_CONFIG="$FIREBASE_CONFIG_BACKUP"
unset GOOGLE_APPLICATION_CREDENTIALS_BACKUP
unset FIREBASE_CONFIG_BACKUP
unset CI
unset GITHUB_ACTIONS

if [ $exit_code -eq 0 ]; then
    echo "✅ Test passed - this suggests a different issue"
else
    echo "❌ Test failed - successfully reproduced CI environment issue!"
fi

exit $exit_code