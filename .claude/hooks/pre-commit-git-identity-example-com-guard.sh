#!/usr/bin/env bash
# pre-commit-git-identity-example-com-guard.sh
#
# Reject commits where the author or committer email is a placeholder
# (RFC 2606 reserved domain). The @example.com pattern was used by
# misconfigured LLM agents in 3 leak commits (3aac8fe8, 45836c8, etc.)
# and is a strong signal of an unsafe commit identity.
#
# Install per-repo via:
#   git config core.hooksPath $HOME/.claude/hooks
#   git config core.hooksPath .githooks   # if a per-repo chain is preferred
#
# Or chain from a per-repo .githooks/pre-commit that calls this script.
set -euo pipefail

# Read the author + committer of the commit being created.
# `git var GIT_AUTHOR_EMAIL` is empty in pre-commit (no commit yet) — derive
# from the same config sources git commit itself uses: env vars first, then
# repo/local config, then global config.
read_email() {
  local var_name="$1"
  local val
  # 1. env override (GIT_AUTHOR_EMAIL / GIT_COMMITTER_EMAIL)
  if [[ -n "${!var_name:-}" ]]; then
    printf '%s' "${!var_name}"
    return 0
  fi
  # 2. repo + local config for user.email
  val="$(git config --get user.email 2>/dev/null || true)"
  if [[ -n "$val" ]]; then
    printf '%s' "$val"
    return 0
  fi
  # 3. fall back to git var (may be empty)
  git var "$var_name" 2>/dev/null || true
}

AUTHOR_EMAIL="$(read_email GIT_AUTHOR_EMAIL)"
COMMITTER_EMAIL="$(read_email GIT_COMMITTER_EMAIL)"

PLACEHOLDER_REGEX='@example\.com$'

blocked=0
if [[ "$AUTHOR_EMAIL" =~ $PLACEHOLDER_REGEX ]]; then
  echo "❌ Commit blocked: author email '$AUTHOR_EMAIL' is a placeholder (RFC 2606 reserved)."
  echo "   This pattern produced 3 real production leaks (commits 3aac8fe8, 45836c8, others)."
  echo "   Fix with: git config --local user.email 'jleechan2015@users.noreply.github.com'"
  blocked=1
fi
if [[ "$COMMITTER_EMAIL" =~ $PLACEHOLDER_REGEX ]]; then
  echo "❌ Commit blocked: committer email '$COMMITTER_EMAIL' is a placeholder (RFC 2606 reserved)."
  echo "   Fix with: git config --local user.email 'jleechan2015@users.noreply.github.com'"
  blocked=1
fi

if [[ "$blocked" -eq 1 ]]; then
  echo ""
  echo "If you really need to commit with a placeholder email (e.g. ephemeral sandbox),"
  echo "set HERMES_SKIP_EXAMPLE_COM_GUARD=1 in the commit environment."
  exit 1
fi

exit 0
