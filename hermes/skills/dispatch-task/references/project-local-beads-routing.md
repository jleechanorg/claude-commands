# Project-Local `.beads/` Routing — Why `br show` Says "not found" After a Dispatch

## Symptom

After `ao spawn` for a project repo (e.g. `jleechanorg/jleechanclaw`, `$GITHUB_REPOSITORY`), `br show <bead-id>` from any random CWD returns:

```
Error: Issue not found: <bead-id>
Hint: Run 'br list' to see available issues.
```

…but the bead clearly exists — the worker has been writing to it for minutes, and `br update` from the same CWD silently no-ops because the bead is in a different database. This is a real split-brain: gateway-side cron/supervisor reads from one DB; the worker writes to another.

## Cause

The `br` CLI is workspace-bound. It looks for `.beads/` (or `beads.db` + `issues.jsonl`) in:
1. `$BEADS_DIR` env var
2. `./.beads/` relative to current directory
3. `git rev-parse --show-toplevel` + `./.beads/`
4. `~/roadmap/.beads/` (global default)

When a project repo (`jleechanclaw`, `your-project.com`, etc.) is registered with `agento` / AO, the worker's dispatch path may create a **project-local** `.beads/` directory inside the repo (`$HOME/repos/<repo>/.beads/`) and route all bead writes through that DB. The worker (which `cd`s into the worktree at `<repo>`) writes to the project-local DB; the gateway (which runs from `~/roadmap` or `$HOME`) looks at the central DB. Bead read/write calls from the wrong CWD silently miss each other.

**Real-world repro (2026-07-31, cron verification of bead `orch-klw` in thread `C09GRLXF9GR/1785429018.170719`):**

```
$ cd ~/roadmap && br show orch-klw
Error: Issue not found: orch-klw
$ grep -c "orch-klw" ~/roadmap/.beads/issues.jsonl
0

$ cd $HOME/repos/jleechanclaw && br show orch-klw
✓ orch-klw · Merge PR #792: durable bug-hunt harness (fix daily 0/0/0/0 misreport)   [● P1 · CLOSED]
Owner: $USER · Type: task
Created: 2026-07-31 · Updated: 2026-07-31
Labels: bug-hunt, jleechanclaw, merge
Closed: 2026-07-31 (Merged PR #792)
...
```

The bead was created in `$HOME/repos/jleechanclaw/.beads/issues.jsonl` (project-local), not in `~/roadmap/.beads/issues.jsonl` (central). The dispatch-task SKILL.md's "claim or create the bead" step warns about ID-format (`$USER-XXXX` vs `rev-XXXX`) but does NOT warn about DB routing — which is exactly the gap that bit the cron.

## Where project-local `.beads/` lives (verified 2026-07-31)

For each jleechanorg project repo known to be using project-local beads:
- `$HOME/repos/jleechanclaw/.beads/` — DB: `beads.db`, JSONL: `issues.jsonl` — registered for AGENT-RUNNING dispatches targeting PRs in `jleechanorg/jleechanclaw`
- `$HOME/repos/your-project.com/.beads/` — same pattern for `$GITHUB_REPOSITORY`

If you `cd` into one of those repos, `br show`, `br list`, and `br update` automatically target the local `.beads/`. If you `cd ~/roadmap` (or any other CWD), `br` falls back to `~/roadmap/.beads/` (or your env-default global).

The AGENTS-on-record claim is that `~/roadmap/.beads/` is canonical. In practice, AGENT-RUNNING dispatchers often have to `cd` to the repo to see the bead they just created.

## Diagnostic Recipe (when `br show <id>` says "not found")

1. **List every `.beads/` directory you suspect might own the bead**:
   ```bash
   for d in ~/roadmap $HOME/repos/*/; do
     [ -d "$d/.beads" ] && echo "==> $d/.beads ($(ls -1 "$d/.beads" | wc -l) files)"
   done
   ```

2. **Grep all `issues.jsonl` files for the bead ID**:
   ```bash
   for f in ~/roadmap/.beads/issues.jsonl $HOME/repos/*/.beads/issues.jsonl; do
     hits=$(grep -c "$BEAD_ID" "$f" 2>/dev/null || echo 0)
     [ "$hits" -gt 0 ] && echo "FOUND ($hits matches): $f"
   done
   ```

3. **Once located, `cd` into the owning repo and use `br` natively**:
   ```bash
   cd $HOME/repos/jleechanclaw && br show orch-klw
   cd $HOME/repos/jleechanclaw && br list --status closed | grep orch-klw
   ```

4. **Check the SQLite DB directly if `br` CLI is being weird** (the JSONL is a shadow file; SQLite is the source of truth at runtime):
   ```bash
   sqlite3 $HOME/repos/<repo>/.beads/beads.db \
     "SELECT id, status, closed_at, close_reason FROM issues WHERE id='<bead>';"
   ```

5. **Do NOT issue `br update` from `~/roadmap`** if the bead lives in a project-local DB — your update silently lands in the central DB and goes nowhere. Always `cd $HOME/repos/<repo>` first.

## Why this happens (root cause)

AGENT-RUNNING dispatchers (the orchestrator that handles `ao spawn`) may auto-create a project-local `.beads/` to keep bead operations co-located with the repo's git state. This avoids cross-repo `br` locking and keeps the canonical bead state in the same repo the worker is committing to. But the gateway-side cron / supervisor that monitors the bead runs from `~/roadmap` (the canonical AGENTS.md location) and looks at `~/roadmap/.beads/`.

The split-brain is intentional for lock-isolation; the cost is that any code path that does `br show <id>` from a non-repo CWD has to discover the DB location.

## Cron brief authors — fix at the source

**The "verify and close bead" cron instructions in task briefs assume the central DB is canonical, which is wrong for project-local beads.** Cron authors should specify the repo (e.g. "verify bead `orch-klw` in `$HOME/repos/jleechanclaw/.beads/`") to skip the diagnostic sweep. If the brief doesn't specify, follow the diagnostic recipe above before declaring the bead missing.

## Cron-specific recipe (the "verify and close" trap)

Cron jobs often say: "If complete, verify and close bead; otherwise report current state." When the bead lives in a project-local DB and the cron runs from `~/roadmap`:

1. **Run the diagnostic sweep** (steps 1-4 above).
2. **Read the bead status** from the project-local DB.
3. **If already closed**, the close-step is a no-op: don't pretend to close it. Report the current state (closed_at + close_reason).
4. **If still open**, `cd $HOME/repos/<repo>` first, THEN `br close <id>`. Issuing `br close` from the wrong CWD creates an orphan record in the central DB.

## Verified

2026-07-31, cron-fired status check for `jleechanclaw-31` / bead `orch-klw`. First `br show orch-klw` from `~/roadmap` returned "not found"; diagnostic sweep located the bead in `$HOME/repos/jleechanclaw/.beads/issues.jsonl` (and `beads.db`); `br show` from the repo returned "CLOSED 2026-07-31 (Merged PR #792)" confirming the worker had already closed it. Cron's "verify and close bead" instruction's close-step was correctly a no-op. No fix needed beyond making the routing explicit in this skill.
