# Calendar Discovery — multi-calendar parsing recipe

Captured 2026-07-05 after a session that found a Reclaim focus-time block hidden on a calendar the default `gog` invocation missed.

## Why `--all` matters

`gog calendar events` defaults to a single calendar (the OAuth'd account's primary). For accounts with multiple connected calendars (Gmail personal + Google work + Snapchat + Reclaim/Clockwise auto-scheduling + family), the default invocation returns ~4 events and silently drops everything on the auxiliary calendars. The `--all` flag is the only way to get the union.

Verified command (returns 230 lines / 5 events on a typical Sunday):

```bash
gog calendar events --days=1 --max=200 --all --json --results-only
```

Without `--all` the same command returns 4 events; with it, 5 — the extra was a `🔒 🎯 Focus time` block from a Reclaim calendar.

## Post-filter by local date in Python

`gog` returns events across the requested window but does not pre-filter to today. Always re-bucket in Python using {{OWNER_NAME}}'s local timezone, not UTC.

```python
import subprocess, json
from datetime import datetime, timezone, timedelta

PT = timezone(timedelta(hours=-7))  # or whatever {{OWNER_NAME}}'s tz is
today_date = datetime.now(PT).date()

r = subprocess.run(
    ["gog", "calendar", "events", "--days=1", "--max=200",
     "--all", "--json", "--results-only"],
    capture_output=True, text=True,
)
events = json.loads(r.stdout)

todays = []
for e in events:
    s = e.get("start", {})
    dt_str = s.get("dateTime") or s.get("date")
    if not dt_str:
        continue
    if "T" in dt_str:
        local = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(PT)
    else:  # all-day event
        local = datetime.fromisoformat(dt_str)
    if local.date() == today_date:
        todays.append((local, e))
```

## Decide whether each event is a meeting vs. a task block

Real meetings usually have at least one of these signals:

| Signal | Example |
|---|---|
| Other attendees in `attendees[]` (non-self emails) | `[cindilashley@gmail.com]` |
| `conferenceData.entryPoints[].uri` populated | `https://meet.google.com/adf-yveo-apx` |
| `transparency == "opaque"` (shows as busy) | omitted for focus holds |
| `creator.email` is NOT one of {{OWNER_NAME}}'s own addresses | `$USER@snapchat.com` may count as self if {{OWNER_NAME}} owns it |

If an event has none of these, it is almost certainly a personal task block (`task: water plants`, `Budget`, `sierra credit`) or a focus hold (`🔒 🎯 Focus time`). Per the SKILL.md "Exclude personal or family calendar blocks" rule, do not add these to `## Today`.

## Recurring reminder timing rules

The skill says: "Treat recurring reminders as due when the stored due timestamp lands on the current local date, or when the recurrence rule implies an occurrence on the current local date from that stored anchor date."

For `every <weekday>` reminders anchored on a specific weekday, do not promote them on weekends just because the anchor date's weekday still appears in the past — the recurrence is weekly on the named weekday, not daily. If today is Sunday and the reminder is `every Thursday`, do not promote.

## When the carryover is old but not stale

`order arthritis medication — carryover from 2026-06-29` was kept across 6 days because:
- It is a personal action item, not a past meeting.
- The SKILL.md "Preserve existing manually added open tasks in ## Today unless they are obviously stale past meetings" rule explicitly scopes "stale" to past meetings, not pending personal actions.
- Removing personal action items without {{OWNER_NAME}}'s explicit instruction could cause a missed medication refill.