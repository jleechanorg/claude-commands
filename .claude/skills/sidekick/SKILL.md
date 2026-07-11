---
name: sidekick
description: Spawn or respawn a persistent, crash-recoverable sidekick (claude Sonnet by default, codex engine supported) for ANY long-running mission — PR/CI fleets, research sweeps, migrations, monitoring, ops runbooks, data pipelines, multi-day projects in any repo or no repo at all — with disk-checkpointed state and commit-often discipline. DEFAULT: spawn the worker as a named in-process teammate of the invoking session's Agent Team (visible in the user's panel, SendMessage-addressable), with durability via STATE.md checkpoints + a P1 resumption bead. tmux external session is the FALLBACK only for must-survive-session-exit missions or when Agent Teams is unavailable (then: STATE.md + tmux is the control channel, NOT SendMessage; disclose panel invisibility + attach command). Use when the user says /sidekick, "respawn the sidekick", or wants long work to survive conversation crashes.
---

# Sidekick — persistent restartable Sonnet Claude Code teammate

One named background teammate owns long-running orchestration. The main session
supervises and relays milestones. If the conversation crashes, a fresh session
respawns the sidekick and it resumes from a disk state file with zero
conversation context.

## DEFAULT MODE: in-session teammate (user directive 2026-07-11 — "I want it in this session")

