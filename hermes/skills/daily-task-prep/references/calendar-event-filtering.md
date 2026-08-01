# Calendar Event Filtering Reference

Companion to `daily-task-prep` SKILL.md. Captures the deterministic filters that decide whether a `gog calendar events` result becomes a `## Today` line.

## Decision tree (apply per event in order)

```
1. visibility == "private" AND summary == "" AND no organizer/attendees?
   → DROP. Personal time block.
   Fingerprint: iCalUID ends @google.com (not @group.calendar.google.com),
   no `organizer` key, no `attendees` key.

2. transparency == "transparent"?
   → DROP. Travel / OOO block (e.g. "Trip to Dublin").

3. organizer.email belongs to another household member
   AND Jeffrey is a guest (not organizer)?
   → DROP. (E.g. "Therapy Cindil" organized by a Cindil-side calendar.)

4. Source calendar (`iCalUID @group.calendar.google.com`) is the family
   calendar (`family04573895333712838899@group.calendar.google.com`)?
   → DROP. Family calendar = conflict source only.

5. Recurring reminder whose `## Recurring reminders` source line is
   tagged "<Name>-owned" (not Jeffrey-owned)?
   → DROP. Keep the recurring source line; do NOT add a ## Today instance.
   Verified pitfall: "Therapy Cindil — Cindil-owned" — adding it would
   make Jeffrey's morning list look like HE has therapy.

6. Otherwise: candidate. Check Jeffrey is in `attendees` OR is organizer
   OR event is on his primary calendar. Add to ## Today in time order.
```

## Field fingerprints (verified 2026-07-16)

| Field | Personal block | Real meeting |
|---|---|---|
| `summary` | `""` (empty) | non-empty string |
| `visibility` | `"private"` | default/missing/`"public"` |
| `organizer` | absent | object with `email` |
| `attendees` | absent | array (often `[{"self": true, "email": "$USER@gmail.com"}]`) |
| `transparency` | absent or `opaque` | `opaque` (default for meetings) |
| `iCalUID` | ends `@google.com` | `@group.calendar.google.com` for shared, `@google.com` for primary |
| `hangoutLink` | absent | present for video meetings |

## Common false-positive traps

- **Recurring events with `recurringEventId` set**: the per-occurrence row has its own iCalUID (with date suffix). The decision rule should look at the parent `recurringEventId`'s organizer, not the occurrence's organizer. Currently `gog calendar events` returns the occurrence row; check the source-of-truth `## Recurring reminders` line in the task file when present.

- **All-day events**: `start.date` is a date string (`YYYY-MM-DD`), not a dateTime. Compare by local date, not datetime.

- **Cross-timezone events**: `start.dateTime` includes `-07:00` offset for America/Los_Angeles. `timeZone` field may differ (the calendar's default vs the event's). Trust `dateTime` offset for ordering.

- **Past-meeting carryover tasks** (e.g. "order arthritis medication — carryover from 2026-06-29"): do NOT auto-remove. The calendar may also show a separate all-day block on today's date — those are reminders, not duplicate tasks. If the live task wording already mentions "carryover from YYYY-MM-DD", preserve it; do not silently drop.