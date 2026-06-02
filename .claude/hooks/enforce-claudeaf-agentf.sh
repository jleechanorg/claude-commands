#!/usr/bin/env bash
# enforce-claudeaf-agentf.sh — PreToolUse(Bash) guard.
#
# Invariant: any Claude CLI spawned while working under $HOME/agent-f
# MUST use the Agent-F enterprise account, i.e. CLAUDE_CONFIG_DIR=~/.claude-agent-f
# (the `claudeaf`/`claudeafc` shell functions). A bare `claude` / `clauded*`
# spawn in that scope is blocked (exit 2) so the model retries with claudeaf.
#
# Scope is intentionally narrow to avoid false positives:
#   - fires only when the cwd OR the command text references the agent-f root
#   - fires only when the command actually invokes the claude CLI at a command
#     position (not when "claude" merely appears inside a path like ~/.claude/)
#   - allows the call when it carries CLAUDE_CONFIG_DIR=...claude-agent-f, or
#     uses the claudeaf/claudeafc functions.
#
# Non-blocking by design for everything else: git, gh, python, npm, the
# `python -m runner` factory launch, etc. all pass through untouched.
set -uo pipefail

AGENTF_ROOT="$HOME/agent-f"

input="$(cat 2>/dev/null || true)"
[ -z "$input" ] && exit 0

read_field() {
  printf '%s' "$input" | python3 -c "import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    print(''); sys.exit(0)
print(d.get('$1','') if '$1'=='cwd' else d.get('tool_input',{}).get('command',''))" 2>/dev/null || true
}

cmd="$(read_field command)"
cwd="$(read_field cwd)"
[ -z "$cmd" ] && exit 0

# Scope gate: only agent-f work.
case "$cwd $cmd" in
  *"$AGENTF_ROOT"*) : ;;
  *) exit 0 ;;
esac

# Detect a Claude CLI spawn at a command position. 'claudeaf'/'claudeafc' do NOT
# match here because a letter (a) follows 'claude' instead of whitespace/end.
if printf '%s' "$cmd" | grep -qE '(^|[;&|`]|[[:space:]]|env[[:space:]]+)(claude|clauded|claudedanger|claudedo|claudedc|claudet)([[:space:]]|$)'; then
  # Allowed iff it carries the agent-f config dir or uses claudeaf/claudeafc.
  if printf '%s' "$cmd" | grep -qE 'CLAUDE_CONFIG_DIR=[^[:space:]]*\.claude-agent-f' \
     || printf '%s' "$cmd" | grep -qE '(^|[;&|`]|[[:space:]])claudeaf[c]?([[:space:]]|$)'; then
    exit 0
  fi
  {
    echo "BLOCKED by enforce-claudeaf-agentf: agent-f work must use the Agent-F enterprise account."
    echo "This command operates under $AGENTF_ROOT but spawns a bare 'claude'."
    echo "Fix one of:"
    echo "  • use the claudeaf function:   claudeaf <args>"
    echo "  • or prefix the config dir:    CLAUDE_CONFIG_DIR=~/.claude-agent-f claude <args>"
  } >&2
  exit 2
fi

exit 0
