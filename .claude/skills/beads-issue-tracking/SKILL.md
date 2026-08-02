---
name: beads-issue-tracking
description: Use when creating, querying, updating, closing, syncing, or diagnosing Beads issues with the br CLI.
---

# Beads issue tracking (`br`)

`br` (`beads_rust`) is the supported issue tracker. Never use the retired `bd` CLI and never read `.beads/*.jsonl` directly.

## Essential commands

```bash
br list --status open
br list --status open --json
br show REV-demo
br search "keyword" --status open --label bug
br create "Fix login bug" --type bug --priority 2 --description "Provenance: file:line, repro, or URL"
br update REV-demo --status in_progress
br close REV-demo --reason "Fixed and verified"
br stats
```

Use `br close`, not `br update --status closed`; the update command rejects terminal states so close-policy and dependency rewiring run.

## Operating contract

- `beads.db` is the primary working store; `br` is the only supported read/write interface.
- `.beads/issues.jsonl` is the version-controlled interchange/export. Do not edit or inspect it directly.
- Default to creating a bead for sourced follow-up work, regressions, flaky behavior, harness gaps, cross-session debt, and review leftovers.
- Do not create one for an unsourced idea or a trivial sub-two-minute fix already in flight.
- Include provenance in `--description`; close with `--reason`; reopen a failed fix with `br reopen <id>`.
- Reference the bead ID in related commits and PR artifacts.

## Sync and diagnosis

```bash
br sync --status
br sync --flush-only
br sync --import-only
br doctor --robot-triage
br doctor --quick
```

`br sync` never runs Git commands. Export/import guards protect against empty, stale, conflicted, or malformed data. Do not use `--force`, `--repair`, or `--bypass-policy` without first reading the matching command help and inspecting the proposed scope.

For machine-readable contracts, run `br capabilities`, `br schema`, or `br robot-docs guide`. Treat live `br <command> --help` as authoritative when this reference and the installed version differ.

## Worktrees and conflicts

Each worktree has its own checked-out `.beads/issues.jsonl`, while the database location depends on workspace discovery. Use `br where` before diagnosis. Do not discard or stage another worktree's Beads state by assumption.

If JSONL has merge conflicts, stop and inspect repository policy; do not hand-edit records or install a merge driver from this reference. Resolve through the repository's Beads workflow and validate with `br sync --status` plus `br doctor --quick`.
