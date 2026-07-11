# /sidekick — spawn or respawn a real Sonnet Claude Code sidekick in tmux

Pattern origin: [Devin Fusion](https://cognition.com/blog/devin-fusion)
(hybrid-model harness — cost-cutting sidekick agents + dynamic routing).

Load and follow the `sidekick` skill at `~/.claude/skills/sidekick/SKILL.md`
(Skill tool: `sidekick`). Works for ANY long-running mission — PR/CI fleets,
research sweeps, migrations, monitoring, ops runbooks, non-repo work — not just
this repo or PRs. Repo-specific rules go in the mission adapter, never the core
protocol.

Usage: `/sidekick [sonnet|codex] [mission...]`

**Instant start:** spawning the tmux session is the FIRST action on any
`/sidekick` invocation — write STATE.md and launch; no preflight questions.
Use interactive TUI mode whenever the mission benefits from real team lanes
or live steering; `-p` for unattended batch missions.

Engines (both verified 2026-07-10): claude Sonnet (default) or codex
(`codex exec --dangerously-bypass-approvals-and-sandbox`, native `multi_agent`
for lanes). Between-run steering: `claude -p --resume <session-id>` /
`codex exec resume <session-id>`; in-flight steering via STATE.md for both.

- `/sidekick` — respawn from the current project+branch's
  `/tmp/<project>/sidekick/<branch-or-mission>/STATE.md` (crash recovery;
  `/`→`-` in branch names; mission slug for non-repo work). Default model is
  latest Sonnet via a real `tmux new-session` running
  `claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p "<mission prompt>"`.
- `/sidekick sonnet audit all launchd jobs and fix drift` — fresh non-PR ops
  mission: write initial STATE.md, spawn a real tmux Claude Code teammate.
- `/sidekick research LLM eval harnesses for 3 hours, write a report` — fresh
  non-repo research mission using the same Sonnet tmux sidekick.

Behavior contract (details in the skill):
0. **Claude teams where they actually exist** — the tmux sidekick is its OWN
   session and is NOT SendMessage-addressable from the main session (Agent
   Teams is one-team-per-session, no cross-session join; `--teammate-mode
   tmux` is display-only for teammates a session itself spawns). Main-session
   control channel is STATE.md + `tmux send-keys`/`capture-pane`. When Agent
   Teams is allowed: an INTERACTIVE (TUI) sidekick runs its OWN fan-out lanes
   as a named Claude team (two-way SendMessage with lanes, split panes inside
   its tmux session); a `-p` sidekick has NO team primitives and always falls
   back to Agent-tool subagents. Main-session supervision lanes are
   team-managed Agent-tool teammates (addressable, but they die with the CLI
   — never the durable worker).
1. State file first — respawns never overwrite an existing STATE.md.
2. One named background teammate: a real `tmux new-session -d` running
   `claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p "<mission prompt>"`.
   `--teammate-mode tmux` is a real, documented flag (verified via web search
   2026-07-10 — enables Agent Teams split-pane display; see upstream GitHub
   issue #24771 for a known bug in it). Do not remove it — an earlier pass
   this session incorrectly concluded it was fake because it doesn't appear
   in `claude --help`'s printed text (help output can be incomplete) and
   because the CLI silently accepts unknown flags without erroring (so "ran
   without erroring" was never valid proof either way). Verify claims like
   this with a real web search before editing harness docs, not just local
   `--help` text.
3. Commit-often discipline propagated verbatim to every sub-prompt.
4. Never merge / never force-push; milestone reports are captured from tmux and
   relayed to the user.
5. Proof before claim: verify with `tmux ls`, `tmux capture-pane`, and process
   inspection before saying the sidekick started.
