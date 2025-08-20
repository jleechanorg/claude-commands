#!/bin/bash
"""
CI Integration Tests for Orchestration System

Runs the critical integration tests in CI/CD pipeline to prevent
regression of the stale task queue bug and related issues.
"""

set -e  # Exit on any error

echo "🧪 Starting Orchestration Integration Tests..."
echo "=================================================="

cd "$(dirname "$0")"

# Run stale task prevention tests (critical)
echo "📋 Running stale task prevention tests..."
python3 run_integration_tests.py --stale-only

# Run lifecycle management tests (important)
echo "📋 Running lifecycle management tests..."
python3 run_integration_tests.py --lifecycle-only

# Run task execution verification tests (important)
echo "📋 Running task execution verification tests..."
python3 run_integration_tests.py --verification-only

echo "=================================================="
echo "✅ All orchestration integration tests completed successfully!"
echo ""
echo "These tests specifically prevent:"
echo "  - Stale task queue bugs (289 stale files scenario)"
echo "  - Prompt file lifecycle issues"
echo "  - Task execution mismatches"
echo "  - Resource leaks from tmux sessions"
echo ""
echo "Coverage: Orchestration reliability and state management"
