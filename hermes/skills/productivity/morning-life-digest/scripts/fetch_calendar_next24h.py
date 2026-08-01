#!/usr/bin/env python3
"""Fetch next-24h events across all known $USER Google accounts via gog.

Handles the JSON shape quirks documented in references/gog-gws-tool-quirks.md:
  * `gog calendar events --all` returns {"events":[...]} not {"items":[...]}
  * Output may begin with "Using keyring backend: keyring" line
  * Per-account auth failures are reported but don't crash the loop

Usage:
    python3 fetch_calendar_next24h.py [--hours 24] [--tz -07:00]

Prints JSON to stdout: {"events": [...], "auth_failures": [...], "window": {...}}
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ACCOUNTS = [
    "$USER@gmail.com",
    "jleechan2015@gmail.com",
    "$USER@your-project.com",
]


def fetch(account: str, time_min: str, time_max: str) -> tuple[list, str | None]:
    cmd = [
        "gog", "calendar", "events",
        "--account", account,
        "--from", time_min,
        "--to", time_max,
        "--max", "50",
        "--all",
        "--json",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        return [], f"{account}: timeout"
    if out.returncode != 0 and not out.stdout:
        return [], f"{account}: exit={out.returncode} stderr={out.stderr.strip()[:200]}"
    raw = out.stdout
    # Strip leading keyring line
    idx = raw.find("{")
    if idx < 0:
        return [], f"{account}: no json in output: {raw[:200]}"
    try:
        data = json.loads(raw[idx:])
    except json.JSONDecodeError as e:
        return [], f"{account}: json parse error: {e}"
    # CRITICAL: --all returns {"events":[...]}; defensive on both keys
    items = data.get("items", data.get("events", []))
    return items, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--tz", default="-07:00", help="IANA offset for window edges (e.g. -07:00)")
    args = ap.parse_args()

    now_utc = datetime.now(timezone.utc)
    tz_offset = args.tz if args.tz.startswith(("+", "-")) else "+00:00"
    start = now_utc.astimezone(timezone(tz_offset)).replace(microsecond=0)
    end = start + timedelta(hours=args.hours)
    time_min = start.isoformat()
    time_max = end.isoformat()

    all_events = []
    auth_failures = []
    for acct in ACCOUNTS:
        items, err = fetch(acct, time_min, time_max)
        if err:
            auth_failures.append(err)
            continue
        for ev in items:
            start_field = ev.get("start", {})
            end_field = ev.get("end", {})
            all_events.append({
                "account": acct,
                "calendar_id": ev.get("calendarId", "primary"),
                "id": ev.get("id"),
                "summary": ev.get("summary", ""),
                "start": start_field.get("dateTime", start_field.get("date")),
                "end": end_field.get("dateTime", end_field.get("date")),
                "all_day": "date" in start_field and "dateTime" not in start_field,
                "visibility": ev.get("visibility", "default"),
                "attendees": [a.get("email") for a in ev.get("attendees", []) if isinstance(a, dict)],
            })

    # Sort by start datetime (all-day events first by start date)
    all_events.sort(key=lambda e: (e["start"] or ""))
    json.dump({"events": all_events, "auth_failures": auth_failures,
               "window": {"from": time_min, "to": time_max}},
              sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
