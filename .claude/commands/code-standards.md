---
description: "User-scope /code-standards — review code, diffs, PRs, or proposed implementations against the user-wide standards: ZFC, ZFC leveling, root-cause-first, and the ponytail (lazy senior dev) ladder. Same skill family lives at `~/.claude/skills/code-standards/SKILL.md`."
type: quality
execution_mode: immediate
---

# /code-standards [scope]

> This is the **user-scope** `/code-standards` command, at
> `~/.claude/commands/code-standards.md`, so every repo — including ones
> without a repo-local `.claude/commands/code-standards.md` — can invoke the
> same review lanes against the same source skills. **If a repo-local
> `.claude/commands/code-standards.md` exists, prefer it.**

Read `~/.claude/skills/code-standards/SKILL.md` and execute the full
four-lane workflow (ponytail, ZFC, ZFC leveling, root-cause-first) against
`<scope>`, or the current diff/PR if no scope is given.

## Quick reference

| Lane | Skill |
|---|---|
| Ponytail (do discipline) | `~/.claude/skills/ponytail/SKILL.md` |
| ZFC | `~/.claude/skills/zero-framework-cognition/SKILL.md` |
| ZFC leveling | `~/.claude/skills/zfc-leveling-roadmap/SKILL.md` |
| Root-cause-first | `~/.claude/skills/root-cause-first/SKILL.md` |

## Flags

- `smoke-test` — load-only check; reports command/skill paths and revision
  marker without dispatching review lanes or editing files.

## Examples

```
/code-standards
/code-standards $PROJECT_ROOT/rewards_engine.py
/code-standards smoke-test
```
