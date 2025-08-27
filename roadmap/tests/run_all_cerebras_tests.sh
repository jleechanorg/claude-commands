#!/bin/bash

# Script to run all cerebras enhancement tests

set -euo pipefail

echo "Running all cerebras enhancement tests"
echo "====================================="
echo ""

# Create results directory
mkdir -p cerebras_test_results

# Test 1: Performance comparison
echo "Test 1: Performance comparison (default vs light mode)"
echo "-----------------------------------------------------"
/home/jleechan/projects/worldarchitect.ai/worktree_worker/roadmap/tests/run_cerebras_comparison_test.sh
echo ""

# Test 2: Security filtering
echo "Test 2: Security filtering test"
echo "-------------------------------"
/home/jleechan/projects/worldarchitect.ai/worktree_worker/roadmap/tests/test_cerebras_security_filtering.sh
echo ""

echo "All tests completed. Results are in cerebras_test_results/ directory."