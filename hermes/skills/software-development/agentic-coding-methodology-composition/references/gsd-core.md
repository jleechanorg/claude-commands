# GSD Core (formerly gsd-build/get-shit-done)

- **Author(s):** TÂCHES (and the open-gsd org)
- **Canonical source:** https://github.com/open-gsd/gsd-core (current repo as of 2026)
- **License:** MIT
- **Local install status:** Installed v1.9.0 (`--profile=full`) at `~/.claude/`, 71 `gsd-*` skills at `~/.claude/skills/gsd-*`, runtime marker `~/.claude/gsd-core/.gsd-runtime=claude`. Installed via `npx -y @opengsd/gsd-core@latest --claude --global`. **Lean re-install recommended** — see `--profile` pitfall below.
- **Repo history:** The original `gsd-build/get-shit-done` GitHub repo is archived and redirects to `open-gsd/gsd-core`. npm packages: `@opengsd/gsd-core` (current, v1.9.0 as of 2026-07-30) and `get-shit-done-cc` (legacy, 1.42.3).

## One-line positioning

A context-engineering + spec-driven development framework that defeats context rot via fresh-context subagents.

## Core question it asks

"How do we carry project/milestone/phase/verification state across many sessions without context bloat silently degrading the agent?"

## Pipeline / loop / workflow

```
Discuss          (capture implementation decisions via adaptive Q&A)
    ↓
UI design        (optional /gsd-ui-phase for visual phases)
    ↓
Plan             (research → decompose → verify plan fits fresh context window)
    ↓                (researcher + planner + plan-checker as fresh subagents)
Execute          (wave-based parallel subagents, each with clean 200k-token context)
    ↓
Verify           (walk through what was built; generate fix plans if discrepancies)
    ↓
Ship             (create PR, archive phase, repeat for next phase)
```

Six namespace routers sit above the core commands: `/gsd-workflow`, `/gsd-project`, `/gsd-quality`, `/gsd-context`, `/gsd-manage`, `/gsd-ideate`.

## Distinctive features (what it does that others don't)

- **Multi-session state continuity via `.planning/STATE.md`** — survives restarts.
- **Wave-based parallel execution across phases** — multiple PLAN.md files run in parallel waves where concerns don't overlap.
- **`/gsd-package-legitimacy-gate` (v1.42.1)** — `slopcheck install <pkg> --json` on every recommended package. Verdicts: `[SLOP]` (removed), `[SUS]` (human checkpoint), `[OK]` (approved), `[ASSUMED]` (WebSearch-sourced, same as SUS).
- **Reversibility-gates for one-way-door decisions** — by default, a `one-way` decision (data migration, broken contract, irreversible) earns a `checkpoint:decision` before the task that implements it. `--no-reversibility-gates` suppresses for unattended runs.
- **`--bounce` external plan validation** and `/gsd-plan-review-convergence` cross-AI plan convergence loop (max 3 cycles by default).
- **`/gsd-spec-phase` with Edge Coverage + Prohibition Coverage probes** — surfaces applicable boundary/empty/ordering/precision/idempotency/concurrency edges and unwritten must-NOT constraints.
- **`/gsd-ultraplan-phase` (BETA)** — offload planning to Claude Code's ultraplan cloud; review in browser; import back.
- **Tracer-first decomposition** — every plan leads with one production-quality end-to-end `tracer` slice that the executor verifies before any expansion task.

## Invocation model

**Mixed**. Namespace routers (`/gsd-workflow`, etc.) auto-fire; concrete commands (`/gsd-plan-phase`, `/gsd-execute-phase`) are user-invoked. Heavy skills declare `effort: max`; quick-status skills (`/gsd-progress`, `/gsd-stats`) declare `effort: low`.

## Artifact tree

```
.planning/
├── PROJECT.md              # project-wide context
├── REQUIREMENTS.md
├── ROADMAP.md              # milestones + phases
├── STATE.md                # navigation: where in the loop currently sits
├── config.json
├── research/
├── CLAUDE.md               # injected on next session
└── <phase>/
    ├── <phase>-SPEC.md              # from /gsd-spec-phase
    ├── <phase>-CONTEXT.md           # from /gsd-discuss-phase
    ├── <phase>-RESEARCH.md          # from /gsd-plan-phase
    ├── <phase>-<N>-PLAN.md          # from /gsd-plan-phase
    ├── <phase>-VALIDATION.md
    └── <phase>-VERIFICATION.md      # from /gsd-verify
```

