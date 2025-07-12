#!/bin/bash

# Simple curl command to test structured fields API directly
# This tests the /api/campaigns/{id}/interaction endpoint

# Set test mode and port
export TESTING=true
PORT=8086

echo "Starting test server..."
# Start server in background
TESTING=true python mvp_site/main.py serve --port $PORT &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "Testing structured fields API..."
echo "================================"

# Create a test campaign first
echo "1. Creating test campaign..."
CAMPAIGN_RESPONSE=$(curl -s -X POST http://localhost:$PORT/api/campaigns \
  -H "Content-Type: application/json" \
  -H "X-Test-User-Id: test-user-123" \
  -d '{
    "title": "Test Campaign",
    "prompt": "A simple test campaign",
    "campaign_type": "custom"
  }')

CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['campaign_id'])")
echo "Created campaign: $CAMPAIGN_ID"

# Test interaction with debug mode to see structured fields
echo -e "\n2. Testing interaction with debug mode..."
INTERACTION_RESPONSE=$(curl -s -X POST http://localhost:$PORT/api/campaigns/$CAMPAIGN_ID/interaction \
  -H "Content-Type: application/json" \
  -H "X-Test-User-Id: test-user-123" \
  -d '{
    "input_text": "I attack the goblin with my sword!",
    "mode": "character",
    "debug_mode": true
  }')

echo "Response from API:"
echo "$INTERACTION_RESPONSE" | python -m json.tool

# Check for structured fields
echo -e "\n3. Checking for structured fields..."
echo "$INTERACTION_RESPONSE" | python -c "
import sys, json
data = json.load(sys.stdin)
print('✓ response field:', 'response' in data)
print('✓ debug_info field:', 'debug_info' in data)
print('✓ dice_rolls field:', 'dice_rolls' in data)
print('✓ resources field:', 'resources' in data)
print('✓ planning_block field:', 'planning_block' in data)
print('✓ session_header field:', 'session_header' in data)

if 'debug_info' in data:
    print('\nDebug info contents:')
    for key in data['debug_info']:
        print(f'  - {key}')
"

# Cleanup
echo -e "\nCleaning up..."
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo "Test complete!"