---
name: beads-issue-tracking
description: Use when creating, claiming, updating, listing, syncing, or closing repository issues with the br CLI.
---

# Beads Issue Tracking

`br` is the canonical issue-tracking CLI. Do not use `bd`.

## Core Commands

```bash
br ready --json
br list --status open --json
br show <id> --json
br create "Title" --description "Context and acceptance criteria" --priority 1
br update <id> --claim
br update <id> --status in_progress
br close <id> --reason "Completed and verified"
```

Use `br --no-auto-flush ...` in a feature worktree when the task must not
export shared JSONL incidentally. Run `br sync --status` before changing sync
state. `br sync` never runs git commands; stage issue artifacts explicitly
when they belong to the current change.

Read `br <command> --help` before encoding flags in another skill or command.
Do not hand-edit the database or invent an issue ID.
