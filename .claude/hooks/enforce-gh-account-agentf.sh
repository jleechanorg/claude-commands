#!/usr/bin/env bash
# enforce-gh-account-agentf.sh — PreToolUse(Bash) guard.
# Makes the active `gh` account deterministic per scope:
#   - gh command whose cwd is under $HOME/agent-f, OR that references
#     the Agnt-F org → ensure active account = $USER-af
#   - any other gh command → ensure active account = jleechan2015
# Auto-switches (gh auth switch writes hosts.yml, which the about-to-run gh
# command then reads). Non-gh commands pass through untouched.
set -uo pipefail

input="$(cat 2>/dev/null || true)"
[ -z "$input" ] && exit 0
# Fast bail: only care about gh invocations.
case "$input" in *gh*) : ;; *) exit 0 ;; esac

read_field() {
  printf '%s' "$input" | python3 -c "import json,sys
try: d=json.load(sys.stdin)
except Exception: print(''); sys.exit(0)
print(d.get('cwd','') if '$1'=='cwd' else d.get('tool_input',{}).get('command',''))" 2>/dev/null || true
}
cmd="$(read_field command)"; cwd="$(read_field cwd)"
# If JSON didn't include cwd, fall back to shell PWD, then CLAUDE_CONFIG_DIR hint.
[ -z "$cwd" ] && cwd="${PWD:-}"
[ -z "$cmd" ] && exit 0
# Must actually invoke the gh CLI at a command position.
printf '%s' "$cmd" | grep -qE '(^|[;&|`]|[[:space:]]|env[[:space:]]+)gh([[:space:]]|$)' || exit 0

# CLAUDE_CONFIG_DIR=~/.claude-agent-f is set by claudeaf() — reliable agent-f indicator.
agentf_config="${CLAUDE_CONFIG_DIR:-}"
case "$agentf_config $cwd $cmd" in
  *"claude-agent-f"*|*"$HOME/agent-f"*|*[Aa]gnt-[Ff]*) target="$USER-af" ;;
  *) target="jleechan2015" ;;
esac

# Fast read of the active account from hosts.yml (avoids a network call).
active=$(awk '/^github\.com:/{g=1;next} g&&/^[^[:space:]]/{g=0} g&&/^[[:space:]]+user:/{print $2; exit}' ~/.config/gh/hosts.yml 2>/dev/null)
[ "$active" = "$target" ] && exit 0

if gh auth switch --user "$target" >/dev/null 2>&1; then
  exit 0
fi
echo "BLOCKED by enforce-gh-account-agentf: gh active account should be '$target' for this command, and auto-switch failed." >&2
echo "Run: gh auth switch --user $target" >&2
exit 2
