#!/usr/bin/env bash
# Codex Pre-Execution Hook - Safety checks before running commands
# This hook validates potentially dangerous operations
# Usage: Run before executing shell commands

# Parse arguments
COMMAND="$1"
DESCRIPTION="${2:-unknown}"

if [ -z "$COMMAND" ]; then
    echo "Usage: $0 <command> [description]"
    exit 0
fi

# Dangerous patterns (regex, used with grep -Eq to avoid false positives)
# NOTE: This check runs BEFORE git-root detection so it applies outside git repos too.
DANGEROUS_PATTERNS=(
    "rm -rf / *$"
    "rm -rf /\*"
    "rm -rf \*"
    "dd if="
    ":\(\)\{ :\|:& \};:"
    "chmod -R 777"
    "chown -R"
    "mkfs"
)

# Check for dangerous commands
dangerous_matches=()
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if printf '%s' "$COMMAND" | grep -Eq -- "$pattern"; then
        dangerous_matches+=("$pattern")
    fi
done

if [ "${#dangerous_matches[@]}" -gt 0 ]; then
    for match in "${dangerous_matches[@]}"; do
        echo "⚠️  WARNING: Potentially dangerous command detected: $match"
    done
    echo "   Command: $COMMAND"
    echo "   Description: $DESCRIPTION"
    if [ "${CODEX_PRE_EXEC_ALLOW_DANGEROUS:-0}" = "1" ]; then
        echo "   Override active via CODEX_PRE_EXEC_ALLOW_DANGEROUS=1, continuing."
    else
        echo "❌ BLOCKED: refusing to execute dangerous command." >&2
        echo "   Set CODEX_PRE_EXEC_ALLOW_DANGEROUS=1 to bypass intentionally." >&2
        exit 2
    fi
fi

# Get git root (for git-specific checks only)
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$git_root" ]; then
    exit 0
fi
cd "$git_root" 2>/dev/null || exit 0

# Check if command modifies git history
if echo "$COMMAND" | grep -qE "(git reset|git rebase|git push --force)"; then
    echo "⚠️  NOTE: This command modifies git history"
fi

# Check for uncommitted important changes
if [ -d ".git" ]; then
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo "ℹ️  You have uncommitted changes"
    fi
fi

exit 0
