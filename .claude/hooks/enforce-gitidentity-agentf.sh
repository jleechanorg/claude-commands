#!/usr/bin/env bash
# enforce-gitidentity-agentf.sh — PreToolUse(Bash) guard.
# Blocks `git commit` whose target repo is under $HOME/agent-f OR has
# an Agnt-F origin remote, unless the author is $USER-af. Backstop for the
# ~/.gitconfig includeIf (which misses /tmp worktrees and repos with a stale
# local user.* override). Non-commit commands pass through untouched.
set -uo pipefail

input="$(cat 2>/dev/null || true)"
[ -z "$input" ] && exit 0
# Fast bail: only care about commits.
case "$input" in *commit*) : ;; *) exit 0 ;; esac

read_field() {
  printf '%s' "$input" | python3 -c "import json,sys
try: d=json.load(sys.stdin)
except Exception: print(''); sys.exit(0)
print(d.get('cwd','') if '$1'=='cwd' else d.get('tool_input',{}).get('command',''))" 2>/dev/null || true
}
cmd="$(read_field command)"; cwd="$(read_field cwd)"
[ -z "$cmd" ] && exit 0
printf '%s' "$cmd" | grep -qE '\bgit\b([^;&|]*)\bcommit\b' || exit 0

# Resolve the repo from cwd (covers the common `cd repo && git commit` case).
top=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || echo "")
origin=$(git -C "$cwd" config --get remote.origin.url 2>/dev/null || echo "")
case "$cwd|$top|$origin" in
  *"$HOME/agent-f/"*|*[Aa]gnt-[Ff]/*) : ;;
  *) exit 0 ;;
esac

name=$(git -C "$cwd" config user.name 2>/dev/null || echo "")
email=$(git -C "$cwd" config user.email 2>/dev/null || echo "")
if [ "$name" = "$USER-af" ] && {
     [ "$email" = "288516065+$USER-af@users.noreply.github.com" ] ||
     [ "$email" = "jeffrey@agent-f.com" ]; }; then
  exit 0
fi
{
  echo "BLOCKED by enforce-gitidentity-agentf: agent-f commits must be authored $USER-af."
  echo "Repo: ${top:-$cwd}   Got: $name <$email>"
  echo "Fix: git -C \"${top:-$cwd}\" config user.name $USER-af \\"
  echo "      && git -C \"${top:-$cwd}\" config user.email 288516065+$USER-af@users.noreply.github.com"
} >&2
exit 2
