#!/usr/bin/env python3
"""
Per-(repo, workflow) Actions billing histogram.

Builds a cost breakdown across every repo in an org, grouped by
(repo, workflow_name, event, runner_type). Reusable after any
GitHub Actions spend alert fires when the org-level billing API
points at a spike but the workflow-level grep on main doesn't reveal
the culprit (deleted-workflow drain, label-match fallthrough,
misleading workflow names that contain "self-hosted" but actually run
on GitHub-hosted, etc.).

Verified 2026-07-11 on jleechanorg — caught the Skeptic Cron drain
($264 of $292 7-day cost from a workflow that had already been deleted
from all 42 repos).

Updated 2026-07-29 (v1.5.0): per-job endpoint classification with
parallel fetch + on-disk cache (P16 + P21 + P22 in SKILL.md).
Previously this script used YAML-grep on `main` for self-hosted
detection — that heuristic failed for workflows with "self-hosted" in
their NAME (P21) and the sequential per-job fetch for 2k+ runs timed
out at 600s (P22). Both fixed here.

Bugfix 2026-07-30 (v1.5.1): the `global CACHE_PATH` declaration inside
main() was placed AFTER the `--cache-path` argparse default that reads
the module-level constant, producing a SyntaxError
(`name 'CACHE_PATH' is used prior to global declaration`).
Fix: hoist `global CACHE_PATH` to the first executable line of main(),
compute the default from an env var before the argparse default is
materialised, and re-apply the user's --cache-path after parse_args().
Caught during the 2026-07-29 spend-alert investigation on jleechanorg.

Usage:
    python3 scripts/per-repo-workflow-billing-histogram.py \\
        --org jleechanorg --days 7 --workers 20

Output (stdout, plain text):
    1. Per-runner total (with cost)
    2. Top 25 (repo, workflow, event, runner) by minutes, with conclusions
    3. Per-repo total (corrected, with self-hosted detection)
    4. Per-day × per-(repo, workflow) breakdown (top 15 by total)
    5. Today's GH-hosted workflows ranked
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Default rates (USD/min). Override via --rate linux=X,macos=Y.
# Verify against `usageItems[].pricePerUnit` for your specific org.
DEFAULT_RATES = {
    "linux-github-hosted": 0.008,
    "macos": 0.08,
    "windows": 0.016,
    "self-hosted": 0.002,
}

# Per-job classifier: GH-hosted vs self-hosted vs unknown.
# See SKILL.md P16 + P21 for why this is the only reliable signal.
def classify_runner_from_jobs(jobs):
    """Classify a run by looking at all jobs' runner_name + labels."""
    kinds = set()
    for j in jobs or []:
        rn = j.get("runner_name") or ""
        labs = j.get("labels") or []
        if rn.startswith("GitHub Actions ") or any(
            l in labs for l in ("ubuntu-latest", "macos-latest", "windows-latest")
        ):
            kinds.add("hosted")
        elif rn and "self-hosted" in labs:
            kinds.add("self-hosted")
    if "hosted" in kinds:
        return "hosted"
    if "self-hosted" in kinds:
        return "self-hosted"
    return "unknown"


