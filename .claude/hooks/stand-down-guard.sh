#!/bin/bash
# stand-down-guard.sh — PreToolUse hook to enforce stand-down orders
# Blocks git push/commit/checkout/gh pr actions targeting a restricted branch/PR/path.

TARGETS_FILE="${STAND_DOWN_FILE:-/tmp/claude_stand_down_targets.json}"

# Read stdin (hook input JSON)
INPUT=$(cat 2>/dev/null || true)
if [ -z "$INPUT" ]; then
  exit 0
fi

# Fast check: if targets file doesn't exist, allow immediately
if [ ! -f "$TARGETS_FILE" ]; then
  exit 0
fi

RESULT=$(HOOK_INPUT="$INPUT" python3 - "$TARGETS_FILE" <<'PYEOF'
import sys, json, re, os, subprocess

targets_file = sys.argv[1]

try:
    with open(targets_file) as f:
        data = json.load(f)
    targets = data.get("targets", {})
except Exception:
    targets = {}

if not targets:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

try:
    hook_input = json.loads(os.environ.get("HOOK_INPUT", "{}"))
except Exception:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

tool_name = hook_input.get("tool_name", "")
tool_input = hook_input.get("tool_input", {})

# Extract command string for Bash tool
command = ""
if tool_name == "Bash":
    command = tool_input.get("command", "")
elif "command" in tool_input:
    command = tool_input.get("command", "")

if not command:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

# Operations subject to stand-down checks
write_ops = ["push", "commit", "checkout", "merge", "rebase", "pr edit", "pr close", "pr merge"]
is_relevant = any(op in command.lower() for op in write_ops)
if not is_relevant:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

# Determine current git branch
current_branch = ""
try:
    current_branch = subprocess.check_output(
        ["git", "branch", "--show-current"], stderr=subprocess.DEVNULL, text=True
    ).strip()
except Exception:
    pass

for target_key, info in targets.items():
    reason = info.get("reason", "Operator stand-down order")
    target = info.get("target", target_key).strip()

    # Clean target representations (e.g. #123 -> 123 for PR numbers)
    target_clean = target.lstrip("#")

    # Match Rule 1: Target matches current branch AND command is commit/push/merge
    if current_branch and (current_branch == target or current_branch.endswith(f"/{target}")):
        if any(op in command for op in ["commit", "push", "merge", "rebase"]):
            msg = (
                f"STAND-DOWN ENFORCEMENT BLOCKED: Current branch '{current_branch}' is under active stand-down order '{target}'. "
                f"Reason: {reason}. Run 'set-stand-down.sh remove {target}' if authorized by operator."
            )
            print(json.dumps({"decision": "block", "reason": msg}))
            sys.exit(0)

    # Match Rule 2: Command explicitly references target as a token or substring
    # Check for branch name in git push/checkout/rebase/merge or gh pr commands
    patterns = [
        r'\b' + re.escape(target) + r'\b',
        r'\b' + re.escape(target_clean) + r'\b',
    ]

    for pat in patterns:
        if re.search(pat, command):
            msg = (
                f"STAND-DOWN ENFORCEMENT BLOCKED: Command touches stand-down target '{target}'. "
                f"Reason: {reason}. Run 'set-stand-down.sh remove {target}' if authorized by operator."
            )
            print(json.dumps({"decision": "block", "reason": msg}))
            sys.exit(0)

print(json.dumps({"decision": "allow"}))
PYEOF
)

# Output decision and exit code
DECISION=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('decision','allow'))" 2>/dev/null || echo "allow")

if [ "$DECISION" = "block" ]; then
  echo "$RESULT"
  exit 2
fi

echo "$RESULT"
exit 0
