---
name: daily-task-prep
description: "Prepare {{OWNER_NAME}}'s task list for the day using `~/.hermes/workspace/tasks/current.md` plus his calendars. Use when a cron or direct request asks to prepare today's tasks before {{OWNER_NAME}} starts work; when recurring weekday tasks, due-today backlog items, and {{OWNER_NAME}}-owned meetings/calls should be added to `## Today`; or when the task list needs a safe early-morning refresh without overwriting {{OWNER_NAME}}'s manual priorities."
---

# Daily Task Prep

Use `~/.hermes/workspace/tasks/current.md` as the canonical live task file.

## Goal

Quietly prepare today's `## Today` section before Jeffrey wakes up.

## Concrete identifiers (resolved 2026-07-07)

The `{{...}}` placeholders in the original template do NOT auto-resolve in this environment. Use these values directly:

- **Owner:** Jeffrey ($USER) — see `~/.hermes/workspace/USER.md`, `MEMORY.md`
- **Primary calendar (verified working):** `$USER@gmail.com` via `gog calendar events`
- **Cindil calendar:** `gog calendar events -a cindilashley@gmail.com` returns a JSON parse error in this env. Detect shared events via the primary's `attendees` array instead of querying cindilashley directly.
- **Todoist CLI:** NOT installed on this host — skip Todoist due-today pulling entirely. Do not retry / fail-loop on it.
- **Google Tasks API:** returns 403 insufficientPermissions on this account — skip.
- **Maid / cleaner / pool / street-cleaning / gardener / dmv:** recurring household bookings on the primary calendar. EXCLUDE per the personal/family rule below.

If the user adds a work calendar, extend this block rather than re-deriving from `USER.md` each session.

## Core rules

- Preserve existing manually added open tasks in `## Today` unless they are obviously stale past meetings.
- **Stale-row cleanup (added 2026-07-07):** A `## Today` row whose `— YYYY-MM-DD HH:MM–HH:MM TZ` time block is fully in the past (date < today) is stale and should be removed in the same edit. Carryover lines (e.g. `— carryover from YYYY-MM-DD`) are human-flagged as still-active and stay even when the anchor date is old. When in doubt, keep.
- On weekdays, treat `## Every weekday` as the recurring seed list.
- On weekends, do **not** auto-add `## Every weekday` items unless Jeffrey explicitly asked.
- Promote items due today from `## Backlog with due date` into `## Today`, and remove the backlog copy in the same edit.
- Scan `## Recurring reminders` and add any reminder that is due today into `## Today` without deleting the recurring source item.
- Add Jeffrey-owned meetings and calls for today to `## Today`.
- Exclude personal or family calendar blocks, lunch/walk holds, travel holds, maid/cleaner appointments, pool service, street cleaning, and appointments that belong to another household member or the family unless Jeffrey explicitly asks for them.
- Do not duplicate tasks that already exist with equivalent wording.
- Keep the `{{ASSISTANT_NAME}}:` ownership marker (e.g. `Hermes:`) for tasks assigned to me.
- Update the file's `Last updated` timestamp.
- Stay silent unless something needs human attention.

## Preparation workflow

1. Read `tasks/current.md`.
2. Determine whether today is a weekday.
3. Build the candidate `## Today` list from:
   - current open `## Today` tasks worth carrying forward
   - weekday recurring items from `## Every weekday` if today is Monday-Friday
   - items in `## Backlog with due date` that are due today
   - items in `## Recurring reminders` whose recurrence makes them due today
   - today's {{OWNER_NAME}}-owned meetings/calls from calendar
4. Remove duplicates by normalized task text while keeping the most specific wording already present in the file.
5. Reorder the open tasks in this order:
   - existing explicit priority tasks
   - due-today items
   - recurring operating tasks
   - meetings/calls in time order
6. Keep completed items untouched unless a cleanup is obviously safe.
7. Write back only the minimal necessary edits.

## Calendar workflow

Use `gog` via shell to inspect {{OWNER_NAME}}'s visible calendars before adding meeting tasks.

### Discover which accounts are configured first

Run `gog auth list` BEFORE iterating calendar accounts — only query accounts that the tool actually has credentials for. Iterating placeholder emails wastes calls and pollutes logs with "No auth for …" errors.

```bash
gog auth list
## Calendar workflow

Use `gog` via shell to inspect Jeffrey's visible calendars before adding meeting tasks.

Check these calendars when visible:
- `$USER@gmail.com` — primary (verified working; use this as the single source of truth)
- `cindilashley@gmail.com` — direct query returns a JSON parse error; detect shared events via the primary's `attendees` array
- Family calendar only as a conflict source, not as a source of Jeffrey tasks

Only add calendar items that Jeffrey himself is expected to attend.

Useful shell pattern (verified 2026-07-07):

```bash
# List events for today (use the primary only)
gog calendar events --all -a $USER@gmail.com --days=1 --max=100 --json --results-only