def gh_api(path, paginate=False):
    """Call gh API with GITHUB_TOKEN unset (per spawn_safe pattern)."""
    cmd = [
        "bash", "-lc",
        f"unset GITHUB_TOKEN; gh api '{path}'{' --paginate' if paginate else ''} 2>/dev/null"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return r.stdout


def list_org_repos(org):
    """Return all private repo full_names in the org."""
    out = gh_api(f"orgs/{org}/repos?per_page=100&type=private", paginate=True)
    pages = [json.loads(l) for l in out.split("\n") if l.strip()]
    return [r["full_name"] for p in pages for r in p]


def fetch_all_runs(repo_full, since_date):
    """Manually paginate actions/runs; avoid --paginate due to URL-filter collision."""
    runs = []
    for page in range(1, 11):
        out = gh_api(f"repos/{repo_full}/actions/runs?per_page=100&page={page}&created=>={since_date}")
        if not out.strip():
            break
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            break
        wrs = data.get("workflow_runs") or []
        if not wrs:
            break
        runs.extend(wrs)
        if len(wrs) < 100:
            break
    return runs


def load_classification_cache():
    """Load cached per-run classifications from disk if present."""
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def save_classification_cache(cache):
    """Persist cache to disk for next run."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache))


def fetch_and_classify(repo_full, run_id):
    """Fetch per-job endpoint for one run and classify it."""
    out = gh_api(f"repos/{repo_full}/actions/runs/{run_id}/jobs")
    if not out.strip():
        return "unknown"
    try:
        jobs = json.loads(out).get("jobs") or []
    except json.JSONDecodeError:
        return "unknown"
    return classify_runner_from_jobs(jobs)


# YAML-grep fallback for runs where per-job 404s. Kept for compatibility
# with deleted-from-history edge case. NOT primary — see P21.
def yaml_grep_self_hosted(repo_full, path, cache):
    key = (repo_full, path)
    if key in cache:
        return cache[key]
    for ref in ("main", "master"):
        out = gh_api(f"repos/{repo_full}/contents/{path}?ref={ref}")
        try:
            data = json.loads(out) if out.strip() else {}
            content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
            cache[key] = bool("self-hosted" in content or "SELF_HOSTED" in content)
            return cache[key]
        except Exception:
            continue
    cache[key] = False
    return False


def classify_runner_hybrid(repo_full, run, job_cache, yaml_cache):
    """Primary: per-job endpoint. Fallback: YAML grep."""
    rid = str(run.get("id"))
    if rid in job_cache:
        kind = job_cache[rid]
        if kind in ("hosted", "self-hosted"):
            return kind
    # Fallback: YAML grep (only used when per-job 404'd)
    return "self-hosted" if yaml_grep_self_hosted(repo_full, run.get("path", ""), yaml_cache) else "hosted"


def main():
    # Bugfix 2026-07-30: `global CACHE_PATH` MUST be declared before any
    # read or write of CACHE_PATH in this function. The argparse default
    # below reads CACHE_PATH, so the global declaration has to be on the
    # very first executable line. We resolve the default from an env var
    # (overridable as `JLORG_RUN_CLASSIFICATION_CACHE`) and re-apply the
    # user's --cache-path override after parse_args().
    global CACHE_PATH  # noqa: PLW0603
    CACHE_PATH = Path(os.environ.get(
        "JLORG_RUN_CLASSIFICATION_CACHE",
        str(Path.home() / ".hermes" / "cache" / "jlorg-run-classification.json"),
    ))

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", required=True, help="GitHub org name")
    ap.add_argument("--days", type=int, default=7, help="Lookback window in days (default 7)")
    ap.add_argument("--workers", type=int, default=20, help="Parallelism for per-job classification (default 20)")
    ap.add_argument("--cache-path", default=str(CACHE_PATH),
                    help=f"Per-run classification cache path (default: {CACHE_PATH})")
    ap.add_argument("--rate", action="append", default=[],
                    help="Override pricing rate, format: linux=0.008 or macos=0.08 (repeatable)")
    args = ap.parse_args()

    rates = dict(DEFAULT_RATES)
    for ovr in args.rate:
        if "=" in ovr:
            k, v = ovr.split("=", 1)
            rates[k] = float(v)

    # Re-apply the user-supplied --cache-path after parse.
    CACHE_PATH = Path(args.cache_path)

    since_date = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%d")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"=== {args.org} Actions billing histogram ===")
    print(f"Window: {since_date} → {today} ({args.days}d)")
    print(f"Rates: {rates}")
    print(f"Per-job cache: {CACHE_PATH}\n")

    # 1. List repos
    print(f"[1/5] Listing repos in {args.org}...")
    repos = list_org_repos(args.org)
    print(f"      Found {len(repos)} repos\n")

    # 2. Fetch runs (parallel across repos)
    print(f"[2/5] Fetching completed runs from last {args.days}d...")
    t0 = time.time()
    repo_runs = {repo: [] for repo in repos}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_all_runs, r, since_date): r for r in repos}
        for fut in as_completed(futs):
            repo = futs[fut]
            try:
                runs = fut.result()
            except Exception:
                runs = []
            if runs:
                repo_runs[repo] = runs
    total_runs = sum(len(v) for v in repo_runs.values())
    print(f"      {total_runs} runs from {sum(1 for v in repo_runs.values() if v)}/{len(repos)} repos "
          f"({time.time() - t0:.1f}s)\n")

    # 3. Per-job classification (parallel across runs) with cache
    print(f"[3/5] Classifying runner types via per-job endpoint ({args.workers} workers, with cache)...")
    job_cache = load_classification_cache()
    yaml_cache = {}

    # Build list of (repo, run_id) tuples still needing classification
    to_classify = []
    for repo, runs in repo_runs.items():
        for run in runs:
            if str(run.get("id")) not in job_cache or job_cache[str(run["id"])] not in ("hosted", "self-hosted"):
                to_classify.append((repo, run["id"]))
    print(f"      {len(to_classify)} runs need classification (cache: {len(job_cache)})")

    t0 = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_and_classify, repo, rid): (repo, rid)
                for repo, rid in to_classify}
        for fut in as_completed(futs):
            repo, rid = futs[fut]
            try:
                kind = fut.result()
            except Exception:
                kind = "unknown"
            job_cache[str(rid)] = kind
            completed += 1
            if completed % 200 == 0:
                save_classification_cache(job_cache)
                print(f"      {completed}/{len(to_classify)} classified ({time.time() - t0:.0f}s)")
    save_classification_cache(job_cache)
    print(f"      {completed} classified in {time.time() - t0:.1f}s; cache size {len(job_cache)}\n")

    # 4. Aggregate
    print(f"[4/5] Aggregating...")
    hist = defaultdict(lambda: {"count": 0, "minutes": 0.0, "conclusions": defaultdict(int)})
    per_day_hist = defaultdict(lambda: {"count": 0, "minutes": 0.0})
    runner_totals = defaultdict(lambda: {"minutes": 0.0, "count": 0})
    for repo, runs in repo_runs.items():
        for run in runs:
            if run.get("status") != "completed":
                continue
            try:
                st = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
                up = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                dur_min = max(0.0, (up - st).total_seconds() / 60.0)
            except (KeyError, ValueError):
                continue
            runner = classify_runner_hybrid(repo, run, job_cache, yaml_cache)
            key = (repo, run.get("name", "?"), run.get("event", "?"), runner)
            day = run["run_started_at"][:10]
            hist[key]["count"] += 1
            hist[key]["minutes"] += dur_min
            conc = run.get("conclusion") or "unknown"
            hist[key]["conclusions"][conc] += 1
            runner_totals[runner]["minutes"] += dur_min
            runner_totals[runner]["count"] += 1
            if runner != "self-hosted":
                per_day_hist[(day, repo, run.get("name", "?"))]["minutes"] += dur_min
                per_day_hist[(day, repo, run.get("name", "?"))]["count"] += 1

    # Output
    print("=" * 70)
    print("By runner:")
    for r, v in sorted(runner_totals.items(), key=lambda kv: -kv[1]["minutes"]):
        cost = v["minutes"] * rates.get(r, 0.008)
        print(f"  {r:25s} {v['minutes']:9.1f}min  ${cost:8.2f}  {v['count']} runs")

    print("\n" + "=" * 70)
    print(f"Top 25 by minutes:")
    for (repo, wf, evt, runner), v in sorted(hist.items(), key=lambda kv: -kv[1]["minutes"])[:25]:
        rate = rates.get(runner, 0.008)
        concs = ", ".join(f"{k}:{n}" for k, n in sorted(v["conclusions"].items(), key=lambda kv: -kv[1]))
        print(f"  {v['minutes']:8.1f}min  ${v['minutes']*rate:7.2f}  {v['count']:4}runs  "
              f"{repo:35s} {wf[:36]:36s} {evt:14s} {runner:20s} [{concs}]")

    print("\n" + "=" * 70)
    print("Per-repo (GH-hosted cost only):")
    repo_tot = defaultdict(lambda: {"count": 0, "minutes": 0.0, "gh_minutes": 0.0, "gh_cost": 0.0})
    for (repo, wf, evt, runner), v in hist.items():
        repo_tot[repo]["count"] += v["count"]
        repo_tot[repo]["minutes"] += v["minutes"]
        if runner != "self-hosted":
            repo_tot[repo]["gh_minutes"] += v["minutes"]
            repo_tot[repo]["gh_cost"] += v["minutes"] * rates.get(runner, 0.008)
    for repo, v in sorted(repo_tot.items(), key=lambda kv: -kv[1]["gh_cost"]):
        print(f"  GH-min={v['gh_minutes']:8.1f}  ${v['gh_cost']:7.2f}  "
              f"total-min={v['minutes']:8.1f}  {v['count']:5}runs  {repo}")

    print("\n" + "=" * 70)
    print(f"Today ({today}) GH-hosted workflows, ranked:")
    today_tot = defaultdict(lambda: {"minutes": 0.0, "count": 0})
    for (day, repo, wf), v in per_day_hist.items():
        if day == today:
            today_tot[(repo, wf)]["minutes"] += v["minutes"]
            today_tot[(repo, wf)]["count"] += v["count"]
    for (repo, wf), v in sorted(today_tot.items(), key=lambda kv: -kv[1]["minutes"]):
        print(f"  ${v['minutes']*rates.get('linux-github-hosted', 0.008):6.2f} "
              f"{v['minutes']:6.0f}min  {v['count']:3d}runs  {repo:35s} {wf[:40]}")


if __name__ == "__main__":
    main()