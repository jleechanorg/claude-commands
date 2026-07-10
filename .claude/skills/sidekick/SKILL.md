---
name: sidekick
description: Spawn or respawn a persistent, crash-recoverable Sonnet Claude Code teammate in tmux for ANY long-running mission — PR/CI fleets, research sweeps, migrations, monitoring, ops runbooks, data pipelines, multi-day projects in any repo or no repo at all — with disk-checkpointed state and commit-often discipline. Use when the user says /sidekick, "respawn the sidekick", or wants long work to survive conversation crashes.
---

# Sidekick — persistent restartable Sonnet Claude Code teammate

One named background teammate owns long-running orchestration. The main session
supervises and relays milestones. If the conversation crashes, a fresh session
respawns the sidekick and it resumes from a disk state file with zero
conversation context.

**Real primitive:** sidekick is a real Claude Code process launched in tmux:

```bash
claude --model sonnet --teammate-mode tmux
```

Do not describe sidekick as an in-memory Agent lane or task-list pseudo team.

## Invocation

`/sidekick [sonnet] [mission...]`

- `model`: always `sonnet` unless the user explicitly asks for a different model
  in the current message. This skill's default and documented path are
  **Sonnet-only**.
- `mission`: freeform priorities. If omitted, resume whatever the state file says.

## Core mechanics

**State file (per project + branch/mission):**
`/tmp/<project-slug>/sidekick/<branch-or-mission>/STATE.md` — `<project-slug>` is
the repo name for repo missions, or any stable slug for non-repo missions (e.g.
`/tmp/homelab-ops/sidekick/dashboard-watch/STATE.md`); `/` in branch names is
sanitized to `-`. Scoping is MANDATORY — two sidekicks with different missions
sharing one STATE.md clobber each other's Mission/Next Actions. For fleet-wide /
cross-branch missions, use a mission slug instead of a branch name (e.g.
`/tmp/<repo>/sidekick/fleet-ci-health/STATE.md`). Sections: Mission, Ground
truth, Standing rules, Progress Log (append-only, timestamped), Next Actions
(rewritten every step). This file IS the recovery mechanism.

**Legacy shared file:** if `/tmp/<repo>/sidekick/STATE.md` exists from an older
spawn, do NOT edit another mission's sections in it. Migrate only YOUR mission's
section into the new branch-scoped path, leave a one-line pointer behind, and
never touch the rest.

## Spawn procedure (main session)

1. Compute a project slug and mission slug. Create the state dir. If STATE.md
   exists, this is a RESPAWN: do not overwrite it; the new sidekick resumes from
   it. If missing, write initial STATE.md from current context (mission, ground
   truth, standing rules, next actions).

2. Write the startup prompt to a file next to STATE.md:

   ```bash
   cat > "$STATE_DIR/sidekick.prompt.md" <<'PROMPT'
   You are sidekick — the persistent, restartable Sonnet Claude Code teammate for
   this mission. The main session may crash; YOU are the durable worker.

   Model contract: you are running under `claude --model sonnet --teammate-mode tmux`.
   Do not switch to another model unless the user explicitly approved it in the
   current mission.

   Startup protocol:
   1. Read STATE.md.
   2. Resume from Next Actions. Never redo logged steps.
   3. After every completed step, append Progress Log and rewrite Next Actions.

   Recovery discipline, verbatim and non-negotiable:
   COMMIT OFTEN: commit + push after EVERY green unit of work. Never hold more
   than ~30 minutes of uncommitted changes. Include this instruction verbatim in
   every sub-agent prompt you write.

   Universal hard rules:
   - Irreversible/outward-facing actions (merges, deploys, deletions,
     publishing, sending messages to humans) are human-only unless explicitly
     pre-authorized.
   - Sign-off on any deliverable requires adversarial verification. Use another
     real Sonnet tmux Claude Code verifier, or a documented external CLI reviewer
     only if the user explicitly approved non-Sonnet reviewers.
   - Re-check file overlap before every ready/green claim, not just at spawn.
     A lane that was clean at spawn can become conflicting after a sibling lane
     merges and origin/main advances.
   - Semantic contradiction is not a merge conflict; stop and flag the scope call
     instead of choosing one behavioral intent silently.
   - Quarantined or foreign uncommitted work in a shared-name worktree must not
     be touched. Do conflict resolution in a third fresh detached worktree.
   - `statusCheckRollup` and check-runs APIs can include stale attempts. Group by
     check name and use only the newest attempt's conclusion.
   - Batch independent CLI calls, but keep a single writer for each mutable file.

   Mission:
   <mission text>
   PROMPT
   ```

3. Launch a real tmux session:

   ```bash
   SESSION="sidekick-${MISSION_SLUG}"
   tmux kill-session -t "$SESSION" 2>/dev/null || true
   tmux new-session -d -s "$SESSION" -x 160 -y 48 \
     "cd '$PWD' && claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p \"\$(cat '$STATE_DIR/sidekick.prompt.md')\"; rc=\$?; printf '\n[sidekick done exit=%s]\n' \"\$rc\"; exec bash"
   ```

4. Verify the sidekick actually started before reporting success:

   ```bash
   tmux ls | grep "^${SESSION}:"
   tmux list-panes -a -F '#{session_name} #{pane_pid} #{pane_current_command}' \
     | grep "^${SESSION} "
   tmux capture-pane -t "$SESSION" -p -S -80 | tail -80
   ps -ef | grep "claude --model sonnet --teammate-mode tmux" | grep -v grep
   ```

   If these checks do not show a real tmux session and a real Claude Code command,
   the sidekick did **not** start. Fix the tmux/Claude launch before doing any
   mission work.

## Respawn procedure

1. Locate the branch/mission-scoped STATE.md.
2. Do not rewrite it.
3. Reuse the existing `sidekick.prompt.md` if present; otherwise generate it from
   STATE.md using the template above.
4. Launch `tmux new-session` with the same Sonnet Claude Code command.
5. Capture pane output to verify it read STATE.md and resumed from Next Actions.

## Milestone reporting

The main session polls the tmux pane and relays dense milestone updates. The
sidekick itself writes durable state to STATE.md and git. A report is not valid
unless it includes proof: tmux capture, git status/log, PR/commit URL, or test
output.

## Why this beats main-session fan-outs

Main-session fan-outs die with the session and re-derive context on resume. The
sidekick externalizes ALL state to disk + git (frequent pushes), so recovery cost
is one tmux Sonnet Claude Code respawn. Parallel verifier lanes can still happen,
but they must be real Sonnet tmux Claude Code sessions unless the user explicitly
approves another model/tool for that mission.
