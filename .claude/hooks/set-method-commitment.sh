#!/bin/bash
# set-method-commitment.sh — Helper to manage method commitment state
# Usage:
#   set-method-commitment.sh set <method> "<user_said>"
#   set-method-commitment.sh clear
#   set-method-commitment.sh approve-fallback
#   set-method-commitment.sh status

COMMITMENT_FILE="/tmp/claude_method_commitment.json"

case "${1:-}" in
  set)
    METHOD="${2:?Usage: set-method-commitment.sh set <method> \"<user_said>\"}"
    USER_SAID="${3:?Usage: set-method-commitment.sh set <method> \"<user_said>\"}"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    python3 -c "
import json, sys
data = {
    'method': sys.argv[1],
    'user_said': sys.argv[2],
    'timestamp': sys.argv[3],
    'fallback_approved': False
}
with open(sys.argv[4], 'w') as f:
    json.dump(data, f, indent=2)
print(f'Commitment set: method={sys.argv[1]}, user_said=\"{sys.argv[2]}\"')
" "$METHOD" "$USER_SAID" "$TIMESTAMP" "$COMMITMENT_FILE"
    ;;

  clear)
    if [ -f "$COMMITMENT_FILE" ]; then
      rm "$COMMITMENT_FILE"
      echo "Commitment cleared."
    else
      echo "No active commitment."
    fi
    ;;

  approve-fallback)
    if [ ! -f "$COMMITMENT_FILE" ]; then
      echo "No active commitment to approve fallback for."
      exit 1
    fi
    python3 -c "
import json
with open('$COMMITMENT_FILE') as f:
    data = json.load(f)
data['fallback_approved'] = True
with open('$COMMITMENT_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print(f'Fallback approved for method: {data[\"method\"]}')
"
    ;;

  status)
    if [ ! -f "$COMMITMENT_FILE" ]; then
      echo "none"
    else
      python3 -c "
import json
with open('$COMMITMENT_FILE') as f:
    data = json.load(f)
method = data.get('method', '?')
user_said = data.get('user_said', '?')
fallback = data.get('fallback_approved', False)
ts = data.get('timestamp', '?')
print(f'Active commitment:')
print(f'  method: {method}')
print(f'  user_said: \"{user_said}\"')
print(f'  fallback_approved: {fallback}')
print(f'  timestamp: {ts}')
"
    fi
    ;;

  *)
    echo "Usage: set-method-commitment.sh {set|clear|approve-fallback|status}"
    echo ""
    echo "Commands:"
    echo "  set <method> \"<user_said>\"  — Set a method commitment"
    echo "  clear                        — Remove active commitment"
    echo "  approve-fallback             — Allow fallback methods"
    echo "  status                       — Show current commitment"
    exit 1
    ;;
esac
