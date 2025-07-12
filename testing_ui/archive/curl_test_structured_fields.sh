#!/bin/bash
# Simple curl test for structured fields
# This bypasses the browser and tests the API directly

echo "=== Testing Structured Fields API ==="
echo

# Start server
echo "Starting test server..."
TESTING=true PORT=8091 python mvp_site/main.py serve &
SERVER_PID=$!

# Wait for server
sleep 5

# The backend expects X-Test-User-Id header when TESTING=true
echo "Creating campaign..."
CAMPAIGN_RESPONSE=$(curl -s -X POST http://localhost:8091/api/campaigns \
  -H "Content-Type: application/json" \
  -H "X-Test-Bypass-Auth: true" \
  -H "X-Test-User-Id: test-user-123" \
  -d '{
    "title": "Test Campaign",
    "prompt": "A test campaign for structured fields",
    "campaign_type": "custom"
  }')

echo "Campaign response:"
echo "$CAMPAIGN_RESPONSE" | python -m json.tool

# Extract campaign ID
CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | python -c "import sys, json; data = json.load(sys.stdin); print(data.get('campaign_id', 'ERROR'))")

if [ "$CAMPAIGN_ID" = "ERROR" ]; then
    echo "Failed to create campaign!"
    kill $SERVER_PID
    exit 1
fi

echo
echo "Campaign ID: $CAMPAIGN_ID"
echo

# Test interaction with debug mode
echo "Testing interaction with debug mode..."

# Show the exact request being sent
echo "Request payload:"
echo '{
    "input": "I attack the goblin with my sword! Roll for damage.",
    "mode": "character",
    "debug_mode": true
}'

INTERACTION_RESPONSE=$(curl -s -X POST http://localhost:8091/api/campaigns/$CAMPAIGN_ID/interaction \
  -H "Content-Type: application/json" \
  -H "X-Test-Bypass-Auth: true" \
  -H "X-Test-User-Id: test-user-123" \
  -d '{
    "input": "I attack the goblin with my sword! Roll for damage.",
    "mode": "character",
    "debug_mode": true
  }')

echo "Interaction response:"
echo "$INTERACTION_RESPONSE" | python -m json.tool

# Analyze the response
echo
echo "=== ANALYSIS ==="
echo "$INTERACTION_RESPONSE" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('Top-level keys:', sorted(data.keys()))
    
    # Check for fields at top level
    print('\\nTop-level structured fields:')
    for field in ['dice_rolls', 'resources', 'planning_block', 'session_header']:
        if field in data:
            print(f'  ✓ {field}: {type(data[field]).__name__}')
        else:
            print(f'  ✗ {field}: not found')
    
    # Check debug_info
    if 'debug_info' in data:
        print('\\ndebug_info contents:')
        for field in data['debug_info']:
            print(f'  - {field}: {type(data[\"debug_info\"][field]).__name__}')
        
        # Check for nested fields
        print('\\nNested structured fields in debug_info:')
        for field in ['dice_rolls', 'resources', 'dm_notes', 'state_rationale']:
            if field in data['debug_info']:
                print(f'  ✓ {field}: {type(data[\"debug_info\"][field]).__name__}')
            else:
                print(f'  ✗ {field}: not found')
except Exception as e:
    print(f'Error analyzing response: {e}')
"

# Cleanup
echo
echo "Cleaning up..."
kill $SERVER_PID 2>/dev/null

echo "Test complete!"