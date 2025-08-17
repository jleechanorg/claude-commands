#!/bin/bash

# Direct Cerebras API test to compare with qwen CLI

echo "=== Direct Cerebras API Speed Test ==="
echo ""

PROMPT="Write a simple Python function to add two numbers"

# Test 1: Direct curl to Cerebras
echo "Test 1: Direct Cerebras API call"
echo "--------------------------------"
START=$(date +%s%N)

curl -s -X POST "https://api.cerebras.ai/v1/chat/completions" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen-3-coder-480b\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"$PROMPT\"}
    ],
    \"max_tokens\": 500,
    \"temperature\": 0.1,
    \"stream\": false
  }" > /tmp/cerebras_direct.json

END=$(date +%s%N)
ELAPSED=$((($END - $START) / 1000000))
echo "Direct API time: ${ELAPSED}ms"

# Parse response
if [ -f /tmp/cerebras_direct.json ]; then
    TOKENS=$(jq -r '.usage.completion_tokens // 0' /tmp/cerebras_direct.json)
    echo "Tokens generated: $TOKENS"
    if [ "$TOKENS" -gt 0 ]; then
        TOKENS_PER_SEC=$(echo "scale=2; $TOKENS * 1000 / $ELAPSED" | bc)
        echo "Tokens/sec: $TOKENS_PER_SEC"
    fi
fi

echo ""
echo "Test 2: qwen CLI with same prompt"
echo "---------------------------------"
START=$(date +%s%N)

timeout 10 qwen -p "$PROMPT" --yolo --load-memory-from-include-directories=false > /tmp/qwen_output.txt 2>&1

END=$(date +%s%N)
ELAPSED=$((($END - $START) / 1000000))
echo "qwen CLI time: ${ELAPSED}ms"

echo ""
echo "=== Performance Comparison ==="
echo "Direct API should be close to Cerebras's advertised speed"
echo "qwen CLI overhead is the difference between the two"