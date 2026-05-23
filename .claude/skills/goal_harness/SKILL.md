---
name: goal_harness
description: "Goal-driven harness loop — keep working on a goal until /es, /er, /code_standards, and Codex plugin review all pass. All gates use adversarial subagents. Alias: /h"
---

# /goal_harness Skill

## Purpose

Iterative goal-driven development with a 4-gate adversarial quality harness.
The primary agent works on a goal, then validates the work through independent
adversarial subagents that evaluate against specific standards.

Define a goal and iterate until 4 adversarial gates all pass:

1. `/es` — Evidence Standards
2. `/er` — Evidence Review
3. `/code_standards` — ZFC + ZFC-leveling + root-cause-first (3 lanes)
4. Independent Agent review — independent diff review

## When to Use

- After implementing a feature or fix, before declaring done
- When code quality must be independently verified
- As the final step in `/converge` (the convergence loop)
- When `/es` and `/er` must both pass before merging

## Gate Details

### Gate 1: /es (Evidence Standards)

Subagent (via the `Agent` tool) reads both evidence-standards skill layers and evaluates the diff and evidence artifacts.
Returns: PASS / WARN / FAIL with file:line evidence.

### Gate 2: /er (Evidence Review)

Subagent (via the `Agent` tool) runs evidence-review + evidence-standards synthesis against the **diff and evidence artifacts** (not the raw goal text).
Subagent reviews: Map claims → artifacts, rate STRONG/WEAK/MISSING.
Verdict: PASS / WARN / PARTIAL / FAIL / INCONCLUSIVE.

Normalization rule: WARN → PASS (document warnings). PARTIAL → FAIL (gaps remain). INCONCLUSIVE → FAIL (cannot confirm).

### Gate 3: /code_standards (3 parallel adversarial lanes)

| Lane | Skill Path | Checks |
|------|-----------|--------|
| ZFC | `~/.claude/skills/zero-framework-cognition/SKILL.md` | No keyword routing, heuristic scoring, regex intent |
| ZFC-leveling | `~/.claude/skills/zfc-leveling-roadmap/SKILL.md` | Level-up fields, modal scoping, stale flag guards |
| Root-cause-first | `~/.claude/skills/root-cause-first/SKILL.md` | Root cause documented before adding protections |

Dispatch all 3 in parallel. Any lane FAIL → overall /code_standards FAIL.

### Gate 4: Independent Agent Review

Independent subagent reviews the full diff as a code reviewer.
Looks for: bugs, anti-patterns, missing tests, security issues, dead code.
Returns PASS or FAIL with file:line evidence.

### Verdict Normalization

| Raw verdict | Normalized | Harness treatment |
|-------------|------------|-------------------|
| PASS | PASS | Gate passes |
| WARN | PASS | Gate passes (document warnings) |
| PARTIAL | FAIL | Gate fails — evidence gaps remain |
| INCONCLUSIVE | FAIL | Gate fails — cannot confirm |

## Convergence

- **4/4 PASS** (after normalization) → CONVERGED. Work is harness-verified.
- **Any normalized-FAIL** → fix blockers, increment, loop.
- **Max iterations (10)** → stop with partial report.
- **Same score 2x** → STALLED. Stop and report.

## Subagent Isolation Rules

- Never skip a gate
- Never weaken a subagent's FAIL verdict
- Subagents are adversarial: only standard + diff, no primary agent optimism
- 3 /code_standards lanes run in parallel when possible
- Independent review must not share context with primary agent's own review

## Environment Detection

When running in cmux (background/scheduled mode):
- Use `scripts/goalexec-loop.sh` for terminal-based loops (canonical)
- Use `scripts/goalexec-loop-cmux.sh` for cmux-aware loops (canonical)
- `scripts/goal-loop.sh` and `scripts/goal-loop-cmux.sh` are legacy aliases
- State directory: `~/.goal-loop/`

## Related Commands

- `/goal` — builtin Claude Code goal command
- `/es` — Evidence Standards (reference/display)
- `/er` — Evidence Review (adversarial synthesis)
- `/code_standards` — Coding standards dispatch (ZFC + ZFC-leveling + root-cause-first)
- `/converge` — Iterative goal achievement loop (formerly `/goalexec`)
- `/converge_define` — Define-only variant