# Or the human-readable table view (catches the 7-day window)
gog calendar list
```

Filter JSON to Jeffrey-owned events with a small Python check (see `scripts/today-stale-check.py` for the reusable helper).

## Stale-row check helper

`scripts/today-stale-check.py` deterministically identifies which `## Today` rows should be removed because their trailing timestamp is in the past. Run it before editing `current.md` so the cleanup is reviewable, not just-in-time judgment.
```

### Pitfalls

- **`--all` is required, not optional.** Without it, `gog` only returns events from a single default calendar (typically the Gmail personal calendar) and silently misses everything on work, Snapchat, Reclaim, family, and other connected calendars. Always pass `--all`, then post-filter in Python by `start.dateTime` (or `start.date` for all-day events) in {{OWNER_NAME}}'s local timezone. See `references/calendar-discovery.md` for the full parsing recipe.
- **Transparent + self-organized + no attendees = task block, not meeting.** Items like `task: water plants`, `Budget`, `sierra credit`, `🔒 🎯 Focus time` are personal task blocks or focus holds — even when they fall in {{OWNER_NAME}}'s working hours. Do NOT add them as meeting tasks. The skill's "Exclude personal or family calendar blocks" rule covers these.
- **Distinguish meeting signals:** real meetings typically have either (a) other attendees, (b) a `conferenceData.entryPoints[].uri` (Meet/Zoom link), (c) `transparency: opaque` (shows as busy), or (d) a creator email that is NOT one of {{OWNER_NAME}}'s own addresses. Lacking all four, treat the event as a task block and skip it.

If calendar access fails on all configured accounts, still do file-based prep and only notify {{OWNER_NAME}} if the failure matters.

## Calendar event classification

Not every event on the calendar is a task. Filter into one of these buckets before adding anything to `## Today`:

| Bucket | Action | Examples |
|---|---|---|
| Owner-attended meeting/call | ADD to `## Today` (chronological) | "Cat sitter meeting", "1:1 with X" |
| Owner all-day recurring personal event | ADD to `## Today` (all-day section at top of meetings) | "Mom's Bday.", "Anniversary" |
| Imported calendar event (organizer = `*import.calendar.google.com` or another person) | SKIP, but flag as a CONFLICT if it overlaps an existing `## Today` slot | Partiful imports, friend-shared events |
| Auto-block / focus time (organizer = `reclaim.ai`, `clockwise`, `motion.ai`) | SKIP — these are not tasks | "Focus time", "Focus block" |
| Public holiday (organizer = `en.usa#holiday@group.v.calendar.google.com` etc.) | SKIP — no action needed | "Independence Day", "Christmas" |
| Multi-day travel plan that spans today | SKIP — not today's work | "Trip to Dublin" running Jun–Aug |
| Lunch / walk / personal block with no external attendee | SKIP unless {{OWNER_NAME}} explicitly asks | — |

### Pitfall: UTC events look like "tomorrow" but are today

Calendar APIs return `start.dateTime` in the event's own timezone or UTC. Events like `2026-07-05T00:00:00Z` are actually **2026-07-04 17:00 PT** (during DST). Before deciding an event is "tomorrow", convert `Z`-suffixed timestamps to local time and re-check. Use Python or `date -u -d`:

```python
import datetime
utc = datetime.datetime.fromisoformat("2026-07-05T00:00:00+00:00")
pt = utc.astimezone(datetime.timezone(datetime.timedelta(hours=-7)))
# → 2026-07-04T17:00:00-07:00
```

If the converted local time lands on today AND the event is owner-attended (not imported), treat it as today's event.

### Pitfall: imported events that overlap an existing block

If an imported calendar event (Partiful, friend-shared, etc.) lands on today's date in local time AND overlaps a slot already in `## Today` (e.g. the cat sitter call 17:00–19:00), it's a conflict source, not a task. Surface it as a heads-up in the final reply only if it would genuinely surprise {{OWNER_NAME}} — otherwise skip silently.

## Task text rules

- Use concise one-line tasks.
- Keep the existing task wording when it is already good.
- Use `YYYY-MM-DD` for all-day due dates and `YYYY-MM-DD HH:MM TZ` for timed due dates.
- Meeting task format should match the live file's existing style.
- If a backlog due-date item is promoted into `## Today`, remove the backlog copy immediately.
- For recurring reminders, keep the recurring source entry in place and only add the due instance into `## Today`.
- Use recurring reminder lines in this shape when present: `- [ ] Task — due YYYY-MM-DD[ HH:MM TZ] — recurs <period> every <n>`.
- For calendar all-day events (e.g. recurring birthdays), use the literal event summary as the task title, followed by the date — keep it short and recognizable so {{OWNER_NAME}} spots it: `- [ ] Mom's Bday. — 2026-07-04 (all-day)`.

## Safety

- Do not wipe `## Today` just to rebuild it.
- Treat recurring reminders as due when the stored due timestamp lands on the current local date, or when the recurrence rule implies an occurrence on the current local date from that stored anchor date.
- For all-day reminders, compare by local date only.
- If calendar access fails, still do file-based prep and only notify {{OWNER_NAME}} if the failure matters.
- If the file structure has drifted, adapt to the live file instead of forcing a full reformat.
- If nothing needs to change, do nothing.
