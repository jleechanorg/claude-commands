#!/bin/bash

# Test script to compare cerebras direct script default mode vs light mode

set -euo pipefail

# Test prompt for Amazon MVP design
TEST_PROMPT="Create a simple Python function that adds two numbers."

# Create a directory for test results
mkdir -p cerebras_test_results

echo "Testing Cerebras script with default parameters vs --light mode"
echo "=========================================================="
echo ""

# Test 1: Default mode
echo "Test 1: Running with default parameters"
echo "--------------------------------------"
echo "Command: /home/jleechan/projects/worldarchitect.ai/worktree_worker/.claude/commands/cerebras/cerebras_direct.sh \"$TEST_PROMPT\""
echo ""

# Save output to file
/home/jleechan/projects/worldarchitect.ai/worktree_worker/.claude/commands/cerebras/cerebras_direct.sh "$TEST_PROMPT" > cerebras_test_results/default_mode_output.txt 2>&1 || echo "Default mode test completed with exit code $?"

# Extract timing information
DEFAULT_TIMING=$(grep "CEREBRAS GENERATED IN" cerebras_test_results/default_mode_output.txt || echo "Timing not found")
echo "Default mode timing: $DEFAULT_TIMING"
echo ""

# Wait for 30 seconds to avoid rate limiting
echo "Waiting 30 seconds to avoid rate limiting..."
sleep 30

# Test 2: Light mode
echo "Test 2: Running with --light mode"
echo "-------------------------------"
echo "Command: /home/jleechan/projects/worldarchitect.ai/worktree_worker/.claude/commands/cerebras/cerebras_direct.sh --light \"$TEST_PROMPT\""
echo ""

# Save output to file
/home/jleechan/projects/worldarchitect.ai/worktree_worker/.claude/commands/cerebras/cerebras_direct.sh --light "$TEST_PROMPT" > cerebras_test_results/light_mode_output.txt 2>&1 || echo "Light mode test completed with exit code $?"

# Extract timing information
LIGHT_TIMING=$(grep "CEREBRAS GENERATED IN" cerebras_test_results/light_mode_output.txt || echo "Timing not found")
echo "Light mode timing: $LIGHT_TIMING"
echo ""

echo "Test results saved to cerebras_test_results/ directory"
echo "Files created:"
echo "  - default_mode_output.txt"
echo "  - light_mode_output.txt"