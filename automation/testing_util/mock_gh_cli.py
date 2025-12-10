#!/usr/bin/env python3
"""Lightweight mock for the GitHub CLI used by automation smoke tests.

The monitor relies on the `gh` binary to fetch PR metadata and post
comments. This helper emulates the handful of commands we need so the
automation can be exercised offline:

* ``gh pr view <number> --repo <repo> --json ...``
* ``gh pr comment <number> --repo <repo> --body <text>``

It returns deterministic fixture data for three synthetic pull requests:

``#101``  Eligible – no Codex summary comment referencing the head SHA.
``#102``  Ineligible – includes a Codex summary comment that cites the
          current head commit (should trigger the pending-commit skip).
``#103``  Eligible – contains a historic Codex marker for a different SHA.

Usage::

    PATH="/path/to/mock/bin:$PATH" gh ...

where ``/path/to/mock/bin`` contains a copy or symlink of this script
named ``gh``.
"""

from __future__ import annotations

import json
import sys
from typing import Dict, List

PR_FIXTURES: Dict[str, Dict] = {
    "101": {
        "title": "Fix eligible automation path",
        "headRefName": "feature/eligible",
        "baseRefName": "main",
        "url": "https://github.com/$GITHUB_ORG/your-project.com/pull/101",
        "author": {"login": "dev-user"},
        "headRefOid": "abc1234def5678abc1234def5678abc1234def5",
        "comments": [
            {
                "author": {"login": "reviewer"},
                "body": "Looks good to me!",
                "createdAt": "2025-01-01T00:00:00Z",
            }
        ],
    },
    "102": {
        "title": "Pending Codex automation commit",
        "headRefName": "feature/pending",
        "baseRefName": "main",
        "url": "https://github.com/$GITHUB_ORG/your-project.com/pull/102",
        "author": {"login": "automation-bot"},
        "headRefOid": "ffeeddbcaa99887766554433221100ffeeddccbb",
        "comments": [
            {
                "author": {"login": "codex-bot"},
                "body": "Automation summary: Written by Cursor Bugbot for commit ffeeddbc.",
                "createdAt": "2025-01-02T00:00:00Z",
            }
        ],
    },
    "103": {
        "title": "No codex involvement",
        "headRefName": "feature/manual",
        "baseRefName": "main",
        "url": "https://github.com/$GITHUB_ORG/your-project.com/pull/103",
        "author": {"login": "dev-two"},
        "headRefOid": "1234567890abcdef1234567890abcdef12345678",
        "comments": [
            {
                "author": {"login": "codex-helper"},
                "body": "Previous run marker: <!-- codex-automation-commit:1234567 -->",
                "createdAt": "2025-01-03T00:00:00Z",
            }
        ],
    },
}


def _handle_pr_view(args: List[str]) -> int:
    pr_number = args[0]
    fixture = PR_FIXTURES.get(pr_number)
    if not fixture:
        print("{}", end="")
        return 0

    if "--json" in args:
        json_fields = args[args.index("--json") + 1]
        fields = [field.strip() for field in json_fields.split(",")]
    else:
        fields = []

    response: Dict[str, object] = {}
    for field in fields:
        if field in {"title", "headRefName", "baseRefName", "url", "author", "headRefOid", "comments"}:
            response[field] = fixture[field]
        elif field == "statusCheckRollup":
            response[field] = [{"name": "ci", "state": "SUCCESS"}]

    print(json.dumps(response))
    return 0


def _handle_pr_comment(args: List[str]) -> int:
    # We only need to simulate success; the automation logs the comment body.
    print("Comment posted")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2 or args[0] != "pr":
        print("Unsupported command", file=sys.stderr)
        return 1

    command = args[1]
    if command == "view" and len(args) >= 3:
        return _handle_pr_view(args[2:])
    if command == "comment" and len(args) >= 3:
        return _handle_pr_comment(args[2:])

    print("Unsupported command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
