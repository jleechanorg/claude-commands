# ao spawn INTERNAL_ERROR leaving orphan idle session records (2026-07-21)

Verified against `$GITHUB_REPOSITORY` PR [#8462](https://github.com/$GITHUB_REPOSITORY/pull/8462) on 2026-07-21 PT. The dispatcher (gateway session) was attempting to drive a recurring `is_test IS NULL` BQ alert fix into a worker.

## Symptom signature

`ao spawn` exits non-zero with:

```
Internal server error (INTERNAL_ERROR) [request <hostname>/<req-id>]
```

…but the broker has already written a session row. Three signals confirm the orphan row:

1. `ao session ls --project <p>` shows a new row with `[no_signal] worker` matching the spawn's `--name` (the broker allocates the row before launching tmux).
2. `ao session get <id> --project <p> --json` returns:
   ```json
   {"session": {"id": "<id>", "kind": "worker", "harness": "<harness>",
                "displayName": "<name>", "activity": {"state": "idle"},
                "isTerminated": false, "createdAt": "...", "updatedAt": "...",
                "status": "no_signal"}}
   ```
3. `tmux list-sessions | grep <id>` returns nothing — the tmux pane never materialized, so no worker ever ran.

In one session, three spawn attempts produced request IDs `12wNaBr5kL-001401`, `12wNaBr5kL-001408`, `12wNaBr5kL-001439`; each one created an orphan row (`worldarchitect-83`, `worldarchitect-84`, `worldarchitect-85`). A fourth retry on a sibling PR (`worldarchitect-86`) had the same shape.

## Why it matters

- The 20-slot broker cap counts orphan rows against future spawns. With 4 leaks on one project, the next legitimate dispatch can hit "Spawn rejected: 20 active sessions >= cap" even though zero sessions are actually working.
- The orphaned rows look healthy to `ao status` / `ao session ls` (correct session name, harness, project). An operator scanning the dashboard assumes "work is in flight" while no PR is being driven.
- `ao session cleanup` does NOT reap rows where the worker never produced a PR or bead — it only cleans sessions with merged/closed PRs. So the orphan rows persist indefinitely.

## Verified recovery recipe

```bash
# 1. Verify daemon health (don't trust INTERNAL_ERROR alone)
ao status  # expect: healthz: ok, readyz: ready

# 2. List candidate orphan rows for the dispatch's --name
ao session ls --project worldarchitect 2>&1 | grep -E "bq-8462|worldarchitect-83|worldarchitect-84|worldarchitect-85|worldarchitect-86"

# 3. Confirm row state via JSON (not just ls output)
ao session get worldarchitect-83 --project worldarchitect --json | python3 -c '
import json, sys
s = json.load(sys.stdin)["session"]
assert not s["isTerminated"], "row already terminated"
assert s["activity"]["state"] in ("idle", "spawning"), "unexpected activity state"
'

# 4. Kill orphan rows (preserves worktree so future retries can reuse it)
for sid in worldarchitect-83 worldarchitect-84 worldarchitect-85 worldarchitect-86; do
  ao session kill "$sid" --project worldarchitect
done

# 5. Verify cleanup
for sid in worldarchitect-83 worldarchitect-84 worldarchitect-85 worldarchitect-86; do
  ao session get "$sid" --project worldarchitect --json | python3 -c '
import json, sys
s = json.load(sys.stdin)["session"]
assert s["isTerminated"] and s["activity"]["state"] == "exited"
print("OK", s["id"])
'
done

# 6. Try a different harness BEFORE giving up (cheap, isolates the failure)
ao spawn --project worldarchitect --claim-pr 8462 \
  --harness claude-code --name bq-8462 \
  --prompt '...'   # still likely fails if the broker is the bug, but isolates harness-vs-broker

# 7. Cap retries at 2 (one per harness family). After 2 INTERNAL_ERRORs with
#    daemon healthy, file a bead and surface the verified blocker.
```

## Why `--skip-agent-check` did NOT help in this incident

Adding `--skip-agent-check` to the same project + harness returned the same `Internal server error (INTERNAL_ERROR)` response (request ID `12wNaBr5kL-001439`). The `ao spawn --help` flag description is "Skip advisory agent catalog install/auth preflight before spawning" — i.e. it skips the catalog/auth preflight, not the broker transaction. If the failure is broker-side (which the request-ID pattern strongly suggests), `--skip-agent-check` does not bypass it.

## Detection rules for future dispatches

When dispatching via `ao spawn`:

1. **Track request IDs from the gateway session start.** Every `Internal server error` line carries one. If you see 2+ from the same project with the daemon healthy, treat it as a broker incident, not a transient failure.
2. **Compare session counts before and after each spawn.** `ao session ls --project <p> | wc -l` after a failed spawn should equal the count before. If it grew by 1, an orphan row was created — kill it before retrying.
3. **Cross-check the broker's `[no_signal]` rows against the tmux pane list.** Orphan rows = `[no_signal]` rows that have no corresponding `tmux list-sessions` entry.
4. **If the broker cap rejects with "20 active sessions >= cap"** but `tmux list-sessions | grep wa-` shows nothing, the cap is full of orphans — reap them with `ao session kill <id>` one at a time (the documented "20-slot cliff with stuck `[spawning]` zombies" recipe applies to orphans too).

## Where this lives in the dispatcher surface

- **Skill update:** `dispatch-task` SKILL.md gains the §"Pitfall — INTERNAL_ERROR leaves orphan idle sessions" section, plus a one-line pointer in the Notes block. The headline rule — "Cap retries at 2; after 2 INTERNAL_ERRORs with healthy daemon, surface the verified blocker to the user instead of fabricating 'work is in progress'" — captures the most important dispatcher-side decision rule from this incident.
- **Bead filed:** `bd-udmo` (priority 1, type=bug, labels=`ao,spawn,orphan-session`) — fix the broker transaction so failed spawns roll back session records and return actionable diagnostics instead of leaking orphan rows.
- **End-state preserved:** PR [#8462](https://github.com/$GITHUB_REPOSITORY/pull/8462) left untouched at head `66d6d68dbf8f3fe57b9eac3b335b8c3db60a859e` (mergeable=true, mergeable_state=unstable). The dispatcher surfaced the verified blocker rather than claiming a worker was running.

## Cross-reference

- `~/.hermes/skills/finish-the-job` — "60-min clarify silence is not a license to stop pushing" + "User instruction conflicts with ground-truth repo state — pause and surface data before destructive action" — both apply when the dispatch path is blocked but the user has framed the task as "just do it."
- `~/.hermes/skills/agento` — Per-project concurrent-spawn lock + spawn-recovery ladder. The recovery ladder's "running.json bootstrap" recipe handles "lifecycle polling is inactive", not "INTERNAL_ERROR" — they are different failure modes.
- `~/.hermes/skills/dispatch-task/references/repeated-fix-recurrence-preflight.md` — When a fix is "diagnosed but not landed" across multiple days. This incident is the related inverse: dispatch is broken, fix is queued but not landed; without the dispatcher-side detection rules, the next session will repeat the same failure shape.
