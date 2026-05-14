#!/bin/bash
# always_approve.sh — Claude Code PreToolUse hook
# Auto-approves all tool calls without showing dialog
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"auto-approved"}}
EOF
