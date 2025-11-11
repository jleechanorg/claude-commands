---
description: Alias for /gstatus command
type: llm-orchestration
execution_mode: immediate
allowed-tools: Bash
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps sequentially.

## 📋 REFERENCE DOCUMENTATION

# /gst - Alias for /gstatus

This is a short alias for the `/gstatus` command.

Execute /gstatus:
!`(
    set -euo pipefail

    candidates=()

    add_candidate() {
        local path="$1"
        if [ -z "$path" ]; then
            return
        fi
        for existing in "${candidates[@]+"${candidates[@]}"}"; do
            if [ "$existing" = "$path" ]; then
                return
            fi
        done
        candidates+=("$path")
    }

    run_gstatus() {
        local script="$1"
        if [ "${ARGUMENTS+x}" = 'x' ]; then
            if [ -n "$ARGUMENTS" ]; then
                python3 "$script" "$ARGUMENTS"
            else
                python3 "$script" ""
            fi
        else
            python3 "$script" ""
        fi
    }

    add_candidate "$(pwd -P)/.claude/commands/gstatus.py"

    if git_root=$(git rev-parse --show-toplevel 2>/dev/null); then
        add_candidate "$git_root/.claude/commands/gstatus.py"
    fi

    if [ -n "${CLAUDE_REPO_ROOT:-}" ]; then
        add_candidate "${CLAUDE_REPO_ROOT%/}/.claude/commands/gstatus.py"
    fi

    add_candidate "$HOME/.claude/commands/gstatus.py"

    for candidate in "${candidates[@]+"${candidates[@]}"}"; do
        if [ -f "$candidate" ]; then
            run_gstatus "$candidate"
            exit
        fi
    done

    {
        echo "Error: Unable to locate gstatus.py. Checked:"
        for candidate in "${candidates[@]+"${candidates[@]}"}"; do
            echo "  - $candidate"
        done
    } >&2
    exit 1
)`

Claude: Display the complete GitHub status output to the user including PR details, CI checks, file changes, comments, and action items.
