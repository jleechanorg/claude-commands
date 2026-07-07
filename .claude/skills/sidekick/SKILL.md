---
name: sidekick
description: Spawn or respawn a persistent, crash-recoverable orchestrator teammate (Devin-sidekick pattern) that owns ANY long-running mission — PR/CI fleets, research sweeps, migrations, monitoring, ops runbooks, data pipelines, multi-day projects in any repo or no repo at all — with disk-checkpointed state and commit-often discipline. Use when the user says /sidekick, "respawn the sidekick", or wants long work to survive conversation crashes.
---

# Sidekick — persistent restartable orchestrator (general purpose)

One named background teammate owns all long-running orchestration. The main session only supervises. If the conversation crashes, a fresh session respawns the sidekick and it resumes from a disk state file with zero conversation context.

**Domain-agnostic.** The sidekick pattern is about durability, not PRs: any mission that outlives a conversation qualifies — driving PR fleets, multi-hour research/audit sweeps, code migrations, infra monitoring, ops incident runbooks, data pipeline babysitting, cross-repo refactors, or non-repo work entirely (e.g. "watch these dashboards and escalate"). Repo-specific rules live in a mission adapter (below), never in the core protocol.

## Invocation

`/sidekick [model] [mission...]`

- `model`: `fable` | `sonnet` | `haiku` (default `sonnet`; user saying "fable sidekick" = fable)
- `mission`: freeform priorities. If omitted, resume whatever the state file says.

## Core mechanics

**State file (per project + branch/mission):** `/tmp/<project-slug>/sidekick/<branch-or-mission>/STATE.md` — `<project-slug>` is the repo name for repo missions, or any stable slug for non-repo missions (e.g. `/tmp/homelab-ops/sidekick/dashboard-watch/STATE.md`); `/` in branch names sanitized to `-`. Scoping is MANDATORY — two sidekicks with different missions sharing one STATE.md clobber each other's Mission/Next Actions (observed 2026-07-06: retro sidekick overwrote fleet sidekick's live plan; recovered only because the clobber was caught in review). For fleet-wide / cross-branch missions, use a mission slug instead of a branch name (e.g. `/tmp/<repo>/sidekick/fleet-ci-health/STATE.md`). Sections: Mission, Ground truth, Standing rules, Progress Log (append-only, timestamped), Next Actions (rewritten every step). This file IS the recovery mechanism.

**Legacy shared file:** if `/tmp/<repo>/sidekick/STATE.md` exists from an older spawn, do NOT edit another mission's sections in it. Migrate only YOUR mission's section into the new branch-scoped path, leave a one-line pointer behind, and never touch the rest.

**Spawn procedure (main session):**
1. `mkdir -p` the state dir. If STATE.md exists → this is a RESPAWN: do not overwrite it; the new sidekick resumes from it. If missing → write initial STATE.md from current context (mission, ground truth, next actions).
2. Create shared tasks via TaskCreate for each mission lane (skip on respawn if tasks exist — check TaskList).
3. Spawn via Agent tool: `name: "sidekick"` (or `"<model>-sidekick"` if replacing a live one), chosen `model`, `run_in_background: true`, prompt built from the template below.
4. Relay sidekick milestone messages to the user as they arrive.

**Replace/restart a live sidekick:** SendMessage a `shutdown_request` (reason: "being replaced; flush progress to STATE.md first"), then spawn the successor under a fresh name. Dead sidekick (crash): just spawn again — STATE.md has everything.

## Spawn prompt template

The sidekick prompt MUST contain these blocks (adapt mission/repo specifics):

- **Identity**: "You are <name> — the persistent, restartable orchestrator for <mission/project> (Devin-sidekick pattern). The main session may crash; YOU are the durable worker."
- **Token economy** (fable/opus only): reserve self for orchestration/diagnosis/synthesis; delegate mechanical work to sonnet/haiku background sub-agents; never spawn fable sub-agents.
- **Quota-preservation routing** (when Claude quota is constrained — 5hr window running out): route work to EXTERNAL-CLI subagents that burn zero Claude quota — **codex** (`codex exec --yolo`, or codex-pair-coder/codex-pair-verifier agent types) for hard/medium tasks (implementation, debugging, adversarial review); **minimax** (minimax-pair-coder/verifier agent types, or `claudem` wrapper = Claude CLI on MiniMax backend) for easy/mechanical tasks (rebases, description edits, status sweeps, file moves). Claude sonnet/haiku only where session-context judgment is required; the sidekick itself stays Claude for orchestration.
- **Startup protocol**: (1) Read STATE.md, resume from Next Actions, never redo logged steps; (2) TaskList → claim tasks with TaskUpdate(owner=<name>).
- **Recovery discipline** (verbatim, non-negotiable): "COMMIT OFTEN: commit + push after EVERY green unit of work. Never hold more than ~30 minutes of uncommitted changes. Include this instruction verbatim in every sub-agent prompt you write." Plus: update STATE.md after every completed step (append Progress Log, rewrite Next Actions); SendMessage(to="main") on each milestone.
- **Universal hard rules** (every mission, any domain): irreversible/outward-facing actions (merges, deploys, deletions, publishing, sending messages to humans) are human-only unless explicitly pre-authorized — flag them to main instead; **sign-off on any deliverable requires an adversarial subagent review** — spawn an independent verifier (codex CLI via codex-pair-verifier/codex-consultant, or a sonnet skeptic) prompted to REFUTE readiness; deliverables are flagged ready only with the verdict attached (PASS or explicitly-dismissed findings); batch independent CLI calls; check resource overlap before parallel lanes (single-writer rule for any shared mutable artifact).
- **Mission adapter** (include only rules relevant to THIS mission's domain — your-project.com repo example): never `gh pr merge` (human-only literal MERGE APPROVED); never force-push; git worktrees for branch work with identity check ($USER_NAME) + upstream set; `br` CLI only for beads (`--no-auto-flush` on branches); CI status via `gh pr view N --json statusCheckRollup` JSON never grep; gh REST/GraphQL are separate rate-limit buckets. For other repos/domains, write the adapter from that project's CLAUDE.md/policies.
- **Mission**: the prioritized lanes from the user.
- **Pacing**: work continuously; if blocked on all fronts, write STATE.md, message main the blocker, end turn.
- **Closing**: "Your final message goes to main, not the user — make it a dense status report. Begin now with the startup protocol."

## Restart one-liner (for the user, after a crash)

In any new session: "respawn the sidekick from /tmp/<project>/sidekick/<branch-or-mission>/STATE.md" — main reads nothing else; the spawn prompt's startup protocol does the recovery.

## Why this beats main-session Workflow fan-outs

Workflow runs die with the session and re-derive context on resume. The sidekick externalizes ALL state to disk + git (frequent pushes), so recovery cost is one Agent spawn. Sub-agent fan-outs still happen — inside the sidekick, cost-routed to sonnet/haiku.
