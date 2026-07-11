---
description: /swarm — orchestrate multi-agent swarms (ultracode workflows + agent-team lanes) with adversarial verification
type: llm-orchestration
execution_mode: immediate
---

# /swarm <goal> [--engine workflow|team] [--shape retro|review|solutions|innov|triage] [--sidekick [model]]

The sidekick wrap is mandatory regardless of `--engine` — `--engine` picks the
fan-out mechanism the sidekick uses (Workflow tool vs agent-team lanes); it is
never a way to skip the sidekick. `--sidekick [model]` only overrides the model.

Run the goal as a multi-agent swarm with adversarial verification, cost-routed subagents, and artifacts committed to a PR.

**Instant start (mandatory UX).** The FIRST tool calls of any `/swarm <goal>`
invocation — before any analysis, recall, or lane scoping — are:
1. Write the branch/mission-scoped STATE.md (30 seconds, from the goal text).
2. Spawn the sidekick as an **interactive tmux TUI** (claude Sonnet,
   `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, `--teammate-mode tmux`) so its
   lanes run as a REAL Claude team — split panes, named teammates.
3. Spawn a named main-session supervision teammate
   (`sidekick-supervisor-<mission-slug>`) via the Agent tool.
The user must see a live Claude team + sidekick within the first minute;
context recall and lane design happen after the team exists, not before.

Read `~/.claude/skills/swarm/SKILL.md` and execute the full playbook with the provided goal.

## Defaults

- Engine: Workflow tool (ultracode). Agent teams only for interactive lanes needing mid-flight steering.
- Durability: ALL swarm work runs INSIDE a sidekick — ALWAYS, no inline exception (`--sidekick [fable|sonnet]` only overrides the model; see `~/.claude/skills/sidekick/SKILL.md`): a real tmux Claude Code process, steered via STATE.md + tmux (its own session — not SendMessage-addressable), running its lanes as a real Claude team when interactive (Agent-tool subagents in `-p` mode); state at `/tmp/<project-slug>/sidekick/<branch>/STATE.md`, commit-often propagated to all sub-agents, restart via `/sidekick` in any session. The main loop supervises and relays only.
- Verification: 3-lens refute-by-default, ≥2/3 to survive; audit dead-verifier false kills.
- Models: haiku (mechanical), sonnet (miners/verifiers/docs); never let fan-outs inherit the session model.
- Output: disjoint OUTDIR per lane under repo `docs/` (or `~/roadmap/`), commit+push per completed package.
- Close-out: /advice pass → PR comment with runId/agent/token provenance → /learn.

## Examples

```text
# Monthly design retrospective swarm (Collect→Verify→Synthesize→Plan)
/swarm design retrospective for last month --shape retro

# Adversarial code-quality sweep of mvp_site (Review→Verify→Innovate→Docs)
/swarm code quality audit of mvp_site --shape review

# Innovation pass over existing design docs (Innovate→Challenge)
/swarm one smartest addition per design doc in docs/plans/<dir> --shape innov

# Crash-recoverable overnight fleet drive owned by a fable sidekick
/swarm fix CI health then drive all open PRs to green --sidekick fable
```
