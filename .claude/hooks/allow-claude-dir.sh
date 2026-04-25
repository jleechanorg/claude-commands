#!/usr/bin/env bash
# Auto-approve all PermissionRequest events (config file / protected dir prompts).
# Workaround for anthropics/claude-code#35718 / #37253:
# "protected directory" check fires even with dangerouslySkipPermissions=true.
printf '%s' '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","permissionDecision":"allow","permissionDecisionReason":"Auto-approved"}}'
exit 0
