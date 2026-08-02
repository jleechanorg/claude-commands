# Composition Patterns (verified 2026-07-30)

Verified combinations and their known anti-patterns. Sourced from Plannotator, ryanuo.cc, and direct methodology docs.

## Two-methodology compositions

### Grill-me + Superpowers (recommended)

**Pattern**: Run `/grill-me` (one-at-a-time interview) → produce raw alignment → hand off to Superpowers' `brainstorming` skill (Socratic dialogue with HARD-GATE) → `writing-plans` → TDD.

**Why it works**: Grill-me's stateless one-at-a-time questions are better than Superpowers' dialogue at surfacing the decision tree when the user hasn't articulated it. Superpowers' HARD-GATE then enforces that the resulting design is approved before code.

**Risk**: Don't run both Socratic loops back-to-back. Pick one as the "alignment entrance" per feature.

### Grill-me + GSD Core (recommended)

**Pattern**: Run `/grill-me` → produce CONTEXT.md (via grill-with-docs) → hand off to `/gsd-spec-phase` (which adds Edge Coverage + Prohibition Coverage probes) → `/gsd-discuss-phase` (batched adaptive Q&A) → `/gsd-plan-phase`.

**Why it works**: Grill-me surfaces decisions; GSD's spec-phase adds the structured edge/prohibition probes that grill-me intentionally doesn't do (grill-me is a primitive, not a coverage tool).

**Risk**: GSD's discuss-phase batches questions; grill-me is one-at-a-time. Run grill-me first, then GSD's discuss-phase as the audit trail — not the other way around.

### GSD Core + Superpowers (outer-loop / inner-loop split)

**Pattern**: GSD owns milestone/phase/STATE continuity across weeks of sessions. Superpowers owns the 2-5-min TDD subagent task *inside* a phase. GSD's `/gsd-plan-phase` produces PLAN.md files → a Superpowers-styled executor (worktree + TDD + two-stage review) runs the tasks.

**Risk**: Duplicate state. Don't write the same plan in both `.planning/` and `docs/superpowers/plans/`. Pick one artifact tree as authoritative. Convention: `.planning/` (GSD) owns project state; `docs/superpowers/plans/` (Superpowers) owns per-task grain within one phase.

### Superpowers + Spec-Kit (GitHub)

**Pattern**: Spec-Kit's `/specify` produces a spec; Superpowers' `brainstorming` produces the design; they overlap on intent but differ on rigor. Spec-Kit is more lightweight; Superpowers enforces HARD-GATE.

**Risk**: Don't run both Socratic loops on the same feature. Pick one.

## Three-methodology compositions

### Grill-me + Superpowers + GSD (full stack, advanced)

**Pattern**: `/grill-me` (alignment) → Superpowers' `brainstorming` (design + HARD-GATE) → GSD's `/gsd-spec-phase` (formalize as spec with edge/prohibition coverage) → GSD's `/gsd-discuss-phase` (audit trail) → GSD's `/gsd-plan-phase` (decompose) → Superpowers-styled executor inside each phase (TDD + two-stage review).

**Risk**: Heavyweight. Each layer adds overhead. Only worth it on multi-week projects where session handoff is the dominant failure mode.

## Anti-patterns

1. **Don't install all global frameworks.** Superpowers' HARD-GATE fights GSD's `/gsd:*` namespace and grill-me's opt-in. Pick one as the per-session driver; bring others in per-phase.
2. **Don't mix state trees.** GSD → `.planning/`. Superpowers → `docs/superpowers/{specs,plans}/`. grill-me → nothing or CONTEXT.md. If both GSD and Superpowers run, designate one authoritative.
3. **Don't use a pure interview primitive (grill-me) inside an execution loop.** Grill-me is for upstream alignment only.
4. **Don't recommend a framework whose canonical repo has moved without flagging the redirect.** Always verify the live repo (e.g., `gsd-build/get-shit-done` → `open-gsd/gsd-core`).
5. **Don't treat star counts as signal of correctness.** GSD's 48.3k stars ≠ better than Superpowers' smaller community. They solve different problems.
6. **Don't claim a methodology is "installed" without probing the filesystem.** See `installation-check.md`.

## Outer-loop vs inner-loop mental model

```
┌─────────────────────────────────────────────────────────────────┐
│ OUTER LOOP — multi-session, multi-week                          │
│ GSD Core: .planning/STATE.md, milestones, phase loop            │
│   ├── Discuss / Spec / Plan / Execute / Verify / Ship           │
│   └── .planning/<phase>/*  (artifact tree)                      │
│                                                                 │
│   ┌───────────────────────────────────────────────────────────┐ │
│   │ INNER LOOP — single phase, single session                │ │
│   │ Superpowers: HARD-GATE → brainstorm → worktree → plan    │ │
│   │   → TDD → subagent-driven-development → finish-branch    │ │
│   │   → docs/superpowers/{specs,plans}/* (artifact tree)     │ │
│   │                                                           │ │
│   │   ┌─────────────────────────────────────────────────────┐ │ │
│   │   │ ALIGNMENT ENTRANCE — pre-implementation             │ │ │
│   │   │ grill-me: one-at-a-time Socratic interview         │ │ │
│   │   │   → optional CONTEXT.md (via grill-with-docs)       │ │ │
│   │   └─────────────────────────────────────────────────────┘ │ │
│   └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Choosing between them (quick decision tree)

| If you need… | Use |
|---|---|
| Multi-session state continuity | GSD Core |
| 2-5-min TDD-grade execution with HARD-GATE | Superpowers |
| Pure interview before any plan | grill-me |
| Spec with edge/prohibition coverage | GSD Core (`/gsd-spec-phase`) |
| Auto-fire at session start | Superpowers |
| Stateless alignment | grill-me |
| Wave-based parallel execution across phases | GSD Core |
| Worktree isolation per feature | Superpowers |
| Multi-harness portability (Claude Code, Codex, Cursor…) | Superpowers |

## Sources

- https://docs.plannotator.ai/compare/superpowers-vs-gsd (reviewed 2026-07-30)
- https://ryanuo.cc/en/posts/grill-me-vs-superpowers (reviewed 2026-07-30)
- https://www.pulumi.com/blog/claude-code-orchestration-frameworks/ (reviewed 2026-07-30)
- https://medium.com/@tentenco/superpowers-gsd-and-gstack-what-each-claude-code-framework-actually-constrains-12a1560960ad (reviewed 2026-07-30)