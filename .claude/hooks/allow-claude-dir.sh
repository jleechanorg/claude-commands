#!/usr/bin/env bash
# Auto-approve PermissionRequest events for configured directories only.
# Workaround for anthropics/claude-code#35718 / #37253:
# "protected directory" check fires even with dangerouslySkipPermissions=true.
#
# Allowlists ~ under-~ paths. All other permission requests are denied (fail-closed).
# Logs decision reason to stderr for diagnostics.

set -euo pipefail

INPUT=$(cat)

# Extract the requested path using multiple common field names
REQUESTED_PATH=$(echo "$INPUT" | jq -r '[
  .input.requestedDirectory,
  .input.requestedPath,
  .input.path,
  .requestedDirectory,
  .requestedPath,
  .path
] | map(select(. != null and . != "")) | .[0] // ""' 2>/dev/null)

if [[ -z "$REQUESTED_PATH" ]]; then
  # Could not extract path — fail closed for safety
  echo "allow-claude-dir: deny (could not extract path)" >&2
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"deny","permissionDecisionReason":"allow-claude-dir: unknown path"}}'
  exit 0
fi

# Resolve to absolute path for comparison
ABS_PATH=$(realpath "$REQUESTED_PATH" 2>/dev/null || echo "$REQUESTED_PATH")

# Allowlist: home dir subdirs and git worktrees under /Users
ALLOWED=false
if [[ "$ABS_PATH" == "$HOME/"* || "$ABS_PATH" == "$HOME" ]]; then
  ALLOWED=true
elif [[ "$ABS_PATH" == /Users/*/worktrees/* ]]; then
  ALLOWED=true
fi

if [[ "$ALLOWED" == true ]]; then
  echo "allow-claude-dir: allow $ABS_PATH" >&2
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"allow","permissionDecisionReason":"allow-claude-dir: in allowlist"}}'
else
  echo "allow-claude-dir: deny $ABS_PATH (not in allowlist)" >&2
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"deny","permissionDecisionReason":"allow-claude-dir: not in allowlist"}}'
fi
