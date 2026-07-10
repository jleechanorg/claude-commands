---
name: sidekick
description: Spawn or respawn a persistent, crash-recoverable Sonnet Claude Code teammate in tmux for ANY long-running mission — PR/CI fleets, research sweeps, migrations, monitoring, ops runbooks, data pipelines, multi-day projects in any repo or no repo at all — with disk-checkpointed state and commit-often discipline. Main-session control channel is STATE.md + tmux (the sidekick is its own session — NOT SendMessage-addressable); when Agent Teams is allowed, the sidekick runs its own lanes as a real Claude team and main-session supervision teammates are team-managed. Use when the user says /sidekick, "respawn the sidekick", or wants long work to survive conversation crashes.
---

# Sidekick — persistent restartable Sonnet Claude Code teammate

One named background teammate owns long-running orchestration. The main session
supervises and relays milestones. If the conversation crashes, a fresh session
respawns the sidekick and it resumes from a disk state file with zero
conversation context.

**Pattern origin:** [Devin Fusion](https://cognition.com/blog/devin-fusion) —
Cognition's hybrid-model harness that keeps frontier-level coding intelligence
while cutting costs with sidekick agents and dynamic routing. This skill is the
Claude Code adaptation: a cheap durable Sonnet sidekick does the long-running
work while the premium main session only supervises.

**Real primitive:** sidekick is a real Claude Code process launched in a real
`tmux new-session`:

```bash
tmux new-session -d -s "$SESSION" \
  "cd '$PWD' && CLAUDE_CONFIG_DIR='${CLAUDE_CONFIG_DIR:-$HOME/.claude}' claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p \"\$(cat '$PROMPT_FILE')\"; exec bash"
```

**Auth env propagation is MANDATORY in the launch command.** The tmux server
snapshots its environment when IT started (possibly days ago) and can even mark
variables like `CLAUDE_CODE_CONFIG_DIR`/`CLAUDE_CONFIG_DIR` for removal — a
sidekick launched without inline env silently runs on a DIFFERENT account than
the parent session. Real incident (2026-07-10): every sidekick spawn died with
"You've hit your session limit" on the default `~/.claude` account while the
parent session's `CLAUDE_CONFIG_DIR=~/.claude-wa` account had quota. Always
inline `CLAUDE_CONFIG_DIR` (and any deliberate `ANTHROPIC_*` routing overrides)
into the tmux command string; never trust the tmux server to pass them.

`--teammate-mode tmux` is a real, documented flag (Agent Teams split-pane
display, verified via web search 2026-07-10; see upstream GitHub issue
#24771 for a known bug in it). An earlier pass this session incorrectly
concluded it was fake — it doesn't appear in `claude --help`'s printed text
(help output can be incomplete/filtered) and the CLI silently accepts ANY
unknown flag without erroring (confirmed by passing a deliberately fake
flag), so neither absence-from-help nor "ran without erroring" is valid
proof either way. Verify CLI-flag claims with a real web search before
editing this file, not just local `--help` text. The persistence and
crash-recoverability come from the `tmux new-session` wrapper — the tmux
session keeps running independently of the parent Claude Code process even
if the orchestrating conversation crashes.

Do not describe sidekick as an in-memory Agent lane or task-list pseudo team.

## Management: use Claude teams where they actually exist (MANDATORY)

The tmux process is the durability substrate. Know what Agent Teams can and
cannot do here before picking a control channel (verified against the official
Agent Teams docs, 2026-07-10):

**Hard fact — the tmux sidekick is NOT SendMessage-addressable from the main
session.** An externally launched `tmux new-session ... claude -p` process is
its own Claude Code session with its own team; Agent Teams is one-team-per-
session with no cross-session join, and `--teammate-mode tmux` is a display-
mode flag (it renders teammates *that a session itself spawns* as tmux split
panes — it does not register the process into anyone else's team). Do not
attempt SendMessage to the sidekick and do not "debug" its silence — the
route does not exist (see anthropics/claude-code#24771 for messaging-routing
failures even for lead-spawned tmux teammates).

Required channel per relationship:

1. **Main session → sidekick: STATE.md + tmux (this IS the channel, not a
   fallback).** Durable directives go into STATE.md (Standing rules / Next
   Actions); interactive nudges via `tmux send-keys`; reading/proof via
   `tmux capture-pane`.
2. **Inside the sidekick: run lanes as a real Claude agent team when allowed
   (DEFAULT).** When the sidekick's own harness exposes Agent Teams, its
   fan-out lanes run as named teammates (task claims + SendMessage between
   sidekick and lanes) rather than fire-and-forget subagents — this is where
   `--teammate-mode tmux` earns its keep, rendering the sidekick's own
   teammates as split panes inside the sidekick's tmux session. Caveat: teams
   under `-p` (print mode) are undocumented; if a team fails to form, fall
   back to Agent-tool subagents and note that in STATE.md.
3. **In the main session: supervision teammates ARE team-managed.** Any
   companion lanes the main session spawns via its own Agent tool (verifiers,
   watchers) are named, SendMessage-addressable teammates — but they die with
   the parent CLI, so they must never be the durable worker. Wait for a
   teammate's shutdown to be confirmed before reusing its name — same-name
   respawn while a prior instance winds down spawns duplicate concurrent
   workers on the same mission.

Name everything `sidekick-<mission-slug>` consistently (tmux session, STATE.md
header, any related teammate names) so humans and agents can correlate the
pieces. Crash-recovery is unchanged either way: STATE.md on disk + git pushes
are the durable state; every control channel is disposable.

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

   Model contract: you are running under `claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions`.
   Do not switch to another model unless the user explicitly approved it in the
   current mission.

   Startup protocol:
   1. Read STATE.md.
   2. Resume from Next Actions. Never redo logged steps.
   3. After every completed step, append Progress Log and rewrite Next Actions.

   Lane management: when your harness allows Agent Teams, run your fan-out
   lanes as a real Claude agent team (named teammates + task claims); if a
   team fails to form (teams under -p are undocumented), fall back to
   Agent-tool subagents and note it in STATE.md. Your operator steers you via
   STATE.md and tmux, not SendMessage — check STATE.md's Standing rules /
   Next Actions for new directives at every checkpoint.

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
     "cd '$PWD' && CLAUDE_CONFIG_DIR='${CLAUDE_CONFIG_DIR:-$HOME/.claude}' claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p \"\$(cat '$STATE_DIR/sidekick.prompt.md')\"; rc=\$?; printf '\n[sidekick done exit=%s]\n' \"\$rc\"; exec bash"
   ```

4. Verify the sidekick actually started before reporting success:

   ```bash
   tmux ls | grep "^${SESSION}:"
   tmux list-panes -a -F '#{session_name} #{pane_pid} #{pane_current_command}' \
     | grep "^${SESSION} "
   tmux capture-pane -t "$SESSION" -p -S -80 | tail -80
   pgrep -fl -- "--teammate-mode tmux"   # ps may show the full binary path, so
                                         # match on the flag, not "claude --model"
   ```

   Note: in `-p` (print) mode the pane stays BLANK until the run finishes — an
   empty capture is not failure. Liveness proof is the `pgrep` hit (a `claude`
   process with the flag) plus, later, STATE.md's Progress Log advancing. A
   pane showing "You've hit your session limit" means the sidekick launched on
   a quota-exhausted account — check the auth env propagation above.

   If these checks do not show a real tmux session and a real Claude Code command,
   the sidekick did **not** start. Fix the tmux/Claude launch before doing any
   mission work.

## Respawn procedure

1. Locate the branch/mission-scoped STATE.md.
2. Do not rewrite it.
3. Reuse the existing `sidekick.prompt.md` if present; otherwise generate it from
   STATE.md using the template above.
4. Launch `tmux new-session` with the same Sonnet Claude Code command (including
   the inline `CLAUDE_CONFIG_DIR` propagation — respawns from a fresh session
   are exactly when the tmux server's stale env bites).
5. Capture pane output to verify it read STATE.md and resumed from Next Actions.

## Milestone reporting

The main session polls the tmux pane (`capture-pane`) and STATE.md and relays
dense milestone updates — the sidekick cannot SendMessage the main session
(separate sessions, separate teams). The
sidekick itself writes durable state to STATE.md and git. A report is not valid
unless it includes proof: tmux capture, git status/log, PR/commit URL, or test
output.

## Why this beats main-session fan-outs

Main-session fan-outs die with the session and re-derive context on resume. The
sidekick externalizes ALL state to disk + git (frequent pushes), so recovery cost
is one tmux Sonnet Claude Code respawn. Parallel verifier lanes can still happen,
but they must be real Sonnet tmux Claude Code sessions unless the user explicitly
approves another model/tool for that mission.
