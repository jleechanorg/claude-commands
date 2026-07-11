---
name: sidekick
description: Spawn or respawn a persistent, crash-recoverable sidekick in tmux (claude Sonnet by default, codex engine supported) for ANY long-running mission — PR/CI fleets, research sweeps, migrations, monitoring, ops runbooks, data pipelines, multi-day projects in any repo or no repo at all — with disk-checkpointed state and commit-often discipline. Main-session control channel is STATE.md + tmux (the sidekick is its own session — NOT SendMessage-addressable); INTERACTIVE (TUI) sidekicks run their lanes as a real Claude team, while -p sidekicks always fall back to Agent-tool subagents; main-session supervision teammates are team-managed. Use when the user says /sidekick, "respawn the sidekick", or wants long work to survive conversation crashes.
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

## Why this beats main-session fan-outs

Main-session fan-outs die with the session and re-derive context on resume. The
sidekick externalizes ALL state to disk + git (frequent pushes), so recovery cost
is one tmux Sonnet Claude Code respawn. Parallel verifier lanes can still happen,
but they must be real Sonnet tmux Claude Code sessions unless the user explicitly
approves another model/tool for that mission.
