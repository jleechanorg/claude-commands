#!/bin/bash
# method-commitment.sh — PreToolUse hook
# Blocks silent method substitution when user has specified a required method.
# Reads commitment from /tmp/claude_method_commitment.json.
# If a commitment is active and fallback not approved, blocks tmux+CLI spawns.

COMMITMENT_FILE="/tmp/claude_method_commitment.json"

# Read stdin (hook input JSON)
INPUT=$(cat)

# Only check Bash tool calls
TOOL=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

# No commitment file — allow everything
if [ ! -f "$COMMITMENT_FILE" ]; then
  exit 0
fi

# Parse commitment and check against the command
# Pass INPUT via environment variable to avoid stdin conflicts with heredoc
RESULT=$(HOOK_INPUT="$INPUT" python3 - "$COMMITMENT_FILE" <<'PYEOF'
import sys, json, re, os

commitment_file = sys.argv[1]

# Read hook input from environment variable
hook_input = json.loads(os.environ["HOOK_INPUT"])
command = hook_input.get("tool_input", {}).get("command", "")

if not command:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

# Read commitment file
try:
    with open(commitment_file) as f:
        commitment = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

# If fallback is approved, allow everything
if commitment.get("fallback_approved", False):
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

method = commitment.get("method", "")
user_said = commitment.get("user_said", "")

if not method:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

# Patterns that indicate silent method substitution (spawning tmux+CLI workers)
substitution_patterns = [
    r'tmux\s+new-session',
    r'tmux\s+new\s',
    r'claude\s+--dangerously-skip-permissions',
]

for pattern in substitution_patterns:
    if re.search(pattern, command):
        reason = (
            f"METHOD COMMITMENT ACTIVE: User requested '{user_said}' (method: {method}). "
            f"Cannot spawn tmux+CLI workers without explicit fallback approval. "
            f"Use /{method} skill or ask user to approve fallback."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)

print(json.dumps({"decision": "allow"}))
PYEOF
)

# If python produced a block decision, output it and exit 2
DECISION=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('decision','allow'))" 2>/dev/null)

if [ "$DECISION" = "block" ]; then
  echo "$RESULT"
  exit 2
fi

exit 0
