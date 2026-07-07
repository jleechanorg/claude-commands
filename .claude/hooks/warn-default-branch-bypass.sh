#!/usr/bin/env bash
# warn-default-branch-bypass.sh
#
# PreToolUse hook for `Bash` tool. Warns (does NOT block) when the model
# is about to push to or merge into a default branch (main/master) on
# $GITHUB_REPOSITORY without first showing a 7-green verdict.
#
# The user has final authority — this hook exists to surface the bypass,
# not prevent it. The session Stop hook checks the goal condition; this
# PreToolUse hook checks the action surface for known-bad defaults.
#
# Install (per ~/.claude/skills/harness-fix-durability):
#   Add to ~/.claude/settings.json under "hooks.PreToolUse" matcher "Bash":
#   [
#     {
#       "matcher": "Bash",
#       "hooks": [
#         { "type": "command", "command": "$HOME/.claude/hooks/warn-default-branch-bypass.sh" }
#       ]
#     }
#   ]

set -euo pipefail

# Read the tool input from stdin (JSON: {"tool_name": "Bash", "tool_input": {"command": "..."}})
input=$(cat)

# Extract the command string
command=$(printf '%s' "$input" | python3 -c "import sys, json; d=json.loads(sys.stdin.read()); print(d.get('tool_input', {}).get('command', ''))" 2>/dev/null || echo "")

# Only inspect if it's a git push or gh merge command
if ! printf '%s' "$command" | grep -qE "(git push.*(origin|upstream)\s+(main|master)|gh pr merge.*--(merge|squash|rebase)|git push\s+.*HEAD:refs/heads/(main|master))"; then
  exit 0
fi

# Match found — emit a JSON warning to stderr (PreToolUse hook convention:
# exit 0 always; warnings go to stderr and surface in the transcript).
cat >&2 <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Potential default-branch push/merge detected (heuristic — the hook only pattern-matches the command string, not PR metadata, so non-default-branch merges can match). This command may bypass Green Gate and/or Skeptic. Confirm explicitly with the user via literal 'MERGE APPROVED' or 'merge approved' phrase before executing — or 'NOPE' to abort."
  }
}
JSON

exit 0