---
description: Monitor and supervise active AO worker sessions
type: orchestration
execution_mode: immediate
---

# /babysit

Read and execute `.claude/skills/babysit/SKILL.md` with the supplied session,
PR, branch, or watch mode.

This command monitors AO worker state. It does not redefine `/green`, merge a
PR, or make CodeRabbit/Bugbot approval mandatory.
