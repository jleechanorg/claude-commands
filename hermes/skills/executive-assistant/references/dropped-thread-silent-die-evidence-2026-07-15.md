# Dropped-thread watcher silent-die — evidence from 2026-07-15 08:00 PT sweep

## Symptom

A 16h gap between EA briefs (Tue 16:02 PT → Wed 08:00 PT) and **13 unanswered $USER asks** piled up across `#worldai` (5) and `#all-$USER-ai` (8) with `reply_count == 0` (zero replies on every single one). The previous brief at 16:02 PT flagged the same issue.

## Diagnostic evidence

```text
$ launchctl print gui/$(id -u)/ai.hermes.schedule.dropped-thread-watcher | grep -E "state|last exit"
state = not running
last exit code = 0

$ launchctl print gui/$(id -u)/ai.hermes.schedule.dropped-thread-followup | grep -E "state|last exit"
state = not running
last exit code = 0
```

Both launchd jobs are silent-died with exit code 0. No error, no log line, just gone.

## Root cause

Same pattern as the 2026-07-03 codexbar incident documented in SOUL.md `## COMMIT: dropped-thread-watcher-of-watchers`. Root cause: launchd treats `SuccessfulExit=false` plist with an exit-0 result as "successfully completed" and skips subsequent ticks. The fix landed in SOUL.md but the underlying plists still show the bug.

## Surface this evidence supports

The 2026-07-15 08:00 PT brief surfaced this as the **#1 ranked action item** with suggested dispatcher (AO worker on `fix/hermes-dropped-thread-watcher-resurrect`). The brief also ranked 12 other unanswered asks, but items 1/2/3 share the bot-lockout root cause — fix once, unblock all 13.

## Why this lives under `executive-assistant`

The EA sweep is the canonical surface that **detects** this kind of backlog (it's the only cron that periodically scans Tier-1 channels for unanswered operator asks and reports the gap). Future EA sweeps should:
1. **Always compare** `now - last_brief_ts` against the cron schedule — if gap > 1.5× the schedule interval, the dropped-thread-watcher probably silently died.
2. **Surface the silent-die state explicitly** in the brief footer (`dropped-thread-watcher=not running`) so the operator can act without re-investigating.
3. **Treat >5 unanswered $USER posts as a P0** signal (vs the existing `≥3 unanswered + ≥2 channels` threshold from P52), because the 16h-gap evidence shows the bot-lockout case generates many asks in a short window.

## Workaround (until the watcher plists are fixed)

For an ad-hoc EA sweep triggered outside the schedule, the cron destination field in the trigger can deliver to DM directly. But the recurring schedule (`0 8,12,16,20 * * *`) is mis-wired to post to `#life` instead of DM (see SKILL.md pitfall added 2026-07-15). Until the schedule fix lands, EA sweeps during the 12:00 / 16:00 / 20:00 PT ticks do not reach the operator.