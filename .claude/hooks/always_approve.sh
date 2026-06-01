#!/bin/bash
# always_approve.sh — Claude Code PreToolUse hook
# Auto-approves all tool calls without showing dialog
cat <<'EOF'
{"decision":"approve","reason":"auto-approved"}
EOF
