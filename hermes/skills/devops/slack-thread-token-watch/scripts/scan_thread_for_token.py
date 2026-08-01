#!/usr/bin/env python3
"""
scan_thread_for_token.py — deterministic Phase 1 helper for slack-thread-token-watch.

Scans a Slack thread for a literal approval token, applying the seven pitfalls
from references/scan-pitfalls.md as required filters. Returns 0 (no match) or 1
(match) plus a structured report on stdout (JSON).

Usage:
  export SLACK_USER_TOKEN=$(awk -F'"' '/^export SLACK_USER_TOKEN=/{print $2; exit}' ~/.profile)
  python3 scan_thread_for_token.py \\
    --channel C0AJQ5M0A0Y \\
    --thread-ts 1784070882.257369 \\
    --token WORKTREE_APPROVED \\
    --start-ts 1784070882.257369 \\
    --limit 20

Exit codes:
  0 — token found in a human row posted AFTER start_ts and OUTSIDE code blocks
  1 — token NOT found (no match after all filters)
  2 — error (network, auth, malformed args)

Stdout: JSON object describing the scan result + per-row details.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any


def fetch_replies(channel: str, thread_ts: str, limit: int) -> list[dict]:
    """Fetch thread replies via Slack API (XOX-P fallback path).

    Uses SLACK_USER_TOKEN env var. Falls back to MCP if available — but MCP
    access is via the gateway, not via this CLI script, so we always use curl
    here.
    """
    token = os.environ.get("SLACK_USER_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "SLACK_USER_TOKEN env var is empty; source it from ~/.profile: "
            "awk -F'\"' '/^export SLACK_USER_TOKEN=/{print $2; exit}' ~/.profile"
        )
    url = f"https://slack.com/api/conversations.replies?channel={channel}&ts={thread_ts}&limit={limit}"
    r = subprocess.run(
        ["curl", "-fsS", "-H", f"Authorization: Bearer {token}", url],
        capture_output=True,
        text=True,
        timeout=30,
    )
    r.raise_for_status()
    data = json.loads(r.stdout)
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")
    return data.get("messages", [])


def is_human_row(m: dict) -> bool:
    """Pitfall 2: skip bot rows."""
    if m.get("bot_id"):
        return False
    user = m.get("user", "")
    if not user.startswith("U"):
        return False
    return True


def strip_code_blocks(body: str) -> str:
    """Pitfall 3: remove fenced and inline code so we don't match quoted tokens."""
    stripped = re.sub(r"```[\s\S]*?```", "", body)
    stripped = re.sub(r"`[^`]*`", "", stripped)
    return stripped


def scan(messages: list[dict], token: str, start_ts: str) -> dict[str, Any]:
    """Walk messages in ts-ascending order, return first match + summary."""
    report = {
        "matched": False,
        "matched_at": None,
        "matched_user": None,
        "matched_text": None,
        "scanned_count": 0,
        "skipped_bot": 0,
        "skipped_pre_start": 0,
        "skipped_code_block": 0,
        "rows": [],
    }
    for m in sorted(messages, key=lambda x: float(x.get("ts", 0))):
        ts = m.get("ts", "")
        user = m.get("user", "?")
        bot_id = m.get("bot_id", "") or ""
        text = m.get("text", "") or ""

        report["scanned_count"] += 1
        row: dict[str, Any] = {
            "ts": ts,
            "user": user,
            "is_bot": bool(bot_id),
            "text_head": text[:120],
            "match_status": "pending",
        }

        if not is_human_row(m):
            report["skipped_bot"] += 1
            row["match_status"] = "skipped:bot"
            report["rows"].append(row)
            continue

        if float(ts) < float(start_ts):
            report["skipped_pre_start"] += 1
            row["match_status"] = "skipped:pre-start"
            report["rows"].append(row)
            continue

        unquoted = strip_code_blocks(text)
        if token in unquoted:
            report["matched"] = True
            report["matched_at"] = ts
            report["matched_user"] = user
            report["matched_text"] = text
            row["match_status"] = "MATCH"
            report["rows"].append(row)
            return report

        if token in text and token not in unquoted:
            report["skipped_code_block"] += 1
            row["match_status"] = "skipped:in-code-block"
            report["rows"].append(row)
            continue

        row["match_status"] = "no-match"
        report["rows"].append(row)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--channel", required=True, help="Slack channel ID, e.g. C0AJQ5M0A0Y")
    ap.add_argument("--thread-ts", required=True, help="Slack thread parent ts, e.g. 1784070882.257369")
    ap.add_argument("--token", required=True, help="Literal substring to match (case-sensitive)")
    ap.add_argument("--start-ts", required=True, help="Ignore rows posted before this ts")
    ap.add_argument("--limit", type=int, default=20, help="conversations.replies limit (default 20)")
    ap.add_argument("--json", action="store_true", help="Emit JSON only (no human-readable text)")
    args = ap.parse_args()

    try:
        messages = fetch_replies(args.channel, args.thread_ts, args.limit)
    except Exception as e:
        if not args.json:
            print(f"ERROR fetching replies: {e}", file=sys.stderr)
        else:
            print(json.dumps({"ok": False, "error": str(e)}))
        return 2

    report = scan(messages, args.token, args.start_ts)
    report["ok"] = True
    print(json.dumps(report, indent=2))
    return 0 if report["matched"] else 1


if __name__ == "__main__":
    sys.exit(main())
