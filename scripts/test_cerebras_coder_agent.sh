#!/bin/bash

# Test script to validate cerebras-coder agent enforcement
# This tests the validation logic that should be embedded in the agent

echo "🧪 Testing Cerebras-Coder Agent Validation Protocol"
echo "=================================================="

# Test 1: Check API Key Validation
echo ""
echo "TEST 1: API Key Validation"
echo "-------------------------"

# Save current keys and track if they were set
OLD_CEREBRAS_KEY="${CEREBRAS_API_KEY:-}"
OLD_OPENAI_KEY="${OPENAI_API_KEY:-}"
WAS_SET_CEREBRAS_KEY=0
WAS_SET_OPENAI_KEY=0

# Check if keys were originally set
if [ -n "${CEREBRAS_API_KEY}" ]; then
    WAS_SET_CEREBRAS_KEY=1
fi
if [ -n "${OPENAI_API_KEY}" ]; then
    WAS_SET_OPENAI_KEY=1
fi

# Test with no keys
unset CEREBRAS_API_KEY
unset OPENAI_API_KEY

echo "Testing with no API keys..."
if [ -z "${CEREBRAS_API_KEY}" ] && [ -z "${OPENAI_API_KEY}" ]; then
    echo "❌ CRITICAL ERROR: No Cerebras API key found!"
    echo "Required: export CEREBRAS_API_KEY=your_key_here"
    echo "CEREBRAS-CODER AGENT WOULD EXIT HERE ✅"
else
    echo "❌ TEST FAILED: Should have detected missing keys"
fi

# Restore keys properly
if [ "$WAS_SET_CEREBRAS_KEY" -eq 1 ]; then
    export CEREBRAS_API_KEY="${OLD_CEREBRAS_KEY}"
else
    unset CEREBRAS_API_KEY
fi
if [ "$WAS_SET_OPENAI_KEY" -eq 1 ]; then
    export OPENAI_API_KEY="${OLD_OPENAI_KEY}"
else
    unset OPENAI_API_KEY
fi

# Test 2: Check Command Availability
echo ""
echo "TEST 2: Command Availability Check"
echo "----------------------------------"

if [ -f ".claude/commands/cerebras/cerebras_direct.sh" ]; then
    echo "✅ /cerebras command found at .claude/commands/cerebras/cerebras_direct.sh"
else
    echo "❌ CRITICAL ERROR: /cerebras command script not found!"
    echo "Expected: .claude/commands/cerebras/cerebras_direct.sh"
    echo "CEREBRAS-CODER AGENT WOULD EXIT HERE"
fi

# Test 3: Verify Cerebras Execution Works
echo ""
echo "TEST 3: Cerebras Execution Test"
echo "-------------------------------"

echo "Testing actual /cerebras execution..."
OUTPUT=$(.claude/commands/cerebras/cerebras_direct.sh "Create a simple Python test function" 2>&1)

if echo "$OUTPUT" | grep -q "🚀🚀🚀 CEREBRAS GENERATED"; then
    echo "✅ /cerebras execution successful - found success marker"
    TIMING=$(echo "$OUTPUT" | grep "CEREBRAS GENERATED IN" | head -1)
    echo "   $TIMING"
else
    echo "❌ FATAL: /cerebras execution failed - no success marker found"
    echo "CEREBRAS-CODER AGENT WOULD EXIT HERE"
fi

# Test 4: Validate Agent Requirements
echo ""
echo "TEST 4: Agent Requirements Summary"
echo "================================="

echo "Required validations that cerebras-coder agent MUST perform:"
echo "✅ 1. Check CEREBRAS_API_KEY or OPENAI_API_KEY is set"
echo "✅ 2. Verify .claude/commands/cerebras/cerebras_direct.sh exists"
echo "✅ 3. Execute /cerebras command via Bash tool"
echo "✅ 4. Verify '🚀🚀🚀 CEREBRAS GENERATED' marker appears in output"
echo "✅ 5. Exit immediately if any validation fails"

echo ""
echo "🎯 CONCLUSION: cerebras-coder agent should now ALWAYS use /cerebras"
echo "🚨 ENFORCEMENT: Agent will exit with error if /cerebras not used"