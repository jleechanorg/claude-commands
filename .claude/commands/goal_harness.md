---
description: "Goal Harness — work on a goal until /es, /er, /code_standards, and Independent Agent Review all pass via adversarial subagents"
type: quality
execution_mode: immediate
aliases: [h]
---

# /goal_harness — Goal-Driven Harness Loop

Define a goal (via builtin `/goal`), then iterate until **4 adversarial gates** all pass —
each dispatched to an isolated subagent that receives only the diff and its standard.

Read `~/.claude/skills/goal_harness/SKILL.md` and execute the full workflow.

## Usage

```
/goal_harness <goal description>
/h <goal description>               # alias
```

## Gate summary

| Gate | Checks |
|------|--------|
| `/es` | Evidence Standards (user-scope + project-scope) |
| `/er` | Evidence Review (adversarial synthesis) |
| `/code_standards` | ZFC + ZFC-leveling + root-cause-first (3 parallel lanes) |
| Independent Agent Review | Full-diff code review — bugs, anti-patterns, missing tests |

Convergence requires **4/4 PASS** (after normalization). Max 10 iterations; stall detection at 2x same score.

## Related Commands

- `/goal` — builtin Claude Code goal command (sets success criteria)
- `/es` — Evidence Standards (reference/display)
- `/er` — Evidence Review (adversarial synthesis)
- `/code_standards` — Coding standards dispatch (ZFC + ZFC-leveling + root-cause-first)
- `/converge` — Iterative goal achievement loop (formerly `/goalexec`)
- `/converge_define` — Define-only variant (sets goal without execution)
