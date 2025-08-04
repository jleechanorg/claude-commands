#!/bin/bash
# Load test credentials from various sources
# This script provides a centralized way to load test credentials

# Enable strict error handling
set -euo pipefail

# Function to load credentials
load_test_credentials() {
    # Check if already set in environment
    if [ -n "${TEST_EMAIL:-}" ] && [ -n "${TEST_PASSWORD:-}" ]; then
        echo "✅ Test credentials already loaded from environment"
        return 0
    fi

    # Try loading from secure config file
    local config_file="$HOME/.config/worldarchitect-ai/test-credentials.env"
    if [ -f "$config_file" ]; then
        echo "Loading credentials from $config_file..."
        # shellcheck disable=SC1090
        source "$config_file"
        echo "✅ Credentials loaded from config file"
        return 0
    fi

    # Try loading from .bashrc
    if [ -f "$HOME/.bashrc" ]; then
        # Extract exports from .bashrc
        local email=$(grep "export TEST_EMAIL=" "$HOME/.bashrc" | grep -v "^#" | sed 's/export TEST_EMAIL=//' | tr -d '"')
        local password=$(grep "export TEST_PASSWORD=" "$HOME/.bashrc" | grep -v "^#" | sed 's/export TEST_PASSWORD=//' | tr -d '"')

        if [ -n "$email" ] && [ -n "$password" ]; then
            export TEST_EMAIL="$email"
            export TEST_PASSWORD="$password"
            echo "✅ Credentials loaded from .bashrc"
            return 0
        fi
    fi

    # No credentials found
    echo "❌ Error: Test credentials not found!"
    echo "Please set TEST_EMAIL and TEST_PASSWORD in one of:"
    echo "  1. Environment variables"
    echo "  2. ~/.config/worldarchitect-ai/test-credentials.env"
    echo "  3. ~/.bashrc"
    return 1
}

# Verify credentials are valid
verify_test_credentials() {
    if [ -z "${TEST_EMAIL:-}" ]; then
        echo "❌ Error: TEST_EMAIL is not set"
        return 1
    fi

    if [ -z "${TEST_PASSWORD:-}" ]; then
        echo "❌ Error: TEST_PASSWORD is not set"
        return 1
    fi

    # Basic email format check
    if [[ ! "$TEST_EMAIL" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
        echo "❌ Error: TEST_EMAIL doesn't look like a valid email address"
        return 1
    fi

    echo "✅ Test credentials verified:"
    echo "   Email: $TEST_EMAIL"
    echo "   Password: ${TEST_PASSWORD:0:3}..."
    return 0
}

# Main execution
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    # Script is being executed directly
    echo "Loading test credentials..."
    if load_test_credentials && verify_test_credentials; then
        echo "✅ Test credentials are ready for use"
        # Export for child processes
        export TEST_EMAIL
        export TEST_PASSWORD
    else
        exit 1
    fi
else
    # Script is being sourced
    load_test_credentials
fi
