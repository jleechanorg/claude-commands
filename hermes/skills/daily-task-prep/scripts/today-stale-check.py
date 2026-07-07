#!/usr/bin/env python3
"""
today-stale-check.py — daily-task-prep helper.

Reads `~/.hermes/workspace/tasks/current.md`, finds every `## Today` bullet
whose trailing timestamp is fully in the past, and prints the lines that
should be removed in the same edit (per the Stale-row cleanup rule added
2026-07-07). Carryover lines are kept.

Run:
    python3 ~/.hermes/skills/daily-task-prep/scripts/today-stale-check.py
    python3 ~/.hermes/skills/daily-task-prep/scripts/today-stale-check.py --today 2026-07-07
    python3 ~/.hermes/skills/daily-task-prep/scripts/today-stale-check.py --path /custom/tasks.md
"""
import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_PATH = Path.home() / ".hermes" / "workspace" / "tasks" / "current.md"

# Matches "— YYYY-MM-DD HH:MM-HH:MM TZ" or "— YYYY-MM-DD HH:MM–HH:MM TZ" (em-dash or hyphen)
STALE_RE = re.compile(
    r"—\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})[–-](\d{2}:\d{2})\s+([A-Z]{2,4})\b"
)
CARRYOVER_RE = re.compile(r"carryover\s+from\s+\d{4}-\d{2}-\d{2}", re.IGNORECASE)


def parse_event_end(line: str, today: date):
    m = STALE_RE.search(line)
    if not m:
        return None
    d_str, _, end_time, _tz = m.groups()
    try:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
    except ValueError:
        return None
    return d  # end date == start date for these time blocks; sufficient for daily-task-prep use


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", help="ISO date override (defaults to system local date)")
    ap.add_argument("--path", default=str(DEFAULT_PATH), help="Path to current.md")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    src = Path(args.path)
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 2

    in_today = False
    stale: list[str] = []
    kept: list[str] = []
    for raw in src.read_text().splitlines():
        if raw.strip() == "## Today":
            in_today = True
            continue
        if in_today and raw.startswith("## ") and raw.strip() != "## Today":
            in_today = False
        if not in_today or not raw.lstrip().startswith("- ["):
            continue

        if CARRYOVER_RE.search(raw):
            kept.append(raw)
            continue

        end_d = parse_event_end(raw, today)
        if end_d is not None and end_d < today:
            stale.append(raw)
        else:
            kept.append(raw)

    print(f"=== today-stale-check — today={today} ===")
    print(f"stale (remove): {len(stale)}")
    for line in stale:
        print(f"  - {line.strip()}")
    print(f"kept: {len(kept)}")
    for line in kept:
        print(f"  + {line.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
