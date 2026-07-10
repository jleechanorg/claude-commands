# /sidekick — spawn or respawn a real Sonnet Claude Code sidekick in tmux

Load and follow the `sidekick` skill at `~/.claude/skills/sidekick/SKILL.md`
(Skill tool: `sidekick`). Works for ANY long-running mission — PR/CI fleets,
research sweeps, migrations, monitoring, ops runbooks, non-repo work — not just
this repo or PRs. Repo-specific rules go in the mission adapter, never the core
protocol.

Usage: `/sidekick [sonnet] [mission...]`

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
0. **Claude team management first when allowed** — if the session exposes Agent
   Teams primitives (named teammates + SendMessage), the sidekick is managed as
   a named Claude team teammate (`sidekick-<mission-slug>`); team messaging is
   the control channel and `--teammate-mode tmux` ties the process into the
   team's split-pane display. Raw tmux capture-pane/send-keys management is the
   FALLBACK only, for sessions where teams are not allowed.
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
