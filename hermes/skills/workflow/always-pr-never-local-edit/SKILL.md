---
name: always-pr-never-local-edit
version: 1.0.0
description: Never just make local edits and stop. Always create a GH issue + bead, dispatch via ao spawn for a PR, and skillify the pattern. Local exploration is fine; local edits without a PR are a process violation.
---

# always-pr-never-local-edit

## Trigger
Any time you find yourself editing files locally (outside an ao worktree) without a PR in progress.

## Rule

**NEVER make local edits and stop.** Every change that modifies source must end with a PR. The workflow is:

1. **Investigate locally** — read files, search code, understand the problem. This is fine.
2. **Create GH issue + bead** — `gh issue create` + `br create`. Mandatory before any edits.
3. **Dispatch via `ao spawn`** — let the worker do the edits in its own worktree and create a PR.
4. **Skillify the pattern** — if you learned something reusable, create/update a skill.

### What counts as "local edits and stop"
- Editing files in the main checkout without pushing or creating a PR
- Making code changes in a session that ends without a PR URL
- Investigating, finding the fix, applying it locally, then telling the user "done" with no PR

### What's allowed locally
- Read-only exploration: `search_files`, `read_file`, `grep`, `git log`, `gh` queries
- Writing temporary files (scripts, tests) that you run and discard
- Creating issues, beads, cron jobs, memory entries

## Why

Local edits in the main checkout:
- Create drift between main and production
- Can't be reviewed or rolled back
- Get lost when the next checkout overwrites them
- Bypass CI and evidence standards

A PR is the minimum unit of done-ness. No PR = not done.

## Skillifying the pattern

When `/skillify` is requested, create a **general** skill — not one specific to the current project or file. Ask: "Would this pattern apply the same way in any repo?" If yes, make it general.

Examples:
- ✅ `always-pr-never-local-edit` — general workflow pattern
- ❌ `campaign-field-editability` — too specific to one project's one feature

If the pattern has reusable project-specific details (file paths, class names), put those in the GH issue or memory, not in the skill.

## Recovery

If you catch yourself making local edits:
1. Stop immediately
2. `git stash` or `git checkout -- .` to undo
3. Create the GH issue + bead
4. Dispatch via `ao spawn` with the full task description
5. Don't resume local edits