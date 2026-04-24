# Beads Issue Tracking - Your Project Reference

Beads CLI is **`br`** (`~/.local/bin/br`, beads-rs). The legacy **`bd`** binary is **not installed** on this system; use **`br`** everywhere. Optional shell convenience: `alias bd='br'` (see `~/.bashrc`).

Issues live under `.beads/` (JSONL + SQLite `beads.db`, gitignored). **`br` runs in direct mode** (no `bd` daemon / no `.beads/bd.sock`).

## Essential Commands

```bash
br list                              # List issues
br list -s in_progress               # Filter by status
br show REV-abc123                   # Show issue detail
br create "Fix the login bug" -d "…" # Create issue
br update REV-abc123 -s in_progress  # Progress
br close REV-abc123                  # Close issue
br search "keyword"                  # Full-text search
br stats                             # Project stats / health-style summary
br doctor                            # Diagnose / repair
```

## Status Values

`open` | `in_progress` | `blocked` | `done` | `closed` (use `br update -s …` / `br close`)

## Commit Convention

Reference beads in commit messages:

```
fix(auth): resolve JWT expiry edge case

REV-abc123
```

## Database Recovery ("no beads database found")

The SQLite DB (`beads.db`) is gitignored and can be recreated from JSONL.

**Fix:** run `br init` to rebuild from the committed JSONL:

```bash
br init       # rebuilds beads.db from .beads/issues.jsonl
br stats      # verify
```

Do **not** set `no-db: true` in `.beads/config.yaml` unless you want JSONL-only mode.

## Why the Pre-Commit Hook Sometimes Warns

Hooks that flush beads may run `br sync --flush-only`. If the DB is missing or busy, you may see a warning. This is usually **non-blocking**. Run `br init` or `br doctor` afterward if needed.

## Integrate.sh and Beads

`integrate.sh` may stop legacy bead daemons or remove sockets. Afterward, if beads commands fail, run `br init` and `br doctor`.

`integrate.sh --force` skips the expensive squash-merge detection for branches with >1000 commits (configurable via `FORCE_SQUASH_CHECK_MAX`).

## Config File: `.beads/config.yaml`

Key settings (uncomment to activate):

```yaml
issue-prefix: "REV"      # prefix for all issue IDs
sync-branch: "beads-sync" # git branch for beads commits
# no-db: false           # keep false to use SQLite (recommended)
```

## JSONL Sync

`.beads/issues.jsonl` is the source of truth committed to git. Always include `.beads/` changes in commits and PRs (per CLAUDE.md).

```bash
br sync --flush-only      # export DB → JSONL (common hook operation)
br sync --import-only     # import JSONL → DB
```

## Worktree Warning

Avoid staging `.worktrees/pr-*/` directories — git treats them as embedded repos and breaks `git stash`. If accidentally staged:

```bash
git rm --cached .worktrees/pr-5654
```

## Merge Conflict Prevention (union driver)

`.gitattributes` is configured with `merge=union` for `.beads/issues.jsonl`. This uses git's built-in union merge strategy which concatenates unique lines from both sides — no conflict markers ever, since each JSONL line is a self-contained record with a unique hash ID.

If you see merge conflicts in `.beads/issues.jsonl`, the union driver is not configured:

```bash
# Check
cat .gitattributes | grep beads
# Should show: .beads/issues.jsonl merge=union

# Fix if wrong
# Edit .gitattributes: change merge=beads to merge=union
# Remove the old custom driver:
git config --unset merge.beads.driver
```

## Working in Worktrees — Main Dir Drift

Each git worktree has its own `.beads/issues.jsonl`. Pre-commit automation may run `br sync --flush-only` and stage `.beads/issues.jsonl`.

If you work primarily in worktrees and the main repo dir shows `modified: .beads/issues.jsonl`, you can safely discard it:

```bash
git checkout -- .beads/issues.jsonl
```

The beads from your worktrees will merge to main when those PRs merge (via the union driver).
