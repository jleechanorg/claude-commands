#!/usr/bin/env bash
# pre-commit-git-identity.sh
# Directory-aware git author identity check.
#   - repos under $HOME/agent-f  OR  with an Agnt-F origin remote
#       → expect $USER-af (so contributions land on github.com/$USER-af)
#   - everything else → expect jleechan2015
# Identity is set automatically by an includeIf in ~/.gitconfig
# (gitdir:$HOME/agent-f/ → ~/.gitconfig-agentf). This hook only
# verifies it. If it exits non-zero, the commit is blocked.

set -e

toplevel=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
origin=$(git config --get remote.origin.url 2>/dev/null || echo "")

actual_name=$(git config --get user.name 2>/dev/null || echo "")
actual_email=$(git config --get user.email 2>/dev/null || echo "")

case "$toplevel|$origin" in
  $HOME/agent-f/*|*[Aa]gnt-[Ff]/*)
    # Agent-F enterprise identity. Accept the privacy noreply or the real email.
    if [[ "$actual_name" == "$USER-af" ]] && {
         [[ "$actual_email" == "288516065+$USER-af@users.noreply.github.com" ]] ||
         [[ "$actual_email" == "jeffrey@agent-f.com" ]]; }; then
      exit 0
    fi
    {
      echo "=== Git Identity Mismatch (agent-f work) ==="
      echo "Expected: $USER-af <288516065+$USER-af@users.noreply.github.com>"
      echo "          (or jeffrey@agent-f.com)"
      echo "Actual:   $actual_name <$actual_email>"
      echo "Fix: should be automatic via includeIf in ~/.gitconfig."
      echo "     If a local override exists: git config --local --unset user.name; git config --local --unset user.email"
    } >&2
    exit 1
    ;;
  *)
    expected_name="jleechan2015"
    expected_email="jleechan2015@users.noreply.github.com"
    if [[ "$actual_name" != "$expected_name" ]] || [[ "$actual_email" != "$expected_email" ]]; then
      {
        echo "=== Git Identity Mismatch ==="
        echo "Expected: $expected_name <$expected_email>"
        echo "Actual:   $actual_name <$actual_email>"
        echo "Fix: git config --local user.name \"$expected_name\" && git config --local user.email \"$expected_email\""
      } >&2
      exit 1
    fi
    ;;
esac
