#!/usr/bin/env python3
"""
comment-audit.py — last-N-hours issue comment audit for a given repo.

Walks all pages of `gh api repos/<repo>/issues/comments?per_page=100&page=N`
with sort=created + direction=desc.  The `since` query parameter is IGNORED by
GitHub for this endpoint, so we paginate manually and filter `created_at` in
process.

Groups by:
  - (user.login, author_association) — who is leaving the comments
  - body[:80] — what kind of comment (truncated for grouping)
  - hour bucket — when the burst occurred

Usage:
  python3 comment-audit.py                          # default: $GITHUB_REPOSITORY, 24h
  REPO=jleechanorg/jleechanclaw HOURS=48 python3 comment-audit.py
  python3 comment-audit.py --top-issues 10          # also show per-PR totals
"""
import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

REPO = os.environ.get("REPO", "$GITHUB_REPOSITORY")
HOURS = int(os.environ.get("HOURS", "24"))
PER_PAGE = 100
TOP_ISSUES = int(os.environ.get("TOP_ISSUES", "10"))

NOW = datetime.now(timezone.utc)
SINCE = (NOW - timedelta(hours=HOURS)).isoformat().replace("+00:00", "Z")


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"ERR {path}: {r.stderr[:200]}\n")
        return None
    return json.loads(r.stdout)


def collect_comments():
    all_comments = []
    page = 1
    while True:
        data = gh(f"repos/{REPO}/issues/comments?per_page={PER_PAGE}&page={page}"
                  f"&sort=created&direction=desc")
        if not data:
            break
        all_comments.extend(data)
        if data and data[-1]["created_at"] < SINCE:
            break
        if len(data) < PER_PAGE:
            break
        page += 1
        if page > 100:
            break
    return [c for c in all_comments if c["created_at"] >= SINCE]


def main():
    comments = collect_comments()
    print(f"comments in last {HOURS}h: {len(comments)} "
          f"(REPO={REPO}, SINCE={SINCE})", file=sys.stderr)

    by_user = Counter()
    by_prefix = Counter()
    by_hour = defaultdict(Counter)
    issue_to_user = defaultdict(Counter)

    for c in comments:
        u = c["user"]["login"]
        aa = c["author_association"]
        by_user[(u, aa)] += 1
        body = (c.get("body") or "").strip()[:80].replace("\n", " ⏎ ")
        by_prefix[body] += 1
        hour = c["created_at"][:13]  # YYYY-MM-DDTHH
        by_hour[hour][u] += 1
        issue_url = c.get("issue_url", "")
        issue_id = issue_url.rsplit("/", 1)[-1] if issue_url else "?"
        issue_to_user[issue_id][u] += 1

    print(f"\n=== {REPO} — last {HOURS}h issue comments ===\n")
    print("by author:")
    for (u, aa), n in by_user.most_common(15):
        print(f"  {n:>5}  {u:<35}  assoc={aa}")

    print("\ntop body prefixes:")
    for body, n in by_prefix.most_common(15):
        print(f"  {n:>5}  {body!r}")

    print(f"\ntop {TOP_ISSUES} issues/PRs by comment count:")
    issue_totals = {k: sum(v.values()) for k, v in issue_to_user.items()}
    for issue_id, total in sorted(issue_totals.items(),
                                   key=lambda kv: -kv[1])[:TOP_ISSUES]:
        users = issue_to_user[issue_id]
        sample = ", ".join(f"{u}:{n}" for u, n in users.most_common(3))
        print(f"  PR#{issue_id:<8}  total={total:<4}  {sample}")

    # Find the noisiest user and plot their per-hour activity
    if by_user:
        top_user, top_n = by_user.most_common(1)[0]
        if top_n > 10:
            print(f"\n{top_user} per-hour (last {HOURS}h):")
            for hour in sorted(by_hour.keys()):
                n = by_hour[hour].get(top_user, 0)
                if n:
                    bar = "█" * min(n, 60)
                    print(f"  {hour}  {n:>4}  {bar}")


if __name__ == "__main__":
    main()
