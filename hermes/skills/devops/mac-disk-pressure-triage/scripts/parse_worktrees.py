#!/usr/bin/env python3
# Requires Python 3.10+ for `str | None` syntax (or `from __future__ import annotations`)
# Self-contained: depends only on `git`, `du`, and `gh` (the latter optional — only via
# the caller building the open-PR file; this script never shells out to gh).
"""Parse `git worktree list --porcelain` reliably and classify for safe cleanup.

Replaces the unreliable `grep -B1 'prunable'` pattern (which produces false
positives when branch names happen to contain the substring "prunable") with
a deterministic parser that checks for the EXACT porcelain field name.

Usage:
    # Just classify (no writes)
    parse_worktrees.py ~/projects/<repo>

    # Classify and delete Tier-1 candidates (unlocked + not on any open PR)
    parse_worktrees.py ~/projects/<repo> --delete-safe \\
        --open-pr-file /tmp/open_prs_<repo>.txt

    # Dry-run with explicit per-bucket totals
    parse_worktrees.py ~/projects/<repo> --open-pr-file /tmp/open_prs.txt

Buckets produced:
    prunable_by_git     — git itself says safe (exited by a previous session)
    locked              — DO NOT DELETE; held by a live process
    unlocked_safe       — Tier 1 candidates (not locked, branch not on any
                           open PR, not the repo's main worktree)
    unlocked_protected  — unlocked but backing an open PR (DO NOT DELETE)
    main                — the repo's primary worktree (always skipped)

The branch-extract step uses `git -C <wt> symbolic-ref --short HEAD` and
falls back to "(detached)" on a detached HEAD. This is slower than parsing
the porcelain `branch refs/heads/X` line, but it's a sanity check — the
porcelain branch field can be stale when a worktree's branch has been
deleted upstream.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Worktree:
    path: str
    branch: str | None       # e.g. "fix/foo" or None for detached
    locked: bool
    prunable: bool           # git-marked safe (porcelain "prunable" keyword)
    prunable_reason: str | None  # git's reason string if prunable
    is_main: bool            # the primary worktree of the repo


def load_open_pr_heads(path: Path | None) -> set[str]:
    """Read open PR head ref names from a text file (one per line)."""
    if not path or not path.exists():
        return set()
    out: set[str] = set()
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.add(line)
    return out


def parse_porcelain(repo: Path) -> list[Worktree]:
    """Parse `git -C <repo> worktree list --porcelain` into Worktree objects."""
    result = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        capture_output=True, text=True, check=True,
    )
    entries: list[Worktree] = []
    cur_path: str | None = None
    cur_branch: str | None = None
    cur_locked = False
    cur_prunable = False
    cur_prunable_reason: str | None = None

    def flush() -> None:
        nonlocal cur_path, cur_branch, cur_locked, cur_prunable, cur_prunable_reason
        if cur_path is not None:
            entries.append(Worktree(
                path=cur_path,
                branch=cur_branch,
                locked=cur_locked,
                prunable=cur_prunable,
                prunable_reason=cur_prunable_reason,
                is_main=False,  # set in second pass
            ))
        cur_path = None
        cur_branch = None
        cur_locked = False
        cur_prunable = False
        cur_prunable_reason = None

    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            flush()
            cur_path = line[len("worktree "):].strip()
        elif line.startswith("HEAD "):
            pass  # SHA — not used
        elif line.startswith("branch "):
            ref = line[len("branch "):].strip()
            cur_branch = ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref
        elif line == "detached":
            cur_branch = None
        elif line.startswith("locked"):
            cur_locked = True
        elif line.startswith("prunable"):
            cur_prunable = True
            # "prunable" alone OR "prunable <reason>"
            rest = line[len("prunable"):].strip()
            cur_prunable_reason = rest if rest else None
        elif line == "":
            flush()
    flush()

    # Mark the primary worktree (the one matching `git rev-parse --show-toplevel`)
    show_toplevel = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    main_path = show_toplevel.stdout.strip() if show_toplevel.returncode == 0 else None
    for e in entries:
        if main_path and os.path.realpath(e.path) == os.path.realpath(main_path):
            e.is_main = True
    return entries


def classify(entries: list[Worktree], open_heads: set[str]) -> dict[str, list[Worktree]]:
    """Bucket entries. Refetches branch via `symbolic-ref` for unlocked entries
    as a sanity check (porcelain branch field can be stale)."""
    buckets = {
        "main": [],
        "prunable_by_git": [],
        "locked": [],
        "unlocked_protected": [],
        "unlocked_safe": [],
    }
    for e in entries:
        # Defensive branch re-resolution for the bucket decision
        if not e.locked and not e.is_main and e.branch is None:
            try:
                symbolic = subprocess.run(
                    ["git", "-C", e.path, "symbolic-ref", "--short", "HEAD"],
                    capture_output=True, text=True, timeout=5,
                )
                if symbolic.returncode == 0:
                    e.branch = symbolic.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

        if e.is_main:
            buckets["main"].append(e)
        elif e.prunable:
            buckets["prunable_by_git"].append(e)
        elif e.locked:
            buckets["locked"].append(e)
        elif e.branch and e.branch in open_heads:
            buckets["unlocked_protected"].append(e)
        else:
            buckets["unlocked_safe"].append(e)
    return buckets


def size_of(path: str) -> str:
    try:
        out = subprocess.check_output(["du", "-sh", path], text=True, stderr=subprocess.DEVNULL)
        return out.split()[0]
    except Exception:
        return "?"


def print_report(repo: Path, buckets: dict[str, list[Worktree]], show_top: int = 30) -> None:
    entries = sum(len(v) for v in buckets.values())
    print(f"# Worktree triage for {repo}")
    print(f"# Total in registry: {entries}")
    for name in ("main", "prunable_by_git", "locked", "unlocked_protected", "unlocked_safe"):
        n = len(buckets[name])
        label = {
            "main": "Main worktree (SKIP)",
            "prunable_by_git": "Prunable by git (safe)",
            "locked": "LOCKED (DO NOT DELETE)",
            "unlocked_protected": "Unlocked + on open PR (DO NOT DELETE)",
            "unlocked_safe": "Unlocked + PR-free (Tier 1 candidates)",
        }[name]
        print(f"#   {n:>5}  {label}")
    print()

    if buckets["locked"]:
        print(f"## LOCKED (verify no live agent processes before any cleanup)")
        for e in buckets["locked"]:
            print(f"  {size_of(e.path):>8}  {e.branch or '(detached)':<50}  {e.path}")
        print()

    if buckets["unlocked_protected"]:
        print(f"## Unlocked + on open PR (DO NOT DELETE)")
        for e in buckets["unlocked_protected"]:
            print(f"  {size_of(e.path):>8}  {e.branch or '(detached)':<50}  {e.path}")
        print()

    if buckets["prunable_by_git"]:
        print(f"## Prunable by git (safe to delete)")
        for e in buckets["prunable_by_git"]:
            reason = f" ({e.prunable_reason})" if e.prunable_reason else ""
            print(f"  {size_of(e.path):>8}  {e.branch or '(detached)':<50}  {e.path}{reason}")
        print()

    if buckets["unlocked_safe"]:
        print(f"## Tier 1 candidates (top {show_top} by size)")
        # du all then sort by size desc
        sized_with_size = [(size_of(e.path), e) for e in buckets["unlocked_safe"]]
        sized_with_size.sort(key=lambda t: t[0], reverse=True)
        for size, e in sized_with_size[:show_top]:
            print(f"  {size:>8}  {e.branch or '(detached)':<50}  {e.path}")
        if len(sized_with_size) > show_top:
            print(f"  ... and {len(sized_with_size) - show_top} more")
        print()


def delete_safe(repo: Path, buckets: dict[str, list[Worktree]], dry_run: bool = True) -> None:
    """Delete Tier 1 candidates via `git worktree remove --force`. Falls back to
    `rm -rf` if git refuses (locked mid-run, or path not in registry)."""
    candidates = buckets["unlocked_safe"] + buckets["prunable_by_git"]
    if not candidates:
        print("# Nothing to delete.")
        return
    print(f"# {'DRY-RUN' if dry_run else 'DELETING'} {len(candidates)} worktrees...")
    failed = []
    for e in candidates:
        if not os.path.isdir(e.path):
            continue
        if dry_run:
            print(f"  would remove: {e.path}")
            continue
        # Prefer git command — honors locks/registry
        result = subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", e.path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            # Last-resort direct rm
            try:
                subprocess.run(["rm", "-rf", e.path], check=True)
                print(f"  removed (rm -rf): {e.path}")
            except Exception as ex:
                failed.append((e.path, str(ex)))
                print(f"  FAILED: {e.path}: {ex}")
        else:
            print(f"  removed: {e.path}")
    if failed:
        print(f"\n# {len(failed)} failures:")
        for p, err in failed:
            print(f"  {p}: {err}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("repo", type=Path, help="Path to the git repo's primary worktree")
    p.add_argument("--open-pr-file", type=Path, default=None,
                   help="File of open PR headRefName values, one per line")
    p.add_argument("--delete-safe", action="store_true",
                   help="Actually delete Tier-1 candidates (omit for dry-run)")
    p.add_argument("--top", type=int, default=30,
                   help="Show top N by size in the report (default 30)")
    args = p.parse_args()

    try:
        entries = parse_porcelain(args.repo)
    except subprocess.CalledProcessError as ex:
        print(f"# git worktree list failed for {args.repo}: {ex.stderr}", file=sys.stderr)
        return 2

    open_heads = load_open_pr_heads(args.open_pr_file)
    buckets = classify(entries, open_heads)
    print_report(args.repo, buckets, show_top=args.top)

    if args.delete_safe:
        delete_safe(args.repo, buckets, dry_run=False)
        # Re-summarize so the operator sees the after-state
        print()
        print("## Post-cleanup re-triage")
        entries2 = parse_porcelain(args.repo)
        buckets2 = classify(entries2, open_heads)
        print(f"  Total: {len(entries2)}, locked: {len(buckets2['locked'])}, "
              f"safe: {len(buckets2['unlocked_safe'])}, prunable: {len(buckets2['prunable_by_git'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
