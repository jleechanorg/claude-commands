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
  latest Sonnet via `claude --model sonnet --teammate-mode tmux`.
- `/sidekick sonnet audit all launchd jobs and fix drift` — fresh non-PR ops
  mission: write initial STATE.md, spawn a real tmux Claude Code teammate.
- `/sidekick research LLM eval harnesses for 3 hours, write a report` — fresh
  non-repo research mission using the same Sonnet tmux sidekick.

Behavior contract (details in the skill):
1. State file first — respawns never overwrite an existing STATE.md.
2. One named background teammate: a real `tmux new-session` running
   `claude --model sonnet --teammate-mode tmux`.
3. Commit-often discipline propagated verbatim to every sub-prompt.
4. Never merge / never force-push; milestone reports are captured from tmux and
   relayed to the user.
5. Proof before claim: verify with `tmux ls`, `tmux capture-pane`, and process
   inspection before saying the sidekick started.
6. **5-minute checkpoint cadence (mandatory, every lane owner):** every ≤5 min the
   sidekick AND each lane owner must append a timestamped heartbeat + current
   phase to STATE.md, `br update <P1-bead-id> --append ...` then `br sync` (one
   bead writer per mission), and make a local commit of state so a crash loses
   ≤5 min on a LIVE session. The 5-min target is best-effort and only holds
   while the supervisor + watcher are alive; STATE.md in `/tmp` does NOT survive
   host reboot / cleanup / parent-CLI death. Drive with `CronCreate` or a
   background `tmux respawn-pane -k` loop; a chat-only print is NOT a
   checkpoint, and `tmux respawn-pane` WITHOUT `-k` is not a timer.
   **Commit-safety:** if the worktree has unrelated staged/modified work, NEVER
   `git commit`/`git add -A` there — route to an isolated state repo
   (`git init` a `.tmp/<mission>-state-repo/`, copy state in, commit) or a WIP
   branch with path-scoped `git add -- <state paths>`. **Gitignored `.tmp/`
   state** needs the isolated-repo (or `git add -f`) path. **Non-repo
   missions:** fall back to the plain `/tmp/<project-slug>/sidekick/<branch>/`
   file path.
