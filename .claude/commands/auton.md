---
description: Diagnose why the AO + Hermes automation system is not autonomously driving PRs to green and merge.
type: skill
execution_mode: immediate
---

# /auton [description]

Autonomy diagnostic: figure out why PRs aren't being driven to N-green and merged without human intervention. Run this AFTER a work block ends (retrospective post-mortem) — for live/concurrent monitoring use `/babysit` instead.

Read `~/.claude/skills/auton/SKILL.md` and execute the full workflow with the provided context.

## Quick reference

| Phase | What it covers |
|-------|-----------------|
| Read first | Hermes config, AO worker vs CLI config, agent policies |
| Diagnostic questions 0-8 | Active config, lifecycle-worker/orchestrator state, spawns, sessions, non-green reasons, rate limits, skeptic-cron wiring, stray worktrees |
| Group A + B sweep | Infrastructure/session state + GitHub/rate-limit diagnostics, run in parallel |
| Cross-references | CHANGES_REQUESTED gaps, stalled PRs, zombie sessions, 6-green/zero-touch rate, skeptic-cron correctness spot-check |
| 48h worker review | Per-worker outcome table + root cause taxonomy (RC-1..RC-7) |

## Example

```
/auton
/auton workers keep going idle after CR approval
```
