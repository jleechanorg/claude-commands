#!/usr/bin/env bash
# block-runtime-mirror-edits.sh — PreToolUse(Edit|Write) guard.
#
# Invariant: ~/.local/share/worldarchitect-runners/*.sh is a RUNTIME MIRROR
# of self-hosted-oss/*.sh. It is NOT the source of truth.
#
# Direct Edit/Write on the runtime mirror is the "I edited the wrong file"
# anti-pattern documented in:
#   - ~/.claude/projects/-Users-$USER-projects-worldarchitect-ai/memory/
#     feedback_2026-06-18_heal_runners_sigkill_session_conflict.md
#   - ~/.claude/projects/-Users-$USER-projects-worldarchitect-ai/memory/
#     feedback_2026-06-09_runner_supervisor_and_ops.md  ("Stable install path sync")
#
# Correct flow:
#   1. Edit self-hosted-oss/<script>.sh in the repo
#   2. Commit + push + open PR (infra changes need a PR, not host-only edits)
#   3. After merge, re-run bash self-hosted-oss/install.sh on every host
#      (install.sh's RUNTIME_SCRIPTS array syncs the mirror)
#
# For solo-dev local test work, the ONE acceptable shortcut is:
#   cp self-hosted-oss/<script>.sh ~/.local/share/worldarchitect-runners/<script>.sh
# via Bash (not Edit/Write), AND the same change is already committed in
# the repo with a PR open. Direct Edit on the runtime copy is NEVER OK
# because it gets clobbered on the next install.sh run AND other Macs
# never see it.
#
# Scope:
#   - Blocks Edit/Write on ~/.local/share/worldarchitect-runners/*.sh
#   - Allows Bash `cp` and `rsync` to the same path (so the explicit
#     sync shortcut still works)
#   - Allows Edit/Write on self-hosted-oss/*.sh in any worktree
#
# Exit codes:
#   0 — pass through (not a runtime-mirror edit)
#   2 — block with diagnostic

set -uo pipefail

input="$(cat 2>/dev/null || true)"
[[ -z "$input" ]] && exit 0

# Only fire on Edit and Write tools.
tool_name="$(printf '%s' "$input" | jq -r '.tool_name' 2>/dev/null || echo "")"
case "$tool_name" in
  Edit|Write|MultiEdit) : ;;
  *) exit 0 ;;
esac

file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null || echo "")"
[[ -z "$file_path" ]] && exit 0

# Match the runtime mirror path. Both expanded and literal forms are checked
# in case $HOME is unset in the hook's environment.
for mirror in \
  "$HOME/.local/share/worldarchitect-runners" \
  "$HOME/.local/share/worldarchitect-runners"; do
  if [[ "$file_path" == "$mirror"/*.sh ]] || [[ "$file_path" == "$mirror"/* ]]; then
    # Allow .jsonl and .log files in the same dir (state + logs are local-only).
    case "$file_path" in
      *.jsonl|*.log|*.bak|*.swp) exit 0 ;;
    esac
    cat <<DIAG >&2
[block-runtime-mirror-edits] ✗ Direct Edit/Write on a runtime-mirror file is not allowed.

Target: $file_path
Tool:   $tool_name

~/.local/share/worldarchitect-runners/ is a RUNTIME MIRROR populated by
self-hosted-oss/install.sh from self-hosted-oss/*.sh in the repo.
Direct edits are clobbered on the next install.sh run AND never propagate
to other Macs.

Correct flow:
  1. Edit self-hosted-oss/<script>.sh in this worktree
  2. Commit + push + open a PR (infra changes need a PR)
  3. Sync the mirror via Bash AFTER commit, not via Edit:
       cp self-hosted-oss/<script>.sh ~/.local/share/worldarchitect-runners/<script>.sh
  4. Re-run bash self-hosted-oss/install.sh on every other Mac after merge

See:
  ~/.claude/projects/-Users-$USER-projects-worldarchitect-ai/memory/
      feedback_2026-06-18_heal_runners_sigkill_session_conflict.md
      feedback_2026-06-09_runner_supervisor_and_ops.md  (§Stable install path sync)

Override: type \`RUNTIME-MIRROR EDIT APPROVED\` in chat if you really mean it
(local-only experiment, will revert before next install.sh run).
DIAG
    exit 2
  fi
done

exit 0
