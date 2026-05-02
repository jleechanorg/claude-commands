#!/usr/bin/env bash
# Auto-approve only .claude directory PermissionRequest events.
# Workaround for anthropics/claude-code#35718 / `#37253`:
# "protected directory" check fires even with dangerouslySkipPermissions=true.
payload="$(cat)"

if grep -Eq '"hookEventName"\s*:\s*"PermissionRequest"' <<<"$payload" \
  && grep -Eq '"\(\.?\/)?\.claude(\/|\")' <<<"$payload"; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"allow","permissionDecisionReason":"Auto-approved for .claude only"}}'
else
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"deny","permissionDecisionReason":"Only .claude path is auto-approved"}}'
fi
exit 0
