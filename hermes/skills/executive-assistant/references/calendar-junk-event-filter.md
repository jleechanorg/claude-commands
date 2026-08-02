# Calendar junk-event filter — multi-week carry-forward events

**Added 2026-07-17 16:04 PT sweep, verified.** `gog calendar events` with `--from` / `--to` does NOT filter by event duration — only by event START.

## Symptom

```
gog calendar events --all -a $USER@gmail.com \
  --from 2026-07-17T00:00:00-07:00 \
  --to 2026-07-20T00:00:00-07:00 \
  --max 50 --json --results-only
```

Returns the expected ~7 events in the window PLUS "Trip to Dublin | 2026-06-19 → 2026-08-23" — a 2-month multi-week event with start-time `2026-06-19T18:05:00-07:00` that overlaps the window's start boundary, so it leaks through. Verified in the 2026-07-17 16:04 PT EA sweep (38 days duration).

## Why

`gog`'s `--from` / `--to` filter `start.dateTime >= --from AND start.dateTime < --to`. They do NOT consider `end.dateTime`. Multi-week all-day-ish or travel events whose START is within the window but whose END extends far beyond leak through unchanged.

## Client-side fix

In the EA sweep Python parser, drop events whose duration exceeds a sanity threshold:

```python
from datetime import datetime
PT = timezone(timedelta(hours=-7))
for e in events:
    s = e.get('start', {})
    if not s.get('dateTime'):
        continue  # all-day events handled separately via P92
    start = datetime.fromisoformat(s['dateTime'].replace('Z','+00:00')).astimezone(PT)
    end_iso = e.get('end',{}).get('dateTime','')
    if not end_iso:
        continue
    end = datetime.fromisoformat(end_iso.replace('Z','+00:00')).astimezone(PT)
    duration_h = (end - start).total_seconds() / 3600
    if duration_h > 48:
        continue  # multi-week carry-forward junk
    # ... render as usual
```

**Threshold choice:** 48h catches "Trip to Dublin"-style multi-day travel events. Lower thresholds (24h) will be too aggressive — a legitimate 30-hour weekend trip with no time-zone boundary gets dropped.

## Alternative: drop events whose start is far before the window start

```python
WINDOW_START = datetime.fromisoformat('2026-07-17T00:00:00-07:00').astimezone(PT)
if start < WINDOW_START - timedelta(hours=24):
    continue  # event started more than 24h before the window — carry-forward junk
```

Catches both multi-week events AND shorter events that started yesterday or earlier (e.g. an "office hours 9-5 daily" recurring block that started a week ago).

## Existing precedents in the workspace

The `daily-task-prep` skill already filters "Trip to Dublin" explicitly. The EA sweep didn't have that filter until 2026-07-17 16:04 PT — the duration-check recipe above is the canonical pattern. If you see this filter missing in another calendar-reading skill, copy it from `~/.hermes/skills/executive-assistant/references/calendar-junk-event-filter.md` (this file).

## Related

- SKILL.md **P91** — same pitfall summary in the SKILL body
- SKILL.md **P92** — all-day events with time-sensitive names (different filter, same parser location)
- `references/all-day-event-time-extraction.md` — companion all-day event handling