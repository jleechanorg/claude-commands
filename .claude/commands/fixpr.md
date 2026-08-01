---
description: /fixpr Command - Intelligent PR Fix Analysis
type: skill
execution_mode: immediate
---

# /fixpr <PR-number> [--auto-apply] [--scope=pattern|comprehensive]

Analyze and fix PR blockers (CI failures, merge conflicts, bot/review
feedback) to get a PR into a mergeable state — local-first, GitHub is the
sole source of truth, never merges the PR itself.

Read `~/.claude/skills/fixpr/SKILL.md` and execute the full workflow with
the provided PR number and flags.

## Quick reference

| Flag | Effect |
|------|--------|
| (none) | Analyze and fix, default scope |
| `--auto-apply` | Auto-apply safe fixes only (imports, formatting, docs) |
| `--scope=pattern` | Fix + scan codebase for the same failure pattern elsewhere |
| `--scope=comprehensive` | Fix all related test infrastructure |

## Examples

```
/fixpr 1234
/fixpr 1234 --auto-apply
/fixpr 1234 --scope=pattern
```

Also embodied as the `copilot-fixpr` subagent type for parallel/automated
dispatch across a PR fleet — see the skill's "2026-07 fleet-drive lessons"
section before batch-driving a large backlog.
