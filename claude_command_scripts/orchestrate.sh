#!/bin/bash
# /orchestrate command - Multi-agent orchestration system
# Usage: /orchestrate [task_description] or ./orchestrate.sh [task_description]
# Works from any directory within a git repository or worktree

set -euo pipefail

# Find the git directory (works in worktrees and submodules)
git rev-parse --git-dir >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[Not in a git repository]"
    exit 1
fi

# Get the root of the working tree
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Unable to find git root]"
    exit 1
fi

# Find the commands directory (similar to git-header.sh pattern)
commands_dir=""
if [ -d "$git_root/.claude/commands" ]; then
    commands_dir="$git_root/.claude/commands"
elif [ -d "$git_root/worktree_roadmap/.claude/commands" ]; then
    commands_dir="$git_root/worktree_roadmap/.claude/commands"
else
    # Search for the commands directory in any subdirectory
    found_commands=$(find "$git_root" -name "commands" -type d -path "*/.claude/*" 2>/dev/null | head -1)
    if [ -n "$found_commands" ]; then
        commands_dir="$found_commands"
    else
        echo "[Commands directory not found]"
        exit 1
    fi
fi

# Execute the Python orchestration script
python3 "$commands_dir/orchestrate.py" "$@"