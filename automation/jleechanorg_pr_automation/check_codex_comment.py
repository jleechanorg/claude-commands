#!/usr/bin/env python3
"""Determine whether a Codex instruction comment should be posted."""

from __future__ import annotations

import json
import sys
from typing import Tuple

# Safety limits for JSON parsing to prevent memory exhaustion
MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB limit for PR data


def decide(marker_prefix: str, marker_suffix: str) -> Tuple[str, str]:
    try:
        # Read stdin with size limit to prevent memory exhaustion
        stdin_data = sys.stdin.read(MAX_JSON_SIZE)
        if len(stdin_data) >= MAX_JSON_SIZE:
            sys.stderr.write("ERROR: PR data exceeds maximum size limit\n")
            return "post", ""

        pr_data = json.loads(stdin_data)
    except json.JSONDecodeError:
        return "post", ""

    head_sha = pr_data.get("headRefOid") or ""

    # Handle GitHub API comments structure variations
    comments_data = pr_data.get("comments", [])
    if isinstance(comments_data, dict):
        # GraphQL format: {"nodes": [...]}
        comments = comments_data.get("nodes", [])
    elif isinstance(comments_data, list):
        # REST API format: [...]
        comments = comments_data
    else:
        comments = []

    if not head_sha:
        return "post", ""

    for comment in comments:
        # Safely handle comment data that may not be a dictionary
        if isinstance(comment, dict):
            body = comment.get("body", "")
        else:
            # Skip malformed comment data
            continue
        prefix_index = body.find(marker_prefix)
        if prefix_index == -1:
            continue

        start_index = prefix_index + len(marker_prefix)
        end_index = body.find(marker_suffix, start_index)
        if end_index == -1:
            continue

        marker_sha = body[start_index:end_index].strip()
        if marker_sha == head_sha:
            return "skip", head_sha

    return "post", head_sha


def main() -> int:
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: check_codex_comment.py <marker_prefix> <marker_suffix>\n")
        return 2

    action, sha = decide(sys.argv[1], sys.argv[2])
    sys.stdout.write(f"{action}:{sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
