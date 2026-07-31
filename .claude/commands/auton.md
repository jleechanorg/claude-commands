---
description: Diagnose why autonomous PR work is stalled or incomplete
type: orchestration
execution_mode: immediate
---

# /auton

Read and execute `.claude/skills/auton/SKILL.md`.

Use live worker, repository, PR, and CI state. Do not infer readiness from
historical summaries or advisory-review state. `/green` means current-head CI
success plus mergeable/no conflicts.
