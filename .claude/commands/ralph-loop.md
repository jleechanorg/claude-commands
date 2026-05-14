---
description: "Start Ralph Wiggum loop in current session"
argument-hint: "PROMPT [--max-iterations N] [--completion-promise TEXT]"
allowed-tools: ["Bash(setup-ralph-loop:*)"]
hide-from-slash-command-tool: "true"
---

# Ralph Loop Command

Execute the setup script to initialize the Ralph loop:

```!
setup-ralph-loop $ARGUMENTS
```

Please work on the task. When you try to exit, the Ralph loop will feed the SAME PROMPT back to you for the next iteration. You'll see your previous work in files and git history, allowing you to iterate and improve.

CRITICAL RULE: If a completion promise is set, you may ONLY output it when the statement is completely and unequivocally TRUE. Do not output false promises to escape the loop, even if you think you're stuck or should exit for other reasons. The loop is designed to continue until genuine completion.

## State file

The loop creates `.claude/ralph-loop.local.md` (gitignored) to persist the prompt, iteration count, and completion promise across turns. This file is auto-created on first invocation and auto-deleted when the loop exits normally. If the file exists when `/ralph` is invoked, the loop resumes from the saved state rather than starting fresh.