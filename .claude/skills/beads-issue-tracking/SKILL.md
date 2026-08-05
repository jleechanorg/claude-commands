---
name: beads-issue-tracking
description: Beads (`br`) issue tracking — command reference, proactive bead creation triggers, and close/reopen discipline. Cross-project single source of truth pointed to by ~/.claude/CLAUDE.md and CLAUDE-global-reference.md.
---

# Beads Issue Tracking — `br` CLI Reference (cross-project)

Beads is the agent-first git-native issue tracker: `.beads/issues.jsonl` (version-controlled source of truth) + a SQLite cache. The CLI is **`br`** — the older `bd` CLI is retired; never use it, and never read `.beads/*.jsonl` raw in any repo (`beads.db` is the primary store and `br` exposes it fully).

## Essential commands (verified against br 0.2.16)

```bash
br show <id>                          # single bead detail (--json for machine use)
br search <term>                      # full-text search; --status, --label filters
br list --status open --json          # filtered lists in JSON
br ready                              # open, unblocked, not deferred — what to work on
br create "<title>" --type task|bug|chore --priority 0..4 --description "<provenance>"
br q "<title>"                        # quick capture, prints ID only
br close <id> --reason "..."          # close when the work lands
br reopen <id>                        # or: br update <id> --status open
br update <id> --notes "..."          # REPLACES notes (no native --append in 0.2.16:
                                      #   read via `br show <id> --json`, concatenate, write back)
br sync                               # sync DB <-> JSONL only — does NOT edit bead bodies
br doctor                             # diagnostics + optional repair
br init                               # (re)build workspace from committed JSONL
```

Also available: `blocked`, `count`, `dep` (dependencies), `label`, `epic`, `defer`, `delete` (tombstone), `graph`, `robot-docs`. Run `br --help` for the full set — do not guess flags.

## Proactive bead creation — don't wait to be asked

Default is CREATE, not ask: never pause to request permission before opening a bead — creation is the default action; silently dropping discovered work is the only real failure mode. A false positive costs one `br close`; a dropped item costs a full re-discovery later. When work surfaces during a session that the user did not explicitly request but is clearly part of the same effort, create a bead immediately. Concrete triggers (not exhaustive):

- **Follow-up work** — bug discovered while fixing another bug, refactor opportunity, missing test coverage, missing doc.
- **Regressions / flaky behavior** — anything that smells like a non-deterministic failure, even if the current task passes.
- **Harness / infra gaps** — same manual cleanup done twice, env-var dance repeated, missing launcher/script.
- **Cross-session debt** — TODO / FIXME / XXX / "we should..." comments spotted while reading code.
- **PR review leftovers** — drive-by nits the PR owner did not address, missing labels, stale threads.

Do **not** create beads for trivial <2-min tasks already in flight or ideas with zero provenance — everything else, create it.

## Provenance + lifecycle discipline

- **Cite the source** in every description (file:line, log line, PR comment URL, test name, session date) so future agents can verify and close without re-investigating.
- Close (`br close <id> --reason "..."`) when the work lands; reopen if a fix attempt actually fails — never leave stale "closed" beads on real defects.
- Single-writer rule for shared mission beads: one agent owns the bead body; concurrent lanes report to the owner instead of writing.

## Repo-level notes

`.beads/issues.jsonl` merges via git's `merge=union` driver (each line is a self-contained record with a unique ID — no conflict markers). Worktrees each carry their own copy; beads ride along with code commits via the pre-commit flush hook where installed. Repo-specific daemon/config details belong in that repo's own docs, not here.