## Multi-harness support

Claude Code, Codex, Antigravity CLI, Kimi CLI, Kilo, OpenCode, Copilot, Cursor, Windsurf. The installer is required — do not copy `agents/` or `commands/` files directly.

## Installation paths (verified)

```bash
# Universal (Node.js)
/usr/bin/env bash -c "$(curl -fsSL https://raw.githubusercontent.com/open-gsd/gsd-core/main/.bin/gsd-install.sh)"

# Or via npx (interactive — needs TTY for runtime/location prompts)
npx @opengsd/gsd-core@latest

# Non-interactive install for Claude Code globally (verified working)
npx -y @opengsd/gsd-core@latest --claude --global

# Lean install: profile=core (~700 tokens eager-load, no always-on hooks)
# profile values: core | standard | full (default). Comma-separated unions also valid.
npx -y @opengsd/gsd-core@latest --claude --global --profile=core

# Uninstall
npx -y @opengsd/gsd-core@latest --uninstall

# Onboarding an existing repo
/gsd-onboard                   # guided brownfield setup
/gsd-onboard --fast            # lightweight codebase mapping first

# Starting a new project
/gsd-new-project               # greenfield
/gsd-new-project --auto @prd.md   # auto-extract from PRD
```

### `--profile` selection (load-bearing)

The installer defaults to `--profile=full`, which **writes ~15 always-on hooks to `~/.claude/settings.json`** that fire on every Claude Code session. Verified live on 2026-07-30 against v1.9.0 — full install added these hooks without confirmation:

| Event | Hook |
|---|---|
| SessionStart | `gsd-check-update.js`, `gsd-session-state.sh` |
| Stop | `gsd-context-monitor.js` |
| PreToolUse | `gsd-prompt-guard.js`, `gsd-read-guard.js`, `gsd-workflow-guard.js`, `gsd-worktree-path-guard.js`, `gsd-validate-commit.sh` |
| PostToolUse | `gsd-context-monitor.js`, `gsd-read-injection-scanner.js`, `gsd-graphify-update.sh`, `gsd-phase-boundary.sh` |
| SubagentStop | `gsd-context-monitor.js` |
| PreCompact | `gsd-context-monitor.js` |
| FileChanged | `gsd-config-reload.js` |

`gsd-context-monitor` alone fires on Stop, PostToolUse, SubagentStop, AND PreCompact — basically always-on. This conflicts with "no default guidance" directives and may shadow other frameworks' session-bootstrap (e.g., Superpowers' `using-superpowers` HARD-GATE).

**Recommendation:** default to `--profile=core` (~700 tokens eager-load). `core` keeps the phase loop (`/gsd-new-project`, `/gsd-plan-phase`, `/gsd-execute-phase`, `/gsd-verify`) and drops most auto-firing hooks. Use `--profile=standard` (15 skills, ~700 desc tokens) if you want the review/debug/audit hooks without the kitchen-sink eager-load. Skip `full` unless the user explicitly asks for "everything."

## Known anti-patterns

- **Don't accept the `--profile=full` default when the user said "no default guidance."** Full installs ~15 always-on hooks to `settings.json`. Use `--profile=core` instead. See `--profile` selection above.
- **Don't copy `agents/` or `commands/` directly to your runtime.** Use the installer — it handles runtime-specific paths and naming (kebab-case for Claude Code, `$gsd-` prefix for Codex).
- **Don't pick phase scope that's too large.** "Build the authentication system" usually contains multiple independent concerns — split into multiple phases.
- **Don't skip the Discuss step to save time.** Without it, the planner guesses on library choices, error-handling strategy, etc. Minutes of discussion save hours of rework.
- **Don't run executors with accumulated session history.** The 200k-token fresh context is the mechanism, not a convenience.
- **Don't trust package recommendations without slopcheck.** As of v1.42.1, every recommended package goes through the package-legitimacy gate.

## Sources

- https://github.com/open-gsd/gsd-core (README, MIT, current)
- https://github.com/gsd-build/get-shit-done (archived redirect → open-gsd)
- https://www.npmjs.com/package/get-shit-done-cc (legacy npm)
- https://deepwiki.com/gsd-build/get-shit-done/4-command-reference (verified 2026-07-30)
- https://docs.plannotator.ai/compare/superpowers-vs-gsd (third-party comparison, reviewed 2026-07-30)
- https://www.pulumi.com/blog/claude-code-orchestration-frameworks/ (third-party comparison)