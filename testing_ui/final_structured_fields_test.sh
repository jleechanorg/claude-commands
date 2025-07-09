#!/bin/bash
# Clean test for structured fields - shows only the essential output

echo "=== Structured Fields Implementation Test ==="
echo

# Start server quietly
TESTING=true PORT=8093 python mvp_site/main.py serve >/dev/null 2>&1 &
SERVER_PID=$!

# Wait for server
sleep 5

# Create campaign
CAMPAIGN_RESPONSE=$(curl -s -X POST http://localhost:8093/api/campaigns \
  -H "Content-Type: application/json" \
  -H "X-Test-Bypass-Auth: true" \
  -H "X-Test-User-Id: test-user-123" \
  -d '{
    "title": "Test Campaign",
    "prompt": "A test campaign",
    "campaign_type": "custom"
  }')

CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('campaign_id', 'ERROR'))")

if [ "$CAMPAIGN_ID" = "ERROR" ]; then
    echo "Failed to create campaign"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo "✓ Created campaign: $CAMPAIGN_ID"

# Test interaction
INTERACTION_RESPONSE=$(curl -s -X POST http://localhost:8093/api/campaigns/$CAMPAIGN_ID/interaction \
  -H "Content-Type: application/json" \
  -H "X-Test-Bypass-Auth: true" \
  -H "X-Test-User-Id: test-user-123" \
  -d '{
    "input": "I attack the goblin with my sword! Roll for damage.",
    "mode": "character",
    "debug_mode": true
  }')

echo
echo "=== STRUCTURED FIELDS ANALYSIS ==="

# Analyze the response
echo "$INTERACTION_RESPONSE" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    print('\\n1. RESPONSE STRUCTURE:')
    print(f'   Top-level keys: {sorted(data.keys())}')
    
    print('\\n2. STRUCTURED FIELDS AT TOP LEVEL:')
    fields = ['dice_rolls', 'resources', 'planning_block', 'session_header']
    for field in fields:
        if field in data:
            val = data[field]
            if isinstance(val, list):
                print(f'   ✓ {field}: list with {len(val)} items')
            elif isinstance(val, str):
                print(f'   ✓ {field}: \"{val[:50]}...\" (length: {len(val)})')
            else:
                print(f'   ✓ {field}: {type(val).__name__}')
        else:
            print(f'   ✗ {field}: NOT FOUND')
    
    print('\\n3. DEBUG_INFO STRUCTURE:')
    if 'debug_info' in data:
        debug = data['debug_info']
        print(f'   ✓ debug_info found with keys: {list(debug.keys())}')
        
        # Check nested fields
        print('\\n4. NESTED FIELDS IN DEBUG_INFO:')
        for field in ['dice_rolls', 'resources', 'dm_notes', 'state_rationale']:
            if field in debug:
                val = debug[field]
                if isinstance(val, list) and val:
                    print(f'   ✓ {field}: list with {len(val)} items')
                    print(f'      Example: {val[0][:100]}...')
                elif isinstance(val, str) and val:
                    print(f'   ✓ {field}: \"{val[:50]}...\"')
                elif val:
                    print(f'   ✓ {field}: {type(val).__name__}')
                else:
                    print(f'   ⚠️  {field}: empty')
            else:
                print(f'   ✗ {field}: NOT FOUND in debug_info')
    else:
        print('   ✗ debug_info NOT FOUND at top level')
    
    print('\\n5. SUMMARY:')
    # Check for duplication
    dice_top = 'dice_rolls' in data
    dice_debug = 'debug_info' in data and 'dice_rolls' in data.get('debug_info', {})
    
    if dice_top and dice_debug:
        print('   ⚠️  ISSUE: dice_rolls appears in BOTH locations (duplication)')
    elif dice_top and not dice_debug:
        print('   ⚠️  ISSUE: dice_rolls ONLY at top level (should be in debug_info)')
    elif not dice_top and dice_debug:
        print('   ✓ CORRECT: dice_rolls only in debug_info')
    else:
        print('   ✗ ERROR: dice_rolls not found anywhere')
        
    # Check frontend expectation vs backend reality
    print('\\n6. FRONTEND COMPATIBILITY:')
    print('   Frontend expects at top level: dice_rolls, resources')
    print('   Backend provides at top level:', end='')
    if dice_top:
        print(' dice_rolls', end='')
    if 'resources' in data:
        print(' resources', end='')
    print()
    print('   Result: Frontend', end='')
    if dice_top:
        print(' WILL', end='')
    else:
        print(' WILL NOT', end='')
    print(' display dice_rolls correctly')
    
except Exception as e:
    print(f'Error analyzing response: {e}')
    print('Raw response:', sys.stdin.read()[:500])
"

# Cleanup
kill $SERVER_PID 2>/dev/null
echo
echo "Test complete!"