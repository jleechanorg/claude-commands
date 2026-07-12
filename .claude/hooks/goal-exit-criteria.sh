#!/usr/bin/env bash
# UserPromptSubmit hook: when the user types the builtin `/goal <condition>`,
# inject a standing instruction to harden the condition into ironclad,
# verifiable exit criteria before working. Fires only on the exact /goal
# command prefix (mechanical command dispatch, not intent detection); the
# criteria brainstorming itself is delegated to the model (ZFC-compliant).
# No-ops on `/goal` (bare), `/goal clear`, `/goal active`, and all other prompts.
set -euo pipefail

input=$(cat)
prompt=$(printf '%s' "$input" | jq -r '.prompt // empty' 2>/dev/null) || exit 0

case "$prompt" in
  "/goal "*) ;;
  *) exit 0 ;;
esac

args="${prompt#/goal }"
case "$args" in
  clear|active|clear\ *|active\ *|"") exit 0 ;;
esac

ctx="The user set a goal via the builtin /goal command. Condition as typed: \"${args}\".
The user has a standing instruction for every /goal invocation:
1. Before any other work, brainstorm 3-7 ironclad exit criteria that are STRONGER and more verifiable than the literal condition: observable end-states, machine-checkable wherever possible, the evidence class each requires (test output, CI conclusion, screenshot, log line), and at least one negative criterion (what must NOT break).
2. State the hardened criteria briefly at the start of the reply, then immediately begin working toward them without waiting for confirmation.
3. The literal condition is the floor, not the ceiling: when evaluating whether the goal / stop condition is met, treat it as met ONLY when every hardened criterion is verified with concrete evidence."

jq -n --arg ctx "$ctx" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: $ctx
  }
}'