**Spawn the sidekick (and its lanes) as named in-process teammates of the
INVOKING session's Agent Team** — `Agent({name: "sidekick", model: "sonnet",
run_in_background: true})` plus one named teammate per lane. This is what the
user means by "real /team-claude": the roster is **visible in the user's own
panel**, every member is SendMessage-addressable both ways, and the user can
watch/steer without attaching to anything.

- Durability in this mode = **STATE.md checkpoints + a P1 resumption bead
  (`br`) + commit-often**, NOT process persistence — teammates die with the
  conversation; that is an accepted trade for visibility. On crash: a fresh
  session re-reads STATE.md / `br show <runbook-bead>` and respawns the same
  named teammates (one spawn, zero context re-derivation).
- **External `tmux new-session` sidekicks are the FALLBACK ONLY** — for
  missions that must survive the conversation process itself (multi-day
  unattended runs) or when Agent Teams is unavailable. Even then, disclose the
  panel-invisibility + attach command up front. Real incident (2026-07-11):
  externally launched tmux sidekicks read as "the team never started" to the
  user because nothing appeared in their panel; missions were migrated to
  in-session teammates on explicit request.
- Migration recipe (tmux → in-session): direct the tmux sidekick to checkpoint
  STATE.md + shut down its lanes, kill its session, then spawn the same-named
  teammates in-session pointed at the same STATE.md.

**Everything below (tmux launch commands, engines, stall watchdog) applies to
the FALLBACK external-tmux mode.** The STATE.md / beads / commit-often /
milestone-reporting protocol applies to BOTH modes.

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
2. **Inside the sidekick: attempt team-based lanes by default — and verify a
   team actually formed before reporting lanes as team-based.** When the
   sidekick's own harness exposes Agent Teams, its
   fan-out lanes run as named teammates (task claims + SendMessage between
   sidekick and lanes) rather than fire-and-forget subagents — this is where
   `--teammate-mode tmux` earns its keep, rendering the sidekick's own
   teammates as split panes inside the sidekick's tmux session. **Empirical
   reality (claude 2.1.197, verified 2026-07-10): a `-p` print-mode sidekick
   gets NO team primitives even with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
   — Agent-tool subagent fallback is the guaranteed outcome in `-p`. An
   INTERACTIVE (TUI) sidekick DOES form a real team — named teammates,
   two-way SendMessage with its lanes, split panes (verified; see the mode
   choice in the Engines section).** Attempt the team, verify whether it
   formed, record the answer in STATE.md, and never report lanes as
   "team-based" without that proof.
3. **In the main session: the VISIBLE official team lives here.** In an
   attended session, worker lanes and supervision teammates are spawned via
   the session's own Agent tool with `name:` — official Agent Teams members,
   visible in the user's team UI, SendMessage-addressable, registered in
   `~/.claude/teams/session-*/config.json` with per-teammate inboxes. This is
   what "start a Claude team" means to the user; teams inside the sidekick's
   tmux session are invisible to them. Main-session teammates die with the
   parent CLI, so the durable state stays in STATE.md and the tmux sidekick
   respawns/re-drives the mission after a crash — teammates are the visible
   workers, never the durability layer. Wait for a
   teammate's shutdown to be confirmed before reusing its name — same-name
   respawn while a prior instance winds down spawns duplicate concurrent
   workers on the same mission.

Name everything `sidekick-<mission-slug>` consistently (tmux session, STATE.md
header, any related teammate names) so humans and agents can correlate the
pieces. Crash-recovery is unchanged either way: STATE.md on disk + git pushes
are the durable state; every control channel is disposable.

## Team visibility is MANDATORY (user directive 2026-07-11)

The user always wants the sidekick visible as part of a new-or-existing Agent
Team in the INVOKING session's panel — never only an invisible external tmux
process. Since cross-session team join does not exist (one team per session,
official docs; feature request anthropics/claude-code#24294), every /sidekick
spawn MUST use the hybrid pattern:

1. **Default worker = in-process teammate.** Spawn the durable worker as a
   named teammate of the invoking session's team (Agent tool,
   `name: sidekick-<mission-slug>`, `run_in_background: true`). It appears in
   the user's agent panel, is SendMessage-addressable, and joins the existing
   team if one is already live (one team per session — spawning adds to it).
2. **Durability layer stays on disk, not in the process.** The teammate
   checkpoints to the same branch/mission-scoped STATE.md after every step and
   the main session maintains a resumption bead (`br create`, P1) carrying:
   mission, ground truth, run IDs/SHAs, next actions, STATE.md path. Teammate
   death (session exit, quota, crash) = respawn from STATE.md + bead, exactly
   like a tmux respawn. In-process teammates are NOT restored by `/resume`
   (official limitation) — the bead + STATE.md ARE the restore path.
3. **tmux sidekick is the fallback, not the default.** Launch the external
   tmux variant ONLY when (a) the work must survive the invoking session
   ending (multi-day/overnight missions), or (b) Agent Teams is unavailable in
   the invoking harness. When you do, TELL the user it cannot appear in the
   team panel (platform limit) and give the exact attach command
   (`tmux attach -t sidekick-<mission-slug>`). Prefer INTERACTIVE (TUI) over
   `-p` for any tmux spawn the user may want to watch.
4. **Migration is cheap and allowed both directions.** tmux→teammate: send a
   stand-down directive (checkpoint + handoff entry in STATE.md, commit/push
   or revert uncommitted work, exit), then spawn the teammate pointing at the
   same STATE.md. teammate→tmux: same in reverse. Never run both writers on
   one mission concurrently (single-writer rule).

## Invocation

`/sidekick [sonnet|codex] [mission...]`

- `engine/model`: default is **claude with Sonnet**. `codex` selects the Codex
  CLI engine (below). Any other model only if the user explicitly asks in the
  current message.
- `mission`: freeform priorities. If omitted, resume whatever the state file says.

## Engines: claude (default) | codex — both verified 2026-07-10

The protocol (STATE.md, tmux, commit-often, respawn) is engine-agnostic. Only
the launch command and the between-run steering command differ.

**codex launch** (auth comes from `~/.codex` — no `CLAUDE_CONFIG_DIR` needed):

```bash
tmux new-session -d -s "$SESSION" -x 160 -y 48 \
  "cd '$PWD' && codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \"\$(cat '$STATE_DIR/sidekick.prompt.md')\"; rc=\$?; printf '\n[sidekick done exit=%s]\n' \"\$rc\"; exec bash"
```

Verify with `pgrep -fl "codex exec"`; unlike claude `-p`, codex exec streams
progress into the pane while working.

**Mode choice: `-p` (headless) vs interactive TUI — verified 2026-07-10.**
`-p` is the default for unattended batch missions (clean `[sidekick done
exit=]` marker, `-o`-style scripting), but it gets NO team primitives. For
missions that benefit from a REAL in-sidekick Claude team or live steering,
launch the interactive TUI in tmux instead:

```bash
tmux new-session -d -s "$SESSION" -x 200 -y 50 \
  "cd '$PWD' && CLAUDE_CONFIG_DIR='${CLAUDE_CONFIG_DIR:-$HOME/.claude}' CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions; exec bash"
