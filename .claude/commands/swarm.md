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
2. **Spawn the worker lanes as OFFICIAL Agent Teams teammates IN THE CURRENT
   SESSION** (Agent tool with `name: lane-<n>-<topic>`) — this is the real
   /team-claude-class feature: the teammates appear in THIS session's team UI
   immediately, are SendMessage-addressable, and register in
   `~/.claude/teams/session-*/config.json` with per-teammate inboxes. The user
   must SEE the team in their own window — a team hidden inside a tmux
   sidekick's session does not satisfy this contract.
3. Spawn the tmux sidekick as the **durability keeper** (`/sidekick`): it owns
   STATE.md checkpoints and respawns/re-drives the mission if this
   conversation crashes. It does NOT own the visible lanes in an attended
   session.
Headless/unattended runs (cron, overnight) invert this: lanes run inside the
sidekick (interactive TUI mode for team lanes) since no user is watching.
The user must see a live in-session Claude team + the sidekick within the
first minute; context recall and lane design happen after the team exists.

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
