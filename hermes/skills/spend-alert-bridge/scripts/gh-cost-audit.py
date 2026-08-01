#!/usr/bin/env python3
"""
gh-cost-audit.py — last-32h workflow volume audit for a given repo.

Walks all pages of `gh api repos/<repo>/actions/runs?per_page=100&page=N` with
sort=created + direction=desc (the `created=>` query param is treated as
equality by the GitHub API, not greater-than, so we paginate manually).

Groups by `path.split('/')[-1]` (the workflow file name) and reports:
  - COUNT: total runs
  - SKIP: runs with `conclusion='skipped'` (0 billable minutes, but the event
    still registered)
  - WALL_MIN: sum of (updated_at - created_at) in minutes (real wall-clock time)

CAVEAT: `run_duration_ms` is null/0 for skipped runs and unreliable for
queued/in-progress runs. Use `updated_at - created_at` and the configured
$/min rate for the runner type as an approximation of billable cost.

Usage:
  python3 gh-cost-audit.py                  # default: $GITHUB_REPOSITORY
  REPO=jleechanorg/jleechanclaw python3 gh-cost-audit.py
  HOURS=24 python3 gh-cost-audit.py
"""
import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict

REPO = os.environ.get("REPO", "$GITHUB_REPOSITORY")
HOURS = int(os.environ.get("HOURS", "32"))
PER_PAGE = 100

NOW = datetime.now(timezone.utc)
SINCE = (NOW - timedelta(hours=HOURS)).isoformat().replace("+00:00", "Z")


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"ERR {path}: {r.stderr[:200]}\n")
        return None
    return json.loads(r.stdout)


def collect_runs():
    """Paginate all runs, stop when oldest in page is older than SINCE."""
    all_runs = []
    page = 1
    while True:
        data = gh(f"repos/{REPO}/actions/runs?per_page={PER_PAGE}&page={page}")
        if not data:
            break
        runs = data["workflow_runs"]
        all_runs.extend(runs)
        if runs and runs[-1]["created_at"] < SINCE:
            break
        if len(runs) < PER_PAGE:
            break
        page += 1
        if page > 50:
            break
    return [r for r in all_runs if r["created_at"] >= SINCE]


def main():
    runs = collect_runs()
    print(f"runs in last {HOURS}h: {len(runs)} (REPO={REPO}, SINCE={SINCE})",
          file=sys.stderr)

    agg = defaultdict(lambda: {"count": 0, "skipped": 0, "wall_min": 0.0})
    for r in runs:
        key = r["path"].split("/")[-1] if r.get("path") else r.get("name", "?")
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        updated = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
        wall = (updated - created).total_seconds() / 60.0
        agg[key]["count"] += 1
        if r.get("conclusion") == "skipped":
            agg[key]["skipped"] += 1
        agg[key]["wall_min"] += wall

    rows = sorted(agg.items(), key=lambda kv: -kv[1]["count"])
    print(f"\n=== {REPO} — last {HOURS}h ===")
    print(f"{'WORKFLOW':<50} {'RUNS':>5} {'SKIP':>5} {'WALL_MIN':>10}")
    print("-" * 75)
    total_runs = 0
    total_min = 0.0
    for name, v in rows:
        if v["count"] < 5:
            continue
        print(f"{name:<50} {v['count']:>5} {v['skipped']:>5} {v['wall_min']:>10.1f}")
        total_runs += v["count"]
        total_min += v["wall_min"]
    print("-" * 75)
    print(f"{'TOTAL':<50} {total_runs:>5} {'':>5} {total_min:>10.1f}")


if __name__ == "__main__":
    main()
