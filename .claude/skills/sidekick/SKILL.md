---
name: sidekick
description: Spawn or respawn a persistent, crash-recoverable Sonnet sidekick for ANY long-running mission — PR/CI fleets, research sweeps, migrations, monitoring, ops runbooks, data pipelines, multi-day projects in any repo or no repo at all. The sidekick is ALWAYS a named in-session Claude Agent-Team teammate (model sonnet, SendMessage-addressable, visible in the user's panel) durable via STATE.md + a P1 resumption bead + commit-often. There is NO tmux mode and NO codex engine — external tmux sidekicks and -p print-mode sidekicks are banned. Use when the user says /sidekick, "respawn the sidekick", or wants long work to survive conversation crashes.
---

# Sidekick — persistent restartable Sonnet teammate (claude team ONLY)

One named Sonnet teammate owns long-running orchestration. The main session
supervises and relays milestones. If the conversation crashes, a fresh session
respawns the same named teammate and it resumes from a disk state file with
zero conversation context.

**Pattern origin:** [Devin Fusion](https://cognition.com/blog/devin-fusion) —
Cognition's hybrid-model harness that keeps frontier-level coding intelligence
while cutting costs with sidekick agents. Delegation split + cost goal adopted;
dynamic model routing is NOT (the sidekick model is fixed at spawn). Durability
(STATE.md + bead + commit-often) is this skill's own addition.

## The one and only mode — in-session Claude team teammate

The sidekick is a named in-process teammate of THIS session's Agent Team:

```
Agent({
  name: "sidekick-<mission-slug>",
  model: "sonnet",              // MANDATORY — see Model contract
  run_in_background: true,
  prompt: <startup prompt, template below>
})
```

- Visible in the user's team panel; SendMessage-addressable both ways.
- Durability is STATE.md + a P1 `br` resumption bead + commit-often — NOT the
  process. Teammates die with the conversation; that is accepted by design.
  Recovery = a fresh session respawns the same named teammate from
  STATE.md/bead. Multi-day/overnight missions survive as state on disk, not
  as a running process.
- Lanes the sidekick fans out are ALSO named teammates
  (`sidekick-<slug>-lane-<topic>`), each with an explicit `model` — never
  fire-and-forget `general-purpose` subagents wearing sidekick names.
- If Agent Teams fails to form in the current harness, fall back to a named
  background Agent-tool subagent (same name, same explicit `model:
  "sonnet"`, same STATE.md protocol) and record the fallback in STATE.md —
  never report lanes as "team-based" without proof a team formed, and never
  fall back to tmux.
- Wait for a teammate's shutdown to be confirmed before reusing its name —
  same-name respawn while a prior instance winds down spawns duplicate
  concurrent workers on the same mission.

Spawning the teammate is the FIRST action on any `/sidekick` invocation —
write/refresh STATE.md, create/refresh the resumption bead, then spawn. No
preflight questions.

## Banned patterns (do not reintroduce)

1. **External tmux sidekicks** (`tmux new-session ... claude ...` in any
   form). Removed 2026-07-18 by user directive: the sidekick is a claude
   team teammate only. Sessions named `sidekick-*` in tmux are legacy.
2. **`-p` print-mode sidekicks.** A `-p` process gets no Agent Teams
   primitives (verified claude 2.1.197, 2026-07-10), shows a blank
   unobservable pane, and needs an error-prone resume dance.
3. **Unconditional `CLAUDE_CONFIG_DIR` exports** in any claude launch —
   the `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` pattern explicitly exports the
   var via its `:-` default, which deterministically breaks OAuth on
   cmux-hosted machines even at the literal default value (reproduced 3-5x
   per variant, 2026-07-17/18). Probe-then-launch if a genuine multi-account
   override is ever needed outside this skill.
4. **Codex-engine sidekicks** (`codex exec` in tmux). Retired with the tmux
   mode; route codex work through AO / `/claw` instead.
5. **Model-less spawns.** See Model contract.

## Model contract — explicit `model` on EVERY spawn (hard rule)

Every sidekick spawn and every lane spawn MUST set `model` explicitly.
Omitting it silently inherits the session model (often Fable/top-tier) — a
policy violation, not a neutral default. Audit 2026-07-18 (bead jleechan-0020)
found real incidents: `sidekick-us-videos` ran on claude-fable-5 and
`sidekick-fix-health-check-green` on MiniMax-M3 purely because `model` was
omitted. The sidekick model is **sonnet**; any other model (including haiku
keepers) only if the user explicitly approved it in the current mission.

## Core mechanics

**State file (per project + branch/mission):**
`/tmp/<project-slug>/sidekick/<branch-or-mission>/STATE.md` — `<project-slug>`
is the repo name for repo missions, or any stable slug for non-repo missions;
`/` in branch names is sanitized to `-`. Minimal skeleton (invent nothing
else — deliverables go in a subdir like `docs/`, since root-file-pollution
guards on some machines block writes next to STATE.md):

```markdown
# Sidekick STATE — <mission-slug>
## Mission
project-slug: <value>            (non-repo missions only)
<mission text>
## Ground truth
model: sonnet · resumption-bead: <br id> · key facts
## Standing rules
<mission-specific constraints>
## Progress Log
- (spawn) initial state written by main session
## Next Actions
1. <first step>
```

Scoping is MANDATORY — two sidekicks with different missions sharing one
STATE.md clobber each other. For fleet-wide / cross-branch missions use a
mission slug instead of a branch name. Sections: Mission, Ground truth,
Standing rules, Progress Log (append-only, timestamped), Next Actions
(rewritten every step). This file IS the recovery mechanism.

**Legacy shared file:** if `/tmp/<repo>/sidekick/STATE.md` exists from an
older spawn, do NOT edit another mission's sections. Migrate only YOUR
mission's section into the new scoped path, leave a one-line pointer behind.

**Resumption bead:** on first spawn, `br create "sidekick: <mission-slug>"
--type task --priority 1 --description "<STATE.md path + mission one-liner>"`.
The bead is the cross-session discovery hook; STATE.md is the state. Close it
when the mission completes.

## 5-minute checkpoint cadence (mandatory)

The sidekick and every lane it owns checkpoint at a ≤5 min cadence:
1. STATE.md heartbeat — append a timestamped Progress Log line.
2. `br update`/`br sync` on the resumption bead — single-writer rule: only
   the sidekick (never lanes) writes the bead body, so concurrent lanes never
   clobber it.
3. Safe local commit — commit + push after every green unit of work; never
   hold >30 min uncommitted. Commit-safety escape hatch: on a dirty shared
   worktree use path-scoped `git add <files>` (never `git add -A`), a WIP
   branch, or an isolated state repo; state files under a gitignored `.tmp/`
   follow the same escape hatch.

## Spawn procedure (main session)

1. Compute slugs deterministically, then create the state dir:
   - **Project slug** = repo name for repo missions; for non-repo missions a
     short 1-2 word topic identifier, written verbatim as
     `project-slug: <value>` in STATE.md's Mission section.
   - **Mission slug** = git branch name (`/`→`-`) when branch-scoped;
     otherwise first 4-6 significant words of the mission text, lowercased,
     non-alphanumeric → `-`, capped ~40 chars. Must be reproducible from
     STATE.md on respawn.

   ```bash
   PROJECT_SLUG="<derived per above>"   # e.g. worldarchitect.ai
   MISSION_SLUG="<derived per above>"   # e.g. fleet-ci-health
   STATE_DIR="/tmp/${PROJECT_SLUG}/sidekick/${MISSION_SLUG}"
   mkdir -p "$STATE_DIR"
   ```

   If `$STATE_DIR/STATE.md` exists this is a RESPAWN: do not overwrite it.
   If missing, write initial STATE.md and create the resumption bead.

2. Write the startup prompt to `$STATE_DIR/sidekick.prompt.md` (kept on disk
   so a respawning session can reuse it verbatim):

   ```
   You are sidekick — the persistent, restartable Sonnet teammate for this
   mission. The main session may crash; YOUR STATE FILE is the durable record.

   Model contract: you run as model sonnet. Do not switch models. Every lane
   you spawn MUST set model explicitly (sonnet unless the user approved
   otherwise); an omitted model param is a policy violation.

   Startup protocol:
   1. Read STATE.md at <STATE_DIR>/STATE.md.
   2. Resume from Next Actions. Never redo logged steps.
   3. After every completed step, append Progress Log and rewrite Next Actions.
   4. Checkpoint every <=5 minutes: STATE.md heartbeat, bead update
      (single-writer), safe local commit.
   5. Before exiting a completed mission, rewrite Next Actions to
      "(mission complete)" and close the resumption bead.

   Lane management:
   - Run fan-out lanes as named teammates of your Agent Team (task claims +
     SendMessage), each with an explicit model param. If a team fails to
     form, fall back to named Agent-tool subagents (still explicit model)
     and record the fallback in STATE.md — never report lanes as
     "team-based" without proof a team formed. Never use tmux or external
     processes for lanes.
   Your operator steers you via SendMessage and STATE.md — check STATE.md
   Standing rules / Next Actions for new directives at every checkpoint.

   Recovery discipline, verbatim and non-negotiable:
   COMMIT OFTEN: commit + push after EVERY green unit of work. Never hold
   more than ~30 minutes of uncommitted changes. Include this instruction
   verbatim in every sub-agent prompt you write.

   Universal hard rules:
   - Irreversible/outward-facing actions (merges, deploys, deletions,
     publishing, sending messages to humans) are human-only unless
     explicitly pre-authorized.
   - Sign-off on any deliverable requires adversarial verification by a
     separate verifier lane (explicit model), or a documented external CLI
     reviewer only if the user explicitly approved it.
   - Re-check file overlap before every ready/green claim, not just at spawn.
   - Semantic contradiction is not a merge conflict; stop and flag the scope
     call instead of choosing one behavioral intent silently.
   - Quarantined or foreign uncommitted work in a shared-name worktree must
     not be touched. Do conflict resolution in a third fresh detached
     worktree.
   - statusCheckRollup / check-runs APIs can include stale attempts. Group by
     check name and use only the newest attempt's conclusion.
   - Batch independent CLI calls, but keep a single writer per mutable file.

   Mission:
   <mission text>
   ```

3. Spawn the teammate — `Agent({name: "sidekick-<mission-slug>", model:
   "sonnet", run_in_background: true, prompt: <the file's content>})`.

4. Verify before reporting success: the teammate appears in the team panel /
   task list, and STATE.md's Progress Log advances within the first
   checkpoint window. Record `resumption-bead` and any key facts in Ground
   truth. If the spawn did not produce a visible named teammate, the
   sidekick did NOT start — fix the spawn before doing any mission work.

## Respawn procedure

1. Locate the scoped STATE.md (via the resumption bead if the path is
   unknown). Do not rewrite it.
2. Reuse the existing `sidekick.prompt.md` if present; otherwise regenerate
   from STATE.md's `## Mission` section verbatim — never from conversation
   memory (respawn implies no conversation context survived).
3. Respawn the same named teammate (explicit `model: "sonnet"`). Confirm any
   prior same-name teammate is fully shut down first.
4. Verify it read STATE.md and resumed from Next Actions (panel + STATE.md
   Progress Log advancing).

## Milestone reporting

The sidekick SendMessages milestones; the main session relays them with
proof — STATE.md excerpt, git status/log, PR/commit URL, or test output. A
report is not valid without captured proof.

## Why this beats plain fan-outs

Anonymous fan-outs die with the session and re-derive context on resume. The
sidekick externalizes ALL state to disk + git (frequent pushes) + a bead, so
recovery cost is one named-teammate respawn from STATE.md. Verifier lanes are
teammates with explicit models — adversarial by assignment, cheap by routing,
and visible in the panel instead of buried in a task list.
