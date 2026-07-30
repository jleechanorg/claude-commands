---
name: nextsteps
description: Situational assessment, beads + ~/roadmap sync after a work block; optional brief from user. Default mode reads only beads + ~/roadmap (lean). `--full` preserves the legacy all-source behavior (Claude auto-memory, mem0, GH Issues).
---

# /nextsteps — Situational Assessment & Roadmap Update

## Modes

`/nextsteps` has **two modes**:

| Mode | Invocation | Sources read | Side effects written |
|------|------------|--------------|----------------------|
| **default** (lean) | `/nextsteps` or `/nextsteps [brief]` | beads (`br list`/`br show`) + `~/roadmap/` + `roadmap/README.md` | nextsteps `.md` doc + `br` updates + `roadmap/README.md` rolling activity + `~/roadmap/learnings-YYYY-MM.md` |
| **`--full`** | `/nextsteps --full` or `/nextsteps --full [brief]` | everything in default + Claude auto-memory + mem0 | everything in default + Claude auto-memory writes + `MEMORY.md` pointers + `mem0_shared_client.py add` + GitHub Issue creation |

**Default mode skips these phases on purpose** (they are owned by `--full`):

- Phase 4 — Write to Claude auto-memory
- Phase 5 — Save to mem0
- Phase 7b — Create or update GitHub Issues

If the user wants the side-effecting phases, they must invoke
`/nextsteps --full`.

This file is the **shorter, user-scope protocol**; keep it in user scope so
`/nextsteps` is reproducible across repos. The full canonical version with the
fail-closed rule, doc discovery, phase detail, and `--full` mode parsing
lives at `~/.claude/skills/nextsteps/SKILL.md`.

## When invoked (default mode — lean)

1. **Gather context in parallel**
   - `git log --oneline -10`
   - `br list --status open` (or `bd` if project uses bd)
   - `ls roadmap/` (or list `roadmap/README.md` recent section)
   - Use any user-provided line after `/nextsteps` as extra context.
   - `ls ~/roadmap/` (home docs)

2. **Assess**
   - Match recent commits to open beads; close or update status.
   - Note gaps → new `br create` issues.
   - Update `roadmap/README.md` **Recent activity (rolling)** with date + bullets.

3. **Execute**
   - Prefer parallel tasks (subagents) for: beads updates, new issues, roadmap edits.
   - **Do NOT** write Claude auto-memory files (Phase 4 — `--full` only).
   - **Do NOT** call `mem0_shared_client.py` (Phase 5 — `--full` only).
   - **Do NOT** run `gh issue create` for new beads (Phase 7b — `--full` only).

4. **Report**
   - First line: `Mode: default (beads + ~/roadmap)` (or `--full` variant if applicable).
   - Then: IDs, paths changed, recommended next actions.

## When invoked (`--full` mode — legacy all-source)

Run **everything in the default mode above**, plus:

- **Phase 4 — Write to Claude auto-memory** for each learning/finding (`~/.claude/projects/<key>/memory/*.md` + `MEMORY.md` pointers).
- **Phase 5 — Save to mem0** via `python3 ~/.hermes/scripts/mem0_shared_client.py add ...`.
- **Phase 7b — Create or update GitHub Issues** for each new bead via `gh issue create`.

First line of the report: `Mode: --full (beads + ~/roadmap + Claude memory + mem0 + GH Issues)`.

## If `~/.claude/skills/nextsteps/SKILL.md` is missing

This file is the protocol; keep it in user scope so `/nextsteps` is reproducible across repos.
reate (parallel subagents)
For each identified update, dispatch in parallel:

**Beads updates** (for each relevant open issue):
```bash
br update <id> --status <new_status>
br show <id>  # verify before updating
```

**New beads issues** (for gaps not tracked):
```bash
br create "<title>" --type <task|bug|feature|chore> --priority <0-4> --description "<details>"
```

**Roadmap doc updates** (edit existing `roadmap/*.md`):
- Add new decisions, findings, or status to relevant docs
- Keep updates concise — append, don't rewrite

**New roadmap docs** (for new initiatives):
- Create `roadmap/<TOPIC>.md` following existing doc style
- Include: Background, Current Status, Next Steps, Open Questions

### Phase 3 — Report
Summarize:
- Issues updated/created (with IDs)
- Docs updated/created (with paths)
- Recommended next actions