```

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is REQUIRED for team formation —
  without it there are no teammate primitives to find.
- First run in a new directory shows a **trust dialog** — capture-pane, then
  `tmux send-keys -t "$SESSION" Enter` to accept before sending the mission.
- Deliver the mission as a pointer to STATE.md (single source of truth), with
  text and the submitting Enter as **separate** send-keys calls — an Enter
  bundled with the text gets swallowed by paste handling:
  ```bash
  tmux send-keys -t "$SESSION" "Read STATE.md in this directory and execute its Next Actions exactly."
  sleep 2 && tmux send-keys -t "$SESSION" Enter
  ```
- **Completion detection** (no exit marker in TUI mode): have the mission
  print a unique DONE token AND rewrite STATE.md's Next Actions to
  "(mission complete)". Gate on the STATE.md condition, not the pane alone —
  the mission text echoed in scrollback contains the same token and produces
  false-positive greps (hit live 2026-07-10). The STATE.md grep has the SAME
  trap: the mission description usually contains the literal string too, so
  use a full-line exact match (`grep -qx "(mission complete)"`) plus a
  deliverable-file existence check — never a plain substring grep (a
  supervisor false-positived on this live, 2026-07-10).
- **Collecting lane results**: teammates go `idle_notification` WITHOUT
  auto-delivering their findings — plain teammate output is not forwarded.
  The sidekick (team lead) must SendMessage-nudge each idle lane to get its
  report (verified live 2026-07-10).
- **Teardown** (the TUI never exits on its own):
  `tmux kill-session -t "$SESSION"` after verifying STATE.md shows
  "(mission complete)" and deliverables are on disk.
- **Verified capabilities in interactive mode (claude 2.1.197):** REAL named
  teammates form (Agent tool with `name`), SendMessage flows BOTH ways
  between the sidekick and its lanes, each teammate gets a tmux split pane
  (`--teammate-mode tmux` display), and the TUI shows a live team roster.
- **In-flight bidi:** `tmux send-keys` delivers live operator directives to a
  working TUI session (verified on both engines' TUIs) — richer than the
  `-p` STATE.md-checkpoint channel.
- Tradeoffs: no exit marker (see Completion detection + Teardown above), and
  an idle TUI session keeps holding its context.
- Codex interactive equivalent: `codex --dangerously-bypass-approvals-and-sandbox`
  (trust dialog too; note `--skip-git-repo-check` is exec-only and REJECTED by
  the TUI). Real `spawn_agent` multi-agent lanes verified in TUI mode via
  child rollouts carrying `parent_thread_id`.

**Bidirectional communication contract (both engines, empirically verified):**

- **While a run is in flight** — inbound: edit STATE.md (Standing rules / Next
  Actions); the sidekick re-reads it at every checkpoint. Outbound: STATE.md
  Progress Log + `tmux capture-pane`.
- **Between runs** — resume the sidekick's own session with a new directive
  (full conversation context is retained). Precondition: the prior process
  must have EXITED (pane shows `[sidekick done exit=...]` / no `pgrep` hit) —
  never fire `--resume`/`resume` at a still-running session; the in-flight
  channel is STATE.md, and resume-while-running risks a duplicate concurrent
  process on the same mission:
  - claude: `claude --model sonnet --dangerously-skip-permissions -p --resume <session-id> "<directive>"`
    — session id = newest `*.jsonl` under
    `$CLAUDE_CONFIG_DIR/projects/<cwd-slug>/`, where `<cwd-slug>` is the
    sidekick's working dir with every `/` replaced by `-`. macOS trap: `/tmp`
    resolves to `/private/tmp`, so the slug starts `-private-tmp-...`, not
    `-tmp-...` — looking up the naive slug finds nothing.
  - codex: `codex exec resume <session-id> "<directive>"` — `--last` also
    works but is GLOBAL across all codex sessions on the machine; never use
    `--last` when more than one codex mission may be live. Session-id
    discovery: codex prints `session id: <uuid>` in its startup banner —
    capture it from the pane right after spawn and record it in STATE.md.
    Fallback: `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-<ts>-<id>.jsonl`,
    BUT multi-agent child lanes write their own rollout files there seconds
    apart — resume the PARENT (the rollout with no `parent_thread_id` in its
    session_meta), never just the newest file (that may be a child lane).
  - Record the session id in STATE.md's Ground truth once known, so any future
    operator can steer without re-discovering it.
- **Lanes/teams inside the sidekick** — claude: Agent Teams when allowed (see
  Management section; empirically NOT available to `-p` sidekicks today —
  Agent-tool subagents are the working default). codex: native `multi_agent`
  support (stable; confirm on the host with
  `codex features list | grep multi_agent`); if unavailable, sequential
  sub-tasks with the fallback noted in STATE.md. Verifying a codex
  multi-agent claim: the pane rendering collapses tool calls and narrated
  paths can be embellished — cross-check `~/.codex/sessions` for child
  rollout files whose `parent_thread_id` equals the sidekick's session id;
  that filesystem evidence, not pane prose, is the proof.

## Core mechanics

**State file (per project + branch/mission):**
`/tmp/<project-slug>/sidekick/<branch-or-mission>/STATE.md` — `<project-slug>` is
the repo name for repo missions, or any stable slug for non-repo missions (e.g.
`/tmp/homelab-ops/sidekick/dashboard-watch/STATE.md`); `/` in branch names is
sanitized to `-`. Minimal skeleton (invent nothing else — deliverables go in a
subdir like `docs/`, since root-file-pollution guards on some machines block
writes next to STATE.md):

```markdown
# Sidekick STATE — <mission-slug>
## Mission
project-slug: <value>            (non-repo missions only)
<mission text>
## Ground truth
engine: claude|codex · session-id: <record after spawn> · key facts
## Standing rules
<mission-specific constraints>
## Progress Log
- (spawn) initial state written by main session
## Next Actions
1. <first step>
```

Scoping is MANDATORY — two sidekicks with different missions
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

1. Compute the slugs deterministically, then create the state dir:
   - **Project slug** = repo name for repo missions. For non-repo missions,
     pick a short 1–2 word topic identifier and write it verbatim as a
     `project-slug: <value>` line at the top of STATE.md's Mission section so
     a respawn can grep it back out instead of re-deriving it from memory.
   - **Mission slug** = the git branch name (`/`→`-`) when the mission is
     branch-scoped; otherwise the first 4–6 significant words of the mission
     text, lowercased, non-alphanumeric replaced with `-`, collapsed/trimmed,
     capped at ~40 chars. Must be reproducible from STATE.md on respawn.

   ```bash
   PROJECT_SLUG="<derived per above>"
   MISSION_SLUG="<derived per above>"
   STATE_DIR="/tmp/${PROJECT_SLUG}/sidekick/${MISSION_SLUG}"
   mkdir -p "$STATE_DIR"
   ```

   If `$STATE_DIR/STATE.md` exists, this is a RESPAWN: do not overwrite it; the
   new sidekick resumes from it. If missing, write initial STATE.md from current
   context (mission, ground truth, standing rules, next actions).

2. Write the startup prompt to a file next to STATE.md:

   ```bash
   cat > "$STATE_DIR/sidekick.prompt.md" <<'PROMPT'
   You are sidekick — the persistent, restartable Sonnet Claude Code teammate for
   this mission. The main session may crash; YOU are the durable worker.

   Model contract: you are running under `claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions`
   (or `codex exec --dangerously-bypass-approvals-and-sandbox` for the codex
   engine). Do not switch to another model unless the user explicitly approved
   it in the current mission.

   Startup protocol:
   1. Read STATE.md.
   2. Resume from Next Actions. Never redo logged steps.
   3. After every completed step, append Progress Log and rewrite Next Actions.
   4. Before exiting a completed mission, rewrite Next Actions to
      "(mission complete)" — never leave stale steps listed as if pending.

   Lane management (use ONLY the branch for your engine — the spawner must
   keep the matching branch and delete the other when writing this prompt):
   - claude engine: when your harness allows Agent Teams, run your fan-out
     lanes as a real Claude agent team (named teammates + task claims); if a
     team fails to form (teams under -p are undocumented), fall back to
     Agent-tool subagents and note it in STATE.md.
   - codex engine: use your native multi-agent capability to run lanes as
     parallel subagents; if unavailable, work sequentially and note it in
     STATE.md.
   Your operator steers you via STATE.md and tmux, not SendMessage — check
   STATE.md's Standing rules / Next Actions for new directives at every
   checkpoint.

   Recovery discipline, verbatim and non-negotiable:
   COMMIT OFTEN: commit + push after EVERY green unit of work. Never hold more
   than ~30 minutes of uncommitted changes. Include this instruction verbatim in
   every sub-agent prompt you write.

   Universal hard rules:
   - Irreversible/outward-facing actions (merges, deploys, deletions,
     publishing, sending messages to humans) are human-only unless explicitly
     pre-authorized.
   - Sign-off on any deliverable requires adversarial verification. Use another
     real sidekick-grade verifier on your own engine (claude: a Sonnet tmux
     Claude Code session; codex: a separate codex exec session), or a
     documented external CLI reviewer only if the user explicitly approved it.
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

