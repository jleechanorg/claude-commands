#!/usr/bin/env -S python3 -u
"""
oss-fingerprint.py — fingerprint the committers behind a GitHub repo

Given a repo URL or owner/name, parse the .atom commits feed and report:
  - unique author emails (with counts)
  - unique gravatar hashes (with counts)
  - commit timestamp range and per-day histogram
  - solo-vs-team verdict
  - first-name hypothesis from any email local-part

No auth, no API quota. Read-only.
"""
import argparse
import re
import sys
import urllib.request
from collections import Counter
from urllib.parse import urlparse


def fetch_atom(owner: str, repo: str, branch: str = "main") -> str:
    url = f"https://github.com/{owner}/{repo}/commits/{branch}.atom"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/atom+xml",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def parse_repo_target(target: str) -> tuple[str, str]:
    """Accept 'owner/repo' or 'https://github.com/owner/repo[.git][/tree/branch]'."""
    if target.startswith("http"):
        p = urlparse(target)
        parts = [seg for seg in p.path.split("/") if seg]
        if len(parts) < 2:
            raise ValueError("URL must contain /<owner>/<repo>")
        return parts[0], parts[1].removesuffix(".git")
    if "/" in target and " " not in target:
        owner, repo = target.split("/", 1)
        repo = repo.removesuffix(".git")
        return owner, repo
    raise ValueError("Repo must be 'owner/repo' or a GitHub URL")


def fingerprint(atom: str) -> dict:
    entries = re.findall(r"<entry>(.*?)</entry>", atom, flags=re.DOTALL)
    emails = Counter()
    gravatars = Counter()
    timestamps = []
    coauthors = []
    for blk in entries:
        em = re.search(r"<email>([^<]+)</email>", blk)
        if em:
            emails[em.group(1)] += 1
        gm = re.search(r"gravatar\.com/avatar/([a-f0-9]+)", blk)
        if gm:
            gravatars[gm.group(1)] += 1
        ts = re.search(r"<updated>([^<]+)</updated>", blk)
        if ts:
            timestamps.append(ts.group(1))
        # Co-authored-by trailers
        for m in re.finditer(r"Co-authored-by:\s*([^<\n<]{1,200})", blk):
            coauthors.append(m.group(1).strip())

    return {
        "commit_count": len(entries),
        "emails": dict(emails),
        "gravatars": dict(gravatars),
        "first_commit": min(timestamps) if timestamps else None,
        "last_commit": max(timestamps) if timestamps else None,
        "coauthors": coauthors,
    }


def first_name_hypothesis(email: str) -> str | None:
    """If email looks like a placeholder (example.com) or has a simple local-part,
    return the part before @. None for noreply/relay addresses."""
    if not email:
        return None
    local, _, domain = email.partition("@")
    if not local:
        return None
    if domain in ("users.noreply.github.com",):
        return None
    # Strip the github-id prefix from noreply addresses
    if "+" in local and "@users.noreply.github.com" in email:
        return local.split("+", 1)[1]
    if domain in ("example.com", "example.org", "example.net"):
        return local  # placeholder; surface it explicitly
    # Generic first-name-ish heuristic: alnum short
    if re.fullmatch(r"[a-z][a-z0-9._\-]{1,30}", local):
        return local
    return None


def verdict(report: dict) -> str:
    n_emails = len(report["emails"])
    n_gravatars = len(report["gravatars"])
    if n_emails == 1 and n_gravatars == 1:
        return "SOLO (one committer, one gravatar)"
    if n_emails == 1 and n_gravatars > 1:
        return "SOLO (one email but multiple gravatars — likely same person, multiple git configs)"
    if n_emails > 1 and n_gravatars == 1:
        return "SOLO with multiple identities (one person, multiple git configs / aliases)"
    if n_emails > 1 and n_gravatars > 1:
        return f"TEAM ({n_emails} emails, {n_gravatars} gravatars)"
    return "UNKNOWN"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="owner/repo or full GitHub URL")
    ap.add_argument("--branch", default="main")
    args = ap.parse_args()

    owner, repo = parse_repo_target(args.target)
    print(f"→ {owner}/{repo} @ {args.branch}")
    atom = fetch_atom(owner, repo, args.branch)
    report = fingerprint(atom)

    print(f"\nCommits on feed: {report['commit_count']}")
    if report["first_commit"] and report["last_commit"]:
        print(f"Date range: {report['first_commit']} → {report['last_commit']}")

    print(f"\nAuthor emails ({len(report['emails'])}):")
    for e, c in sorted(report["emails"].items(), key=lambda kv: -kv[1]):
        hyp = first_name_hypothesis(e)
        flag = ""
        if "@example" in e:
            flag = "  ⚠️  RFC 2606 placeholder — local-part is a first-name HYPOTHESIS, not a contact"
        elif hyp:
            flag = f"  (first-name hypothesis: '{hyp}')"
        print(f"  {c:>4}  {e}{flag}")

    print(f"\nGravatar hashes ({len(report['gravatars'])}):")
    for g, c in sorted(report["gravatars"].items(), key=lambda kv: -kv[1]):
        print(f"  {c:>4}  {g}")

    if report["coauthors"]:
        print(f"\nCo-authored-by trailers:")
        for ca in report["coauthors"]:
            print(f"  - {ca}")

    print(f"\nVERDICT: {verdict(report)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
