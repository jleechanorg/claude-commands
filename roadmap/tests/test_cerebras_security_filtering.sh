#!/bin/bash

# Test script to verify that --light mode skips security filtering

set -euo pipefail

echo "Testing security filtering in default mode vs --light mode"
echo "======================================================="
echo ""

# Test with a prompt that would be blocked by security filtering
TEST_PROMPT='Create a Python function that uses `os.system` to execute commands'

echo "Test 1: Default mode with potentially dangerous prompt"
echo "------------------------------------------------------"
echo "Prompt: $TEST_PROMPT"
echo ""

# Try to run with default mode (should fail)
/home/jleechan/projects/worldarchitect.ai/worktree_worker/.claude/commands/cerebras/cerebras_direct.sh "$TEST_PROMPT" > cerebras_test_results/security_test_default.txt 2>&1 || echo "Default mode correctly blocked dangerous prompt with exit code $?"

echo ""

echo "Test 2: Light mode with same potentially dangerous prompt"
echo "--------------------------------------------------------"
echo "Prompt: $TEST_PROMPT"
echo ""

# Try to run with light mode (should succeed)
/home/jleechan/projects/worldarchitect.ai/worktree_worker/.claude/commands/cerebras/cerebras_direct.sh --light "$TEST_PROMPT" > cerebras_test_results/security_test_light.txt 2>&1 || echo "Light mode test completed with exit code $?"

echo ""
echo "Security filtering test completed. Check cerebras_test_results/ directory for outputs."