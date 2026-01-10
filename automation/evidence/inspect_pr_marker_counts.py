#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor
from jleechanorg_pr_automation.utils import get_automation_limits


def _extract_comments(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    comments_data = payload.get("comments", [])
    if isinstance(comments_data, dict):
        nodes = comments_data.get("nodes", [])
        return nodes if isinstance(nodes, list) else []
    if isinstance(comments_data, list):
        return comments_data
    return []


def _gh_pr_view(repo: str, pr_number: int) -> Dict[str, Any]:
    cmd = [
        "gh",
        "pr",
        "view",
        str(pr_number),
        "--repo",
        repo,
        "--json",
        "headRefOid,comments,title,author,headRefName,updatedAt,url",
    ]
    timeout_seconds = int(os.getenv("INSPECT_PR_MARKER_GH_TIMEOUT_SECONDS", "30"))
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout_seconds)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "gh CLI not found (required for inspect_pr_marker_counts). Install GitHub CLI and authenticate."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"gh pr view timed out after {timeout_seconds}s for {repo}#{pr_number}") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh failed with exit code {result.returncode}")
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse gh JSON: {exc}") from exc


@dataclass(frozen=True)
class MarkerCounts:
    repo: str
    pr_number: int
    head_sha: Optional[str]
    title: str
    author: str
    branch: str
    url: str
    workflow_counts: Dict[str, int]
    workflow_limits: Dict[str, int]
    last_automation_comment_time: Optional[str]


def _compute(repo: str, pr_number: int) -> MarkerCounts:
    payload = _gh_pr_view(repo, pr_number)
    comments = _extract_comments(payload)

    monitor = JleechanorgPRMonitor()
    head_sha = payload.get("headRefOid")

    workflow_counts = {
        "pr_automation": monitor._count_workflow_comments(comments, "pr_automation"),
        "fix_comment": monitor._count_workflow_comments(comments, "fix_comment"),
        "codex_update": monitor._count_workflow_comments(comments, "codex_update"),
        "fixpr": monitor._count_workflow_comments(comments, "fixpr"),
    }

    limits = get_automation_limits()
    workflow_limits = {
        "pr_automation_limit": limits.get("pr_automation_limit"),
        "fix_comment_limit": limits.get("fix_comment_limit"),
        "codex_update_limit": limits.get("codex_update_limit"),
        "fixpr_limit": limits.get("fixpr_limit"),
        "legacy_pr_limit": limits.get("pr_limit"),
    }

    last_time = monitor._get_last_codex_automation_comment_time(comments)
    return MarkerCounts(
        repo=repo,
        pr_number=pr_number,
        head_sha=head_sha,
        title=str(payload.get("title") or ""),
        author=str((payload.get("author") or {}).get("login") or ""),
        branch=str(payload.get("headRefName") or ""),
        url=str(payload.get("url") or ""),
        workflow_counts=workflow_counts,
        workflow_limits=workflow_limits,
        last_automation_comment_time=last_time,
    )


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Inspect workflow marker counts for a PR")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument("--json-out", default=None, help="Write machine-readable JSON to this path")
    args = parser.parse_args(argv)

    counts = _compute(args.repo, args.pr)

    print(f"Repo: {counts.repo}")
    print(f"PR: #{counts.pr_number}")
    print(f"URL: {counts.url}")
    print(f"Title: {counts.title}")
    print(f"Author: {counts.author}")
    print(f"Branch: {counts.branch}")
    print(f"Head SHA: {counts.head_sha or 'unknown'}")
    print(f"Last automation comment time: {counts.last_automation_comment_time or 'none'}")
    print("")
    print("Counts:")
    for key, value in counts.workflow_counts.items():
        print(f"  {key}: {value}")
    print("")
    print("Limits (from env/defaults):")
    for key, value in counts.workflow_limits.items():
        print(f"  {key}: {value}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(asdict(counts), f, indent=2, sort_keys=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
