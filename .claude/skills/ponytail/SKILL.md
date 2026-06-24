---
name: ponytail
description: Lazy senior-dev mode — the seven-rung ladder that decides whether to write code at all, whether to reuse code that already exists, and whether to prefer stdlib/platform/installed deps over a new dependency. Use before writing any code, every PR diff, every fix, every feature. Source attribution included.
source: https://github.com/DietrichGebert/ponytail/blob/main/.github/copilot-instructions.md
---

# Ponytail — Lazy Senior Dev Mode

> "The best code is the code never written."
> — Dietrich Gebert's [ponytail](https://github.com/DietrichGebert/ponytail) `.github/copilot-instructions.md`, adapted as a Claude/Codex skill.

**Lazy means efficient, not careless.** Before writing any code, stop at the first rung that holds.

## The seven-rung ladder

Run these in order, AFTER you understand the problem — not instead of it. Read the task, trace the real flow end-to-end, then climb.

1. **Does this need to be built at all?** (YAGNI)
2. **Does it already exist in this codebase?** Reuse the helper, util, or pattern that's already here. Don't re-write it.
3. **Does the standard library already do this?** Use it.
4. **Does a native platform feature cover it?** Use it.
5. **Does an already-installed dependency solve it?** Use it.
6. **Can this be one line?** Make it one line.
7. **Only then:** write the minimum code that works.

The ladder runs *after* you understand the problem. A small diff you don't understand is just laziness dressed up as efficiency — a second bug in a smaller package.

## Bug fix = root cause, not symptom

A report names a **symptom**. Find the shared function, fix it once.

- Grep every caller of the function you touch.
- One guard at the shared function is a smaller diff than one guard per caller.
- Patching only the path the ticket names leaves a sibling caller still broken.

This is the same discipline as `~/.claude/skills/root-cause-first/SKILL.md` — patch the upstream cause, not the surface symptom.

## Hard rules

- **No abstractions that weren't explicitly requested.** Boring over clever. Fewest files possible.
- **No new dependency if it can be avoided.** Reuse what's installed first.
- **No boilerplate nobody asked for.** Deletion over addition.
- **Shortest working diff wins** — but only once you understand the problem. The smallest change in the wrong place isn't lazy, it's a second bug.
- **Question complex requests.** "Do you actually need X, or does Y cover it?"
- **Pick the edge-case-correct option** when two stdlib approaches are the same size. Lazy means *less code*, not the *flimsier* algorithm.
- **Mark intentional simplifications** with a `ponytail:` comment. If the shortcut has a known ceiling (global lock, O(n²) scan, naive heuristic), the comment names the ceiling and the upgrade path.

## Not lazy about

You stay rigorous on:

- **Understanding the problem** — read it fully, trace the real flow before picking a rung.
- **Input validation at trust boundaries.**
- **Error handling that prevents data loss.**
- **Security and accessibility.**
- **Hardware calibration** — the platform is never the spec ideal. A clock drifts. A sensor reads off.
- **Anything explicitly requested.**

## Lazy code without its check is unfinished

Non-trivial logic leaves **ONE runnable check** behind:

- The smallest thing that fails if the logic breaks.
- An assert-based demo / self-check, OR one small test file.
- No frameworks, no fixtures.

Trivial one-liners need no test.

## When to load this skill

Load `ponytail` BEFORE:

- Writing any new function, helper, or module.
- Picking a dependency.
- Adding a layer of indirection.
- Starting a PR diff.
- Touching a function more than one caller depends on.

If you find yourself reaching for a new dependency, abstraction, or framework — re-read rung 2 ("already in this codebase?") before rung 5 ("already-installed dependency?"). Order matters: in-tree reuse beats a new package.

## Origin and attribution

- Source: <https://github.com/DietrichGebert/ponytail/blob/main/.github/copilot-instructions.md>
- License: see the upstream repo.
- Local copy also exposed to Codex at `~/.codex/skills/ponytail/SKILL.md`.

## Related skills (read alongside)

- `~/.claude/skills/root-cause-first/SKILL.md` — patch the upstream cause, not the symptom. Ponytail's "fix the shared function once" rule and root-cause-first are two sides of the same coin.
- `~/.claude/skills/zero-framework-cognition/SKILL.md` — never invent heuristic/keyword/regex classification; delegate to a model. Complements ponytail's "no abstractions that weren't asked for."
- `~/.claude/skills/code-centralization/SKILL.md` — prefer one source of truth over scattered projections. Ponytail rung 2 ("reuse what's here") lives here.
- `~/.claude/skills/code-standards/SKILL.md` — dispatch adversarial review lanes (ZFC, ZFC-leveling, root-cause-first). Ponytail is the *do* discipline; code-standards is the *check* discipline.
