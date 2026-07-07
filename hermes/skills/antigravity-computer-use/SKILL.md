---
name: antigravity-computer-use
description: Use when asked to control, automate, click/type in, or manage Google Antigravity from Hermes. This Hermes shim skill delegates canonical behavior to the Claude skill at ~/.claude/skills/antigravity-computer-use/SKILL.md.
---

# Antigravity Computer Use (Hermes shim)

This is a pointer skill so Hermes can trigger Antigravity automation from `~/.hermes/skills`.

## Canonical instructions

Read and follow:

`~/.claude/skills/antigravity-computer-use/SKILL.md`

Treat that Claude skill as source-of-truth for:
- Manager-window targeting
- Peekaboo screenshot→decide→act loop
- Workspace/conversation enumeration
- "Allow this conversation" handling
- Completion criteria and evidence format

## Local rule

If the Claude skill path is missing, stop and report:
- missing path
- exact path expected
- one-line remediation (`restore/copy the Claude skill, then retry`)
