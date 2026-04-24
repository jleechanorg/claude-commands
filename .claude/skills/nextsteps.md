---
name: nextsteps
description: Situational assessment, beads + roadmap sync after a work block; optional brief from user.
---

# /nextsteps — Situational Assessment & Roadmap Update

## When invoked

1. **Gather context in parallel**
   - `git log --oneline -10`
   - `br list --status open` (or `bd` if project uses bd)
   - `ls roadmap/` (or list `roadmap/README.md` recent section)
   - Use any user-provided line after `/nextsteps` as extra context.

2. **Assess**
   - Match recent commits to open beads; close or update status.
   - Note gaps → new `br create` issues.
   - Update `roadmap/README.md` **Recent activity (rolling)** with date + bullets.

3. **Execute**
   - Prefer parallel tasks (subagents) for: beads updates, new issues, roadmap edits.
   - **User learnings log:** before appending to `$HOME/roadmap/learnings-<YYYY-MM>.md`, run `mkdir -p "$HOME/roadmap"` (directory may not exist on fresh machines).
   - **Claude auto-memory:** before writing under `$HOME/.claude/projects/<project_key>/memory/`, run `mkdir -p` on that directory. Full step-by-step: `~/.claude/skills/nextsteps/SKILL.md`.

4. **Report**
   - IDs, paths changed, recommended next actions.

## Optional: parallel subagents

For each identified update, dispatch in parallel:

**Beads updates** (for each relevant open issue):
```bash
bd update <id> --status <new_status>
bd show <id>  # verify before updating
```
(Use `br` if that is the project’s CLI.)

**New beads issues** (for gaps not tracked):
```bash
bd create "<title>" ...
```

**Roadmap doc updates** (edit existing repo `roadmap/*.md`):
- Add new decisions, findings, or status to relevant docs
- Keep updates concise — append, don't rewrite

**New roadmap docs** (for new initiatives):
- Create `roadmap/<TOPIC>.md` following existing doc style
- Include: Background, Current Status, Next Steps, Open Questions

### Report

Summarize:
- Issues updated/created (with IDs)
- Docs updated/created (with paths)
- `~/roadmap/learnings-*.md` and memory files touched
- Recommended next actions
