# All-Day Event Time-Extraction Recipe

## Problem

`gog calendar events` returns `date` (not `dateTime`) for all-day events. A naive `HH:MM — title` formatter strips these to:

```
- all-day — Client tech at 11am
```

The actual time ("11am") is buried in the title and invisible at a glance. Operator misses the scheduling conflict.

## Symptom

Calendar event with:
- `start.date = "2026-07-15"` (no `dateTime`)
- `summary = "Client tech at 11am"`
- `end.date = "2026-07-16"` (multi-day, but really just a reminder)

Rendered to brief as "all-day — Client tech at 11am" — operator reads it as "sometime today, no urgency", when it actually means "block 11am Wed".

## Detection regex

```python
import re

TIME_PATTERNS = [
    r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b',                  # 11:30 / 11:30am
    r'\b(\d{1,2})\s*(am|pm)\b',                           # 11am / 7 pm
    r'\b(morning|afternoon|evening|night|noon)\b',        # vague
    r'\bat\s+(\d{1,2})\b',                                # "at 11"
    r'\bby\s+(\d{1,2})\b',                                # "by 5"
]

def extract_time_from_title(title: str) -> str | None:
    t = title.lower()
    # HH:MM with optional am/pm
    m = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b', t)
    if m:
        h, mm, ap = m.group(1), m.group(2), m.group(3)
        h = int(h)
        if ap == 'pm' and h < 12: h += 12
        if ap == 'am' and h == 12: h = 0
        return f"{h:02d}:{mm}"
    # bare H am/pm
    m = re.search(r'\b(\d{1,2})\s*(am|pm)\b', t)
    if m:
        h, ap = int(m.group(1)), m.group(2)
        if ap == 'pm' and h < 12: h += 12
        if ap == 'am' and h == 12: h = 0
        return f"{h:02d}:00"
    # "at 11" without am/pm → ambiguous, skip unless we can infer
    return None
```

## Render recipe

When the time is extractable, REPLACE the all-day row with a time-anchored row + warning emoji:

```python
def render_event(ev, today, tomorrow):
    summary = ev.get('summary') or '(no title)'
    start = ev.get('start', {})
    end = ev.get('end', {})

    # All-day detection
    if 'date' in start and 'dateTime' not in start:
        # Try to extract a time from the title
        extracted = extract_time_from_title(summary)
        if extracted:
            # Surface under Now/Today with warning — and keep the all-day row
            return [
                f"  - {extracted} — {summary} :warning: (from all-day event)",
                f"  - all-day — {summary}",
            ]
        return [f"  - all-day — {summary}"]
    # ... normal time-anchored handling
```

## Verified example: 2026-07-15 all-day

Before:
```
- all-day — Client tech at 11am
```

After:
```
- 11:00 — Client tech :warning: (from all-day event)
- all-day — Client tech at 11am
```

Operator now sees the 11am anchor in the time-ordered Today/Upcoming list, with the `:warning:` flag making it clear the time came from the title not the API.

## Edge cases

- **Multi-day all-day events** (e.g. "Trip to Dublin" spanning 5 days) — still all-day, no extracted time, render as `all-day — Trip to Dublin (5-day)`.
- **No time in title** ("Arthritis med") — keep as `all-day — Arthritis med`.
- **Vague time in title** ("morning", "evening") — extract as `morning — Title` or `evening — Title` (don't pretend to know the hour), keep the all-day row.
- **Already has dateTime in API** (not actually all-day, but title mentions a time) — DON'T re-extract; trust the API.

## Reference

- SKILL.md P42 — the all-day visual flag pitfall (the brief that motivated this)
- The 2026-07-14 08:02 PT sweep: "Client tech at 11am" Wed was hidden in the all-day bucket. Caught at write-time, fixed in the next render.