3. Launch a real tmux session. The `cd` target is the mission's repo root for
   repo missions; for non-repo missions `cd "$STATE_DIR"` (that's where the
   mission's files live). Preconditions, in order:
   - **Directory check**: verify `$PWD` is the intended mission directory
     (`git rev-parse --show-toplevel` matches expectation, or the non-repo
     directory was explicitly chosen) — `--dangerously-skip-permissions`
     gives the sidekick unattended full-permission execution there for the
     mission's duration.
   - **Liveness gate before any kill**: never kill blind —
     ```bash
     SESSION="sidekick-${MISSION_SLUG}"
     if tmux has-session -t "$SESSION" 2>/dev/null; then
       tmux capture-pane -t "$SESSION" -p -S -20 | tail -20
       # If that output looks live/mid-task: STOP — steer the existing
       # sidekick (STATE.md / send-keys) or confirm with the user before
       # killing. Only kill a session whose pane shows it exited.
     fi
     ```

   ```bash
   tmux new-session -d -s "$SESSION" -x 160 -y 48 \
     "cd '$PWD' && CLAUDE_CONFIG_DIR='${CLAUDE_CONFIG_DIR:-$HOME/.claude}' claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p \"\$(cat '$STATE_DIR/sidekick.prompt.md')\"; rc=\$?; printf '\n[sidekick done exit=%s]\n' \"\$rc\"; exec bash"
   ```

   (Claude launch shown. For the **codex engine**, substitute the codex launch
   command from the Engines section — `CLAUDE_CONFIG_DIR` does not apply to
   codex; its auth comes from `~/.codex`.)

4. Verify the sidekick actually started before reporting success:

   ```bash
   tmux ls | grep "^${SESSION}:"
   tmux list-panes -a -F '#{session_name} #{pane_pid} #{pane_current_command}' \
     | grep "^${SESSION} "
   tmux capture-pane -t "$SESSION" -p -S -80 | tail -80
   pgrep -fl -- "--teammate-mode tmux"   # claude engine. ps may show the full
                                         # binary path, so match on the flag.
   pgrep -fl "codex exec"                # codex engine equivalent
   ```

   Multiple sidekicks routinely run on one machine — both pgrep patterns match
   ALL of them. Disambiguate YOURS by piping through
   `grep "$MISSION_SLUG"` (the slug appears in the launch command's cd path).

   Socket gotcha: `tmux` commands target the socket in `$TMUX` — a supervisor
   or verifier agent running inside a DIFFERENT tmux server (e.g. a swarm
   worker pane) will see zero sidekick sessions with plain `tmux ls`. Use
   `tmux -L default ls` (and `-L default` on capture-pane etc.) when checking
   from another tmux context; sidekicks live on the default socket.

   Note: in claude `-p` (print) mode the pane stays BLANK until the run
   finishes — an empty capture is not failure; liveness proof is the `pgrep`
   hit plus, later, STATE.md's Progress Log advancing. **Codex is the
   opposite**: `codex exec` streams progress into the pane while working, so
   a persistently blank pane on the codex engine IS a bad sign. A pane showing
   "You've hit your session limit" means a claude sidekick launched on a
   quota-exhausted account — check the auth env propagation above.

   If these checks do not show a real tmux session and a real Claude Code command,
   the sidekick did **not** start. Fix the tmux/Claude launch before doing any
   mission work.

## Respawn procedure

1. Locate the branch/mission-scoped STATE.md.
2. Do not rewrite it.
3. Reuse the existing `sidekick.prompt.md` if present; otherwise generate it from
   STATE.md using the template above — populate `<mission text>` with the
   verbatim contents of STATE.md's `## Mission` section, never from
   conversation memory (respawn implies no conversation context survived).
4. Launch `tmux new-session` with the same launch command the mission used
   originally — claude: the Sonnet command including the inline
   `CLAUDE_CONFIG_DIR` propagation (respawns from a fresh session are exactly
   when the tmux server's stale env bites); codex: the Engines-section codex
   command (no `CLAUDE_CONFIG_DIR`). STATE.md's Ground truth should record
   which engine the mission runs on.
5. Capture pane output to verify it read STATE.md and resumed from Next Actions.

## Milestone reporting

The main session polls the tmux pane (`capture-pane`) and STATE.md and relays
dense milestone updates — the sidekick cannot SendMessage the main session
(separate sessions, separate teams). The
sidekick itself writes durable state to STATE.md and git. A report is not valid
unless it includes proof: tmux capture, git status/log, PR/commit URL, or test
output.

## Stall watchdog (interactive TUI) — MANDATORY for supervisors

Interactive TUI sidekicks (and their teammate lanes) fail by **stalling alive**,
not by exiting: the session-limit modal (`/rate-limit-options`: wait / credits /
upgrade) blocks ALL work until a key is pressed and does NOT auto-dismiss when
the quota window resets. Real incident (2026-07-11): both sidekick leads AND all
their lane teammates froze 40+ min on this modal — including ~34 min AFTER the
limit reset — while a liveness+progress monitor (pgrep + STATE.md-growth) saw
nothing wrong, because the processes were alive and silence looks identical to
quiet work.

Rules for any supervisor of a TUI sidekick:

1. **Watch staleness, not just liveness.** Alarm when the mission STATE.md mtime
   exceeds ~15 min while the process is alive, then `capture-pane` and grep for
   the stall signatures: `session limit|rate-limit-options|Enter to confirm|Esc
   to cancel`. Escalate at ~45 min even with no signature (silent stall).
2. **Check EVERY teammate pane, not just the lead.** Quota limits are
   per-account (`CLAUDE_CONFIG_DIR`), so the lead and all lanes stall
   SIMULTANEOUSLY — un-sticking only the lead leaves the lanes frozen at their
   own modals (this exact miss cost 3 lane-hours on 2026-07-11). Enumerate panes
   via `tmux list-panes -t "$SESSION" -F '#{pane_id}'` and inspect each.
3. **Recovery**: `tmux send-keys -t <pane> Enter` (selects "Stop and wait" —
   resumes immediately if the window already reset; harmless no-op at an idle
   prompt), then send the lead a resume directive pointing at STATE.md and have
   it re-task idle lanes via SendMessage.
4. **`-p` sidekicks are the opposite**: they fail by exiting (`[sidekick done
   exit=N]` marker) — process-death monitors work there. Don't assume a monitor
   built for one engine mode covers the other.

## Why this beats main-session fan-outs

Main-session fan-outs die with the session and re-derive context on resume. The
sidekick externalizes ALL state to disk + git (frequent pushes), so recovery cost
is one tmux Sonnet Claude Code respawn. Parallel verifier lanes can still happen,
but they must be real Sonnet tmux Claude Code sessions unless the user explicitly
approves another model/tool for that mission.

## Drive-loop invariants (from PR #8292 retro, 2026-07-11)

1. **Endgame single-writer freeze.** When a PR enters its final green drive
   (all code review findings addressed, chasing CI/review convergence), ONE
   agent owns pushes. Before starting the endgame, check for co-writers
   (`git log` author cadence, FixPR automation comments, other sessions'
   uncommitted worktree state) and either take the lock (log it in STATE.md)
   or wait. A push landing mid-cycle costs the full serialized CI pyramid
   (~40 min) AND any live bot approval — PR #8292 lost a CodeRabbit APPROVED
   granted at 23:42Z to a 23:56Z sibling push and spent 4+ hours failing to
   re-obtain it.
2. **External-bot requests are once-per-head.** Before posting any bot
   re-request (`@coderabbitai full review`, Bugbot trigger), list existing
   request comments; if one already exists for the current head, DO NOT post
   another — duplicates escalate the bot's rate-limit window (observed:
   01:04Z + 01:19Z requests pushed CodeRabbit's window to 02:17Z, then
   silence). Re-request only after a genuinely new head or >2h of silence.
3. **Background waits need a deadman.** Any "poller/watcher will wake me"
   plan must include a second, independent check (main-session monitor, or
   an in-turn blocking until-loop instead of a background task). Two
   background pollers died silently on PR #8292, each costing ~1h of
   undetected idle. Prefer in-turn blocking polls only for waits under the
   Bash tool's hard cap (~10 min / 600s — a "blocking poll under 1h" is NOT
   executable in this harness, and the timeout-integrity rule caps all
   layers at 600s); anything longer MUST be a background task, and the
   spawner must record the expected wake-by time in STATE.md so anyone
   reading it can detect the miss (tracked structural fix: rev-nm314).
