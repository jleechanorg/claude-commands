---
description: Repo-local /code-standards — review code, diffs, PRs, or proposed implementations against the user-wide standards (ZFC, ZFC leveling, root-cause-first) plus the ponytail (lazy senior dev) ladder. Bidirectional pointer to the user-scope command at ~/.claude/commands/code-standards.md.
type: quality
execution_mode: immediate
---

# /code-standards (your-project.com repo-local)

Marker: `WORLDARCHITECT_CODE_STANDARDS_COMMAND_V1`

> This is the **repo-local** `/code-standards` command for
> `$GITHUB_REPOSITORY`. It specializes the user-scope command at
> `~/.claude/commands/code-standards.md` (which is the source of truth for the
> four-lane workflow). The two are intentionally designed to co-exist — repo-local
> can add repo-specific behavior (the `/thermo` lane, the smoke-test marker) without
> forking the standards. **If the user-scope command is updated, mirror the
> changes here.**
>
> For repos that do NOT have a repo-local `.claude/commands/code-standards.md`,
> the user-scope copy is the fallback. Both stay loadable.

## Source skills (loaded by this command)

| Skill | Path |
|-------|------|
| Ponytail — lazy senior dev mode | `.claude/skills/ponytail/SKILL.md` (repo-local pointer; user-scope canonical: `~/.claude/skills/ponytail/SKILL.md`) |
| Zero-Framework Cognition (ZFC) | `~/.claude/skills/zero-framework-cognition/SKILL.md` |
| ZFC Leveling Roadmap | `~/.claude/skills/zfc-leveling-roadmap/SKILL.md` |
| Root-cause-first engineering | `~/.claude/skills/root-cause-first/SKILL.md` |
| Code Standards dispatch | `~/.claude/skills/code-standards/SKILL.md` |

`~/.claude/skills/ponytail/SKILL.md` is the canonical mirror of
[ponytail/.github/copilot-instructions.md](https://github.com/DietrichGebert/ponytail/blob/main/.github/copilot-instructions.md).
The same skill is mirrored at `~/.codex/skills/ponytail/SKILL.md` for Codex.

## Lanes dispatched

1. **Ponytail** — the lazy-senior-dev seven-rung ladder. Stops you from
   writing code that already exists in-tree, from adding a new dependency
   when stdlib or installed packages cover it, and from chasing abstractions
   that weren't requested. Mark intentional simplifications with a `ponytail:`
   comment. Loaded from `.claude/skills/ponytail/SKILL.md` (repo-local
   pointer file; canonical user-scope skill at `~/.claude/skills/ponytail/SKILL.md`).
2. **ZFC** — no keyword/regex/heuristic routing in application code. Delegate
   semantic decisions to a model.
3. **ZFC leveling** — for level-up work, the model picks the target level
   (do not derive primary availability from XP thresholds).
4. **Root-cause-first** — patch the upstream prompt/schema/agent first; only
   add backend enforcement as a narrow, logged invariant after documenting
   why prompt correction is insufficient.
5. **Repo-specific: `/thermo`** — when the change is non-trivial (production
   code, agent prompt, or scoring/leveling flow), dispatch the
   `thermo-nuclear-code-quality-review` subagent for an independent
   complexity / duplication / coupling review.

## Workflow

When invoked as `/code-standards <scope>` (or with no argument, against the
current diff/PR):

1. **Load ponytail first.** It is the *do* discipline. Read it, apply the
   seven-rung ladder to the proposed diff before any of the *check* lanes
   run.
2. **Define the review scope** from the command argument, or use the current
   diff / active PR context if no argument was supplied.
3. **Load the four user-scope source skills** by path and treat them as
   authoritative. Do not duplicate the standards into this command file.
4. **Dispatch or emulate the five independent review lanes.** Each lane
   must return either PASS with file/line evidence or FAIL with the exact
   location and required fix. Rationalizations are not evidence.
5. **Reconcile** the lane results into the report format defined in
   `~/.claude/skills/code-standards/SKILL.md`.
6. **Do not mark any lane skipped** unless this is the explicit `smoke-test`
   mode documented below.

## Smoke-test mode

If the argument contains `smoke-test`, do not dispatch review lanes and do
not edit files. Instead, report:

- that this command file loaded,
- this command file path (`$GITHUB_REPOSITORY/.claude/commands/code-standards.md`),
- the user-scope source command path (`~/.claude/commands/code-standards.md`),
- the ponytail skill path (`~/.claude/skills/ponytail/SKILL.md`),
- the marker for this revision (`WORLDARCHITECT_CODE_STANDARDS_COMMAND_V1`).

This lets a runner confirm the command is on PATH and loadable without paying
for a real review.

## Bidirectional pointer

This repo-local command MUST stay in sync with the user-scope command at
`~/.claude/commands/code-standards.md`. Concretely:

1. The user-scope command is the source of truth for the four-lane workflow.
   When the user-scope command adds or removes a lane, mirror the change here.
2. The ponytail skill at `~/.claude/skills/ponytail/SKILL.md` is always part
   of the review, not a per-repo choice. Loading it is a precondition, not
   a toggle.
3. This repo-local command may add repo-specific behavior (the `/thermo` lane,
   the `WORLDARCHITECT_CODE_STANDARDS_COMMAND_V1` marker) without forking the
   four-lane standards.
4. If a repo does not have its own `.claude/commands/code-standards.md`, the
   user-scope copy is loaded as the fallback.

## For Codex callers

`~/.codex/commands/code-standards.md` is the Codex-side dispatcher that
references the same user-scope source skills. Codex loaders resolve this
file through `~/.codex/skills/` discovery.
