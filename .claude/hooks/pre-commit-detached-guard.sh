#!/usr/bin/env bash
# Pre-commit detached HEAD guard
#
# Blocks "git commit" Bash tool calls when the current repo is in detached HEAD.
# AO workers (simplify, rebase, spawn) check out "origin/main" directly, leaving
# main clones in detached HEAD. Committing there creates orphaned commits.
#
# Wired as a PreToolUse:Bash hook in ~/.claude/settings.json.

set -euo pipefail

# Read tool input from stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.name // ""' 2>/dev/null)

# Only intercept Bash tool
[[ "$TOOL_NAME" != "Bash" ]] && { echo "$INPUT"; exit 0; }

COMMAND=$(echo "$INPUT" | jq -r '.input.command // ""' 2>/dev/null)

# Only act on git commit commands (not git commit --amend --no-edit in loops, etc.)
# Match: git commit, git -C <path> commit
if ! echo "$COMMAND" | grep -qE '(^|;|&&|\|\|)[[:space:]]*(git[[:space:]]+(-[A-Za-z][[:space:]]+\S+[[:space:]]+)*commit)[[:space:]]'; then
  echo "$INPUT"
  exit 0
fi

# Check if we are in a git repo and in detached HEAD
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "$INPUT"
  exit 0
fi

BRANCH=$(git branch --show-current 2>/dev/null || echo "")

if [[ -z "$BRANCH" ]]; then
  REPO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")
  HEAD_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "?")
  echo "============================================" >&2
  echo "BLOCKED: Committing on detached HEAD in $REPO" >&2
  echo "" >&2
  echo "HEAD is at $HEAD_SHA (not on any branch)." >&2
  echo "AO workers sometimes check out origin/main directly, leaving" >&2
  echo "the main clone in detached HEAD. Committing here orphans the commit." >&2
  echo "" >&2
  echo "Fix first:" >&2
  echo "  git checkout main        # if main branch exists" >&2
  echo "  git checkout -b <branch> # to create a new branch from current HEAD" >&2
  echo "============================================" >&2
  exit 1
fi

echo "$INPUT"
