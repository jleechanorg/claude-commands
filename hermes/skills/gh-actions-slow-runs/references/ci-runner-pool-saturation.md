# CI runner-pool saturation — session reference (2026-07-05, your-project.com)

## Concrete reproduction recipe

Replicating the pattern: **27-runner pool saturating with stuck `Green Gate` runs on `$GITHUB_REPOSITORY`**, with 745MB repo causing 488-550s checkout steps.

### Snapshot in_progress with ages (Python)

```python
import subprocess, json
from datetime import datetime, timezone

r = subprocess.run(
    ["gh","api","-H","Accept: application/vnd.github+json",
     "repos/OWNER/REPO/actions/runs?status=in_progress&per_page=25"],
    capture_output=True, text=True, timeout=30)
runs = json.loads(r.stdout).get("workflow_runs", [])
now = datetime.now(timezone.utc)
for run in runs:
    s = datetime.fromisoformat(run["run_started_at"].replace("Z","+00:00"))
    age = (now - s).total_seconds() / 60.0
    print(f"{run['id']} {run['name'][:30]:<30} {age:5.1f}m {run['head_branch'][:35]}")
```

`run_started_at` is the wall clock the job was assigned a runner — that's the right "age" reference. `updated_at` lags during silent aborts.

### Job-level: find what's actually stuck

```python
rj = subprocess.run(["gh","api", f"repos/OWNER/REPO/actions/runs/{rid}/jobs"], capture_output=True, text=True, timeout=20)
jobs = json.loads(rj.stdout).get("jobs", [])
for j in jobs:
    print(f"JOB runner={j.get('runner_name')} status={j['status']}")
    for s in j.get("steps", []):
        dur = ""
        if s.get("started_at") and s.get("completed_at"):
            a = datetime.fromisoformat(s["started_at"].replace("Z","+00:00"))
            b = datetime.fromisoformat(s["completed_at"].replace("Z","+00:00"))
            dur = f"({(b-a).total_seconds():.0f}s)"
        elif s.get("started_at"):
            a = datetime.fromisoformat(s["started_at"].replace("Z","+00:00"))
            dur = f"(in_progress {(now - a).total_seconds():.0f}s)"
        print(f"  [{s['number']}] {s['status']} {s['name']}{dur}")
```

### Pool snapshot (org-level)

```python
r = subprocess.run(["gh","api", "-H", "Accept: application/vnd.github+json",
    "/orgs/ORG/actions/runners?per_page=100"], capture_output=True, text=True, timeout=30)
data = json.loads(r.stdout)
busy = [x for x in data["runners"] if x["busy"]]
print(f"{data['total_count']} total, {len(busy)} busy, {len(idle)} idle")
```

Repo-level `/actions/runners` may return empty for self-hosted runners (they live at the org level).

## cancel-loop reality check (CRITICAL)

After 5 waves of cancellation, the pattern that emerges:

- **Cancel frees runners for ~30-60s**, then active PRs (matrix workflows) re-saturate
- The fix (fetch-depth PR) **doesn't take effect until merged**
- So `gh run cancel` is a **band-aid** — the real fix is merging the checkout-optimization PR
- **Tell the user** the cancel-loop is self-regenerating and will keep refilling until the underlying PRs stop pushing OR the fetch-depth PR merges
- Set a one-time status cron to do periodic auto-cancels while waiting for merge

In this session: 30+ stuck runs cancelled across 5 waves (oldest 92.7m, Green Gate polls continuing forever).

## `Green Gate` silent-step-2 abort pattern

When `Green Gate` job logs show only "Set up job" completed and all subsequent steps missing, this is **classic self-hosted runner OOM/network abort**. Recovery: cancel run, let GitHub auto-trigger a fresh one. The polling loop in green-gate.yml (40×20s Bugbot + 50×10s GraphQL retries) takes 5-30min on a healthy runner — slow on degraded runners, but eventually completes.

## Beads lint — `bead-pr-lint.yml` regex pitfall (LESSON FROM THIS SESSION)

**The lint regex is `^[[:space:]]*Beads:[[:space:]]*`** — it requires `Beads:` to be the first non-whitespace token on a line. Inline prose like `**Beads: rev-myr1u** (this PR's tracking bead)` parses fine to a human and fails the lint.

**Correct**:
```
### Tracking

Beads: rev-myr1u
```

**Wrong** (parses visually but fails lint):
```
**Beads: rev-myr1u** (this PR's tracking bead)
```

The skill's pitfall P4 covers "PR body MUST contain a `Beads:` line" but missed the **standalone-line requirement**. Update on next revision.

## Beads JSONL sort — pre-existing on main

`bead-jsonl-sort-check.yml` enforces `.beads/issues.jsonl` sorted by `id` ascending. If your PR doesn't touch `.beads/issues.jsonl` but the gate fails, **first verify the same inversion exists on `origin/main`**:

```bash
git show origin/main:.beads/issues.jsonl | python3 -c "
import sys, json
ids = [json.loads(l)['id'] for l in sys.stdin.read().strip().split(chr(10)) if l.strip()]
inv = [(a,b) for a,b in zip(ids, ids[1:]) if a>b]
print(f'{len(inv)} inversions: {inv[:3]}')"
```

If `origin/main` has the same inversion, the gate is broken-on-main, not on your PR. Run `python3 scripts/sort_beads_jsonl.py` and include the canonical sort in your PR (per AGENTS.md "Keep `.beads/` tracked and include beads changes in PRs").

## cmux workspace survey — gotchas

`cmux list-workspaces` returns **plain text**, not JSON, despite the `--json` flag. The actual JSON path is `cmux list-workspaces --json` which returns:

```json
{
  "window_ref": "window:1",
  "workspaces": [
    {
      "ref": "workspace:3",
      "title": "factory",
      "current_directory": "$HOME/projects/dark-factory",
      "latest_submitted_message": "use /ms and ramp up...",
      "latest_submitted_at": "2026-07-05T18:23:41.416Z",
      ...
    }
  ]
}
```

The `latest_submitted_message` field shows the most recent user instruction per workspace — useful for detecting parallel workstreams competing for the same runners.

**ID gotcha**: `cmux tree --workspace 15` returns the **currently-focused workspace**, not workspace 15. Workspace IDs are dynamically assigned, not the order shown in `list-workspaces`. Use the `ref` from JSON to be precise.