# Superpowers

- **Author(s):** Jesse Vincent (obra), Prime Radiant Inc.
- **Canonical source:** https://github.com/obra/superpowers
- **License:** MIT
- **Local install status:** Installed v6.2.0 via `~/.claude/plugins/cache/superpowers-marketplace/superpowers/6.2.0` (Claude plugin marketplace). Mirror copies at `~/.claude/skills/superpowers-*` and `~/.claude/skills/tessl__*` (the latter is obra's newer naming convention).
- **Local install alias:** `/plugin install superpowers@claude-plugins-official` (official marketplace) OR `/plugin install superpowers@superpowers-marketplace` (obra's marketplace).

## One-line positioning

A complete software development methodology with mandatory skill enforcement.

## Core question it asks

"How do we ship from idea to a mergeable branch with discipline?"

## Pipeline / loop / workflow

```
using-superpowers (HARD-GATE bootstrap)
    ↓
brainstorming (Socratic design refinement — HARD-GATE: no code until design approved)
    ↓
using-git-worktrees (isolated workspace on new branch)
    ↓
writing-plans (2-5 min tasks with exact file paths and verification steps)
    ↓
test-driven-development (RED-GREEN-REFACTOR)
    ↓
subagent-driven-development OR executing-plans
    ↓   (two-stage review: spec compliance, then code quality)
requesting-code-review (between tasks)
    ↓
finishing-a-development-branch (verify → merge/PR/keep/discard)
```

## Distinctive features (what it does that others don't)

- **Mandatory skill invocation at session start.** `using-superpowers` injects a HARD-GATE: "if 1% chance a skill applies, you ABSOLUTELY MUST invoke it." No opt-out.
- **Test-Driven Development as a first-class skill**, not a recommendation.
- **Subagent-driven-development with two-stage review** (spec compliance → code quality).
- **`finishing-a-development-branch`** skill — explicit merge/PR/keep/discard decision flow.
- **`receiving-code-review`** skill — how to respond to feedback without defensiveness.
- **Multi-harness packaging** from day one — Claude Code, Codex, Cursor, OpenCode, Pi, Copilot CLI, Antigravity, Kimi CLI.

## Invocation model

**Auto-fire** (mandatory). The `using-superpowers` bootstrap fires on session start and at every meaningful boundary. `brainstorming` HARD-GATES implementation: no code until design approved.

## Artifact tree

```
docs/superpowers/specs/<feature>.md       # design doc (from brainstorming)
docs/superpowers/plans/<feature>.md      # implementation plan (from writing-plans)
<worktree-branch>                         # isolated workspace
```

## Multi-harness support

Claude Code, Codex CLI, Codex App, Cursor, Factory Droid, Gemini CLI, GitHub Copilot CLI, Kimi Code, OpenCode, Pi. Each install method differs; see official README.

## Installation paths (verified)

```bash
# Claude Code (official marketplace)
/plugin install superpowers@claude-plugins-official

# Claude Code (obra's marketplace)
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# Codex CLI
/plugins                                    # then search "superpowers" → Install Plugin

# OpenCode
# Tell OpenCode: "Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md"
```

## Known anti-patterns

- **Don't use `executing-plans` when subagents are available.** Per the skill itself: "If subagents are available, use superpowers:subagent-driven-development instead."
- **Don't skip the design approval gate.** `brainstorming`'s HARD-GATE is what makes the rest of the methodology work; bypassing it produces unreviewed plans.
- **Don't ignore telemetry concerns.** Superpowers loads a Prime Radiant logo for "version in use" telemetry by default. Set `SUPERPOWERS_DISABLE_TELEMETRY=1` to opt out, or honor Claude Code's `DISABLE_TELEMETRY`.
- **Don't double-write to GSD's `.planning/`** — Superpowers writes to `docs/superpowers/`. If you run both, designate one authoritative.

## Cross-references

- Local install log: see `~/.claude/projects/-Users-$USER/memory/feedback_2026-07-20_superpowers_cloud_build_install_and_differences.md` (superpowers-cloud-build plugin details; separate from this methodology).
- Local install log: `~/.claude/projects/-Users-$USER-wa-6292-fresh/memory/feedback_2026-05-26_obra-superpowers-integration.md` (obra/superpowers → your-project.com `/code-standards` skill integration).

## Sources

- https://github.com/obra/superpowers (README, MIT)
- https://blog.fsck.com/2025/10/09/superpowers/ (original release announcement)
- https://deepwiki.com/obra/superpowers (verified 2026-07-30)
- https://knightli.com/en/2026/05/15/obra-superpowers-agentic-skills-framework/ (verified 2026-07-30)
- https://docs.plannotator.ai/compare/superpowers-vs-gsd (third-party comparison, reviewed 2026-07-30)
- https://ryanuo.cc/en/posts/grill-me-vs-superpowers (third-party comparison, reviewed 2026-07-30)