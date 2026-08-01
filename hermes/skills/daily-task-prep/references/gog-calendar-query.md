# gog calendar query — quirks + working recipe (2026-07-24)

Captured during a real cron run. Replaces the broken shell snippet in
SKILL.md "Useful shell pattern" section.

## TL;DR

- `gog v0.10.0` (build `a92bd63`) calendar filter flags are unreliable in
  specific ways — see pitfalls below.
- Always **list calendars first**, then **query each candidate calendar
  individually** with explicit `--from`/`--to` and local JSON filter.
- The `--all --today` combination is the worst offender — it returns only
  long-spanning overlap events and silently drops day-bounded events.

## Known broken patterns (don't use)

```bash
# Returns only events that overlap "today" with very wide span (e.g. a
# multi-month trip event). Misses day-bounded meetings.
gog calendar events --all -a <email> --today --json --results-only

# --days filter appears to be ignored on some builds; returned every
# event in the window regardless of days=N. Pull wide, filter local.
gog calendar events --all -a <email> --days=1 --json --results-only

# Same as above: --from/--to works ONLY with a single calendarId arg.
# With --all, the same overlap bug appears.
gog calendar events --all -a <email> --from 2026-07-24T00:00:00-07:00 --to 2026-07-25T23:59:59-07:00
```

## Working recipe — per-calendar explicit window

```bash
# 1. List calendars on the account (one-time per session, gives IDs + names)
gog calendar calendars -a $USER@gmail.com --json --results-only

# 2. For each calendar likely to hold Jeffrey events, query a tight window
for cal_id in \
  "$USER@gmail.com" \
  "qclk155rem91cbcg1skco0auc0@group.calendar.google.com" \
  "4ogrrv9qf2m96pg0kk27v2okeg@group.calendar.google.com"; do
  gog calendar events "$cal_id" -a $USER@gmail.com \
    --from 2026-07-24T00:00:00-07:00 \
    --to 2026-07-25T23:59:59-07:00 \
    --json --results-only
done

# 3. Parse + filter locally (Python json.loads w/ strict=False if raw
#    control chars appear; jq works for clean output)
```

## Output caps to watch

- `terminal()` stdout is capped at ~50 KB. A 14-day `--all` pull returned
  81 KB and was truncated mid-JSON, breaking `json.loads`. Keep per-calendar
  pulls under ~30 KB each, or pipe through `jq -c '.[]'` first.
- `--max=100` is plenty per-calendar for any single day.

## Calendar list to check (Jeffrey's known set, 2026-07-24)

Owned or writable:
- `$USER@gmail.com` — primary
- `qclk155rem91cbcg1skco0auc0@group.calendar.google.com` — Fuji
- `4ogrrv9qf2m96pg0kk27v2okeg@group.calendar.google.com` — jeff PA Scheduling
- `7vt80l37nnnre3elo9k1g4k7s0@group.calendar.google.com` — Apartment Viewings
- `jleechanreclaim@gmail.com`
- `e65edb9d870582951ac40c72f35daff30e9c33b3321ffee4dc9e06509c35c0c3@group.calendar.google.com` — AIGen calendar

Read-only / subscribed (skip unless user asks):
- `mike.santiagorn@gmail.com`, `cv0s99a5bmtdpqdl7e7bvddnacusokfe@import.calendar.google.com` (Partiful), `lo05sdd74935gn7rtgie5krcls` (Best), `3r5q0rijuhm75kl0f22g2r8ec5sa8ekj@import.calendar.google.com` (Asana tasks), `en.usa#holiday@group.v.calendar.google.com` (Holidays in US), `qhcubiq13dsqbpuh805668vegv6cmj3t@import.calendar.google.com` (Partiful v2)

**Skip by default:** `family04573895333712838899@group.calendar.google.com` (Family — conflict source only, never a Jeffrey task), Holidays calendar, Asana tasks (those are tasks not events).

## Service-account calendar ($USER@your-project.com)

Currently returns 401 "unauthorized_client" on `calendars.list` —
domain-wide delegation isn't configured for calendar scope on this SA.
Don't include in the per-calendar sweep until that's fixed.

## Filter: "Jeffrey-owned today"

A calendar event counts as a `## Today` candidate only if ALL of:
- starts on today's local date (or all-day starting today, end-date-exclusive)
- organizer is `$USER@gmail.com` (Jeffrey), OR organizer is someone else but
  Jeffrey is an attendee AND the event isn't tagged family/lunch/walk/travel
- not transparent (`transparency != "transparent"`) — transparency events
  are reminders/blocks, not meetings

For our 2026-07-24 run, only the "Trip to Dublin" event (long-spanning)
overlapped — no real day-bounded meetings. So `## Today` ended up
carrying just the medication carryover.
