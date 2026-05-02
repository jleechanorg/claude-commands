#!/usr/bin/env bash
# Block unauthorized merges in your-project.com
#
# PreToolUse:Bash hook that prevents any agent from executing merge commands
# (gh pr merge, gh api .../merge, git merge into main) in the your-project.com
# repository without explicit human "MERGE APPROVED" in the conversation.
#
# This hook exists because:
# - PR #6161: merged without human approval (memory: feedback_no_unauthorized_merge.md)
# - PR #6240: polish agent auto-merged despite CLAUDE.md prohibition and SKEPTIC_CRON_AUTO_MERGE=false
# - Instructions alone are insufficient for commitment integrity violations (harness durability table)
#
# Wired as a PreToolUse:Bash hook in ~/.claude/settings.json.
# Only active when cwd is inside a your-project.com worktree/clone.

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.name // ""' 2>/dev/null)

[[ "$TOOL_NAME" != "Bash" ]] && { echo "$INPUT"; exit 0; }

COMMAND=$(echo "$INPUT" | jq -r '.input.command // ""' 2>/dev/null)

# Only guard your-project.com repos
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [[ -z "$REPO_ROOT" ]]; then
  echo "$INPUT"
  exit 0
fi

# Check if this is a your-project.com repo (by remote URL or directory name)
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
IS_WORLDARCHITECT=false
if echo "$REMOTE_URL" | grep -qi "worldarchitect"; then
  IS_WORLDARCHITECT=true
elif basename "$REPO_ROOT" | grep -qi "worldarchitect"; then
  IS_WORLDARCHITECT=true
elif basename "$(dirname "$REPO_ROOT")" | grep -qi "worktree_worker" && git remote get-url origin 2>/dev/null | grep -qi "worldarchitect"; then
  IS_WORLDARCHITECT=true
fi

if [[ "$IS_WORLDARCHITECT" != "true" ]]; then
  echo "$INPUT"
  exit 0
fi

# Detect merge commands:
# 1. gh pr merge (with any flags)
# 2. gh api repos/.../pulls/.../merge (REST merge endpoint)
# 3. git push to main (direct merge bypass)
MERGE_PATTERN='gh[[:space:]]+pr[[:space:]]+merge|gh[[:space:]]+api[[:space:]]+.*pulls/[0-9]+/merge|gh[[:space:]]+api[[:space:]]+.*merge.*--method[[:space:]]+(PUT|POST)'

if echo "$COMMAND" | grep -qEi "$MERGE_PATTERN"; then
  # Check for explicit override env var (for skeptic-cron CI only, not agents)
  if [[ "${AO_ALLOW_GH_PR_MERGE:-}" == "1" ]] && [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    echo "$INPUT"
    exit 0
  fi

  echo "============================================" >&2
  echo "BLOCKED: Merge command in your-project.com" >&2
  echo "" >&2
  echo "Command: $COMMAND" >&2
  echo "" >&2
  echo "your-project.com requires explicit human 'MERGE APPROVED'" >&2
  echo "in the conversation before any merge. This is a hard block." >&2
  echo "" >&2
  echo "If the user has said 'MERGE APPROVED' for this specific PR," >&2
  echo "ask them to run the merge command directly via: ! gh pr merge ..." >&2
  echo "============================================" >&2
  exit 1
fi

echo "$INPUT"
