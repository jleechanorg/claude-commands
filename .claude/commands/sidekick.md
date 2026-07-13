---
description: Spawn or respawn a persistent, crash-recoverable Sonnet sidekick (DEFAULT in-session teammate; tmux is the fallback) for any long-running mission
type: skill
execution_mode: immediate
scope: user
---
# /sidekick — spawn or respawn a Sonnet sidekick (DEFAULT: in-session teammate)

**DEFAULT (user directive 2026-07-11): the sidekick is a named in-process
teammate of THIS session's Agent Team — visible in the user's panel,
SendMessage-addressable ("I want it in this session"). tmux external sessions
are the FALLBACK only (must-survive-session-exit / no Agent Teams).**

Pattern origin: [Devin Fusion](https://cognition.com/blog/devin-fusion)
(hybrid-model harness — cost-cutting sidekick agents + dynamic routing).

Load and follow the `sidekick` skill at `~/.claude/skills/sidekick/SKILL.md`
(Skill tool: `sidekick`). Works for ANY long-running mission — PR/CI fleets,
research sweeps, migrations, monitoring, ops runbooks, non-repo work — not just
this repo or PRs. Repo-specific rules go in the mission adapter, never the core
protocol.

Usage: `/sidekick [sonnet|codex] [mission...]`

**Instant start:** spawning the DEFAULT in-session teammate is the FIRST
action on any `/sidekick` invocation — write/refresh STATE.md, then
`Agent({name: "sidekick-<mission-slug>", model: "sonnet",
run_in_background: true})` so it appears in the user's own team panel.
Fall back to an external tmux session ONLY when the mission must survive
this conversation ending (multi-day/overnight) or Agent Teams is
unavailable — and when you do, tell the user it won't appear in their
panel and give the `tmux attach` command. No preflight questions either
way.

Engines (both verified 2026-07-10): claude Sonnet (default) or codex
(`codex exec --dangerously-bypass-approvals-and-sandbox`, native `multi_agent`
for lanes). Between-run steering (tmux fallback mode only): `claude -p
--resume <session-id>` / `codex exec resume <session-id>`; durability in
the default in-session mode is STATE.md checkpoints + a P1 resumption
bead, not process persistence.

- `/sidekick` — respawn: reuse the existing named teammate if the team is
  still live, else respawn from the current project+branch's
  `/tmp/<project>/sidekick/<branch-or-mission>/STATE.md` + resumption bead
  (crash recovery; `/`→`-` in branch names; mission slug for non-repo work).
- `/sidekick sonnet audit all launchd jobs and fix drift` — fresh non-PR ops
  mission: write initial STATE.md, spawn the named in-session teammate.
- `/sidekick research LLM eval harnesses for 3 hours, write a report` — fresh
  non-repo research mission using the same default in-session teammate.

Behavior contract (details in the skill):
0. **In-session teammate is the visible default, tmux is the durability
   fallback.** The DEFAULT sidekick is a named in-process teammate of THIS
   session's Agent Team (Agent tool, `name:`, `run_in_background: true`) —
   visible in the user's panel, SendMessage-addressable both ways, durable
   via STATE.md + a P1 `br` bead (teammates die with the conversation; a
   fresh session respawns the same named teammate from STATE.md/bead). An
   external `tmux new-session` sidekick is its OWN separate Claude Code
   session and is NOT SendMessage-addressable from the main session — only
   use it for must-survive-session-exit missions or when Agent Teams is
   unavailable, and disclose the panel-invisibility + attach command when
   you do. `--teammate-mode tmux` (tmux mode only) is a real, documented
   flag (verified via web search 2026-07-10 — enables Agent Teams
   split-pane display; see upstream GitHub issue #24771 for a known bug in
   it) — do not remove it from tmux-mode launch commands.
1. State file first — respawns never overwrite an existing STATE.md.
2. One named teammate owns the mission: in-session by default (Agent tool,
   `run_in_background: true`), or in tmux-fallback mode a real
   `tmux new-session -d` running
   `claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p "<mission prompt>"`.
3. Commit-often discipline propagated verbatim to every sub-prompt.
4. Never merge / never force-push; milestone reports are captured evidence
   (STATE.md, git log, tmux capture in fallback mode) relayed to the user.
5. Proof before claim: for the default mode, verify via the team panel and
   STATE.md progress; for tmux fallback, verify with `tmux ls`,
   `tmux capture-pane`, and process inspection before saying the sidekick
   started.
