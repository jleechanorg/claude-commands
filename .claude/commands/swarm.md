---
description: /swarm — orchestrate multi-agent swarms (ultracode workflows + agent-team lanes) with adversarial verification
type: llm-orchestration
execution_mode: immediate
---

# /swarm <goal> [--engine workflow|team|sidekick] [--shape retro|review|solutions|innov|triage] [--sidekick [model]]

Run the goal as a multi-agent swarm with adversarial verification, cost-routed subagents, and artifacts committed to a PR.

Read `~/.claude/skills/swarm/SKILL.md` and execute the full playbook with the provided goal.

## Defaults

- Engine: Workflow tool (ultracode). Agent teams only for interactive lanes needing mid-flight steering.
- Durability: ALL swarm work runs INSIDE a sidekick by default (`--sidekick [fable|sonnet]` only overrides the model; see `~/.claude/skills/sidekick/SKILL.md`): state at `/tmp/<repo>/sidekick/<branch>/STATE.md`, commit-often propagated to all sub-agents, restart via `/sidekick` in any session. The main loop supervises and relays only — exception: a single quick fan-out (<15 min, user watching) may run inline.
- Verification: 3-lens refute-by-default, ≥2/3 to survive; audit dead-verifier false kills.
- Models: haiku (mechanical), sonnet (miners/verifiers/docs); never let fan-outs inherit the session model.
- Output: disjoint OUTDIR per lane under repo `docs/` (or `~/roadmap/`), commit+push per completed package.
- Close-out: /advice pass → PR comment with runId/agent/token provenance → /learn.

## Examples

```text
# Monthly design retrospective swarm (Collect→Verify→Synthesize→Plan)
/swarm design retrospective for last month --shape retro

# Adversarial code-quality sweep of your_app (Review→Verify→Innovate→Docs)
/swarm code quality audit of your_app --shape review

# Innovation pass over existing design docs (Innovate→Challenge)
/swarm one smartest addition per design doc in docs/plans/<dir> --shape innov

# Crash-recoverable overnight fleet drive owned by a fable sidekick
/swarm fix CI health then drive all open PRs to green --sidekick fable
```
