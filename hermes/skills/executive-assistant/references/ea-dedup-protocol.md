# EA Sweep Dedup Protocol — Evidence & Examples

Reference for the **Dedup discipline (concrete protocol)** section in `SKILL.md`. Captures reproducible behavior seen across `clawchief:ea-sweep-hourly` runs, including the dedup-hit case (2026-07-05 10:40 PDT) that motivated this addition.

## TL;DR

`ea-sweep-hourly` posts a brief to DM `D0AFTLEJGJU` only when (a) it has been ≥30 min since the last brief AND (b) something materially changed. Otherwise: `[SILENT]`.

## Why this matters

The cron flywheel is dense. On 2026-07-05 the `#life` channel showed back-to-back reminders from many cron jobs in the same minute window:

```
17:32:43Z  ea-sweep-hourly posted a brief → DM
17:31:25Z  ea-sweep-hourly would have re-run already...
17:30:16Z  ea-sweep-hourly posted again
17:21:45Z  Life digest posted → #life (different cron)
17:21:12Z  ea-sweep-hourly "Brief delivered successfully" narration
```

Without an explicit dedup check, an hourly cron plus an "every minute" cron plus ad-hoc triggers easily produces 6–10 briefs/day, each ~2–4 KB, diluting the signal of the canonical brief.

## The four-step dedup

| Step | Tool | What to look for | On fail |
|---|---|---|---|
| 1. Resolve DM channel | `echo $JLEECHAN_DM_CHANNEL` | `D0AFTLEJGJU` | If unset, source `~/.bashrc`; do not post anywhere else |
| 2. Read DM history | `conversations_history(channel_id=D0AFTLEJGJU, limit=5)` | most recent `UserID=U0AEZC7RX1Q` row's `ts` | If query unavailable, fall back to Path B curl with `HERMES_SLACK_BOT_TOKEN` |
| 3. Time gate | `(now − last_brief_ts) ≥ 30 min?` | True → continue; False → `[SILENT]` | n/a |
| 4. Content gate | diff prior brief's calendar/email/slack set vs current | No delta → silent or 2-line delta | Material delta → full re-brief |

## What counts as "material change"

Examples (each is sufficient on its own to justify a full re-brief even within 30 min):

- New calendar event starting in next 2h that wasn't in prior brief
- New IMPORTANT / CATEGORY_PERSONAL email from a human sender
- New operator top-level ask in any monitored channel (especially unresolved threads in `#all-$USER-ai`, `#jleechanclaw`, `#worldai`, `#agent-orchestrator`, `#life`)
- Deploy FAILED → SUCCESS pair (deploy-failure-then-recovered)
- System status red (load avg > 4 baseline, disk < 20% free, gateway down, AO worker archived)
- On-call ping from gateway watchdog / launched monitor

What does NOT count as material change:

- Same calendar events with shifted minutes
- Same flagged emails, same senders, same subjects (even with new MsgID for forwarding/reply)
- Cron-job narration posts to `#life` or other channels (those are other cron's work)
- Updates to PR comments / CI status that don't change JEFFREY's action queue
- New AO worker session start without a corresponding blocked-PR state change

## Pitfalls (verified in production)

### 1. Cron-prompt self-narration ≠ Slack artifact

```
"Cronjob Response: clawchief:ea-sweep-hourly
... Briefing delivered to DM D0AFTLEJGJU at 17:30 UTC"
```

This text is in the *next* tick's `cronjob action=run` payload, NOT a Slack post. It just says the prior tick SAID it delivered. Trust `conversations_history` over the cron prompt.

### 2. `[SILENT]` is the right answer for hourly dedup hits

Many sessions want to "produce something useful" — but the most useful thing an hourly cron can do on a dedup hit is **nothing**. The DM is the user's morning signal channel; flooding it with redundant briefs makes the real signal harder to find. Output `[SILENT]` as the literal cron reply and exit.

### 3. The 30-min window is sliding, not per-day

If 09:00 brief lands, 09:30 tick may post (no prior in window but content is fresh), but 10:00 / 10:30 / 11:00 ticks all stay silent unless something material changed. The window resets each time a brief lands.

### 4. Reply to operator mid-window → re-arm once

If JEFFREY posts a top-level message in a monitored channel (e.g. `#life`) within the 30-min window, that's material — but a fast cron tick that catches it should still respect the DM-dedup unless explicitly opening a new action thread. Use `mcp__slack__conversations_history` on the operator's channel, not on the DM, when classifying mid-window operator asks.

## Worked example: 2026-07-05 10:40 PDT dedup hit

| Tick | Time | DM-channel last brief | Decision | Result |
|---|---|---|---|---|
| ea-sweep-hourly | 10:30:08 PDT | (none in window) | Post full brief | MsgID 1783272608.899929 |
| ea-sweep-hourly | 10:40:54 PDT | 1783272608.899929 (≈10 min ago) | Compare sets: identical | `[SILENT]` ✓ |
| ea-sweep-hourly (next) | 11:30 PDT TBD | (depends) | Will run full sweep → likely post brief | TBD |

Calendar set at the dedup hit was identical:
- Today: Budget 17:00–18:00 (in progress), water plants 20:30–23:45, sierra credit 21:00
- Tomorrow: DMV 08:00–12:00, Mizraim workday 10:00–13:00, 3 untitled events, water jugs 21:00

Email set at the dedup hit was identical (Christina Disney gift card, Uphold verify-email, Mom's shared wedding-speech doc — all from prior brief). Slack action items: same 5b-leak safety-net alert resolution, same PR babysits, same agento respawn-cap escalations.

→ No material change → `[SILENT]` is correct.

## Companion artifacts

- `~/.hermes/workspace/tasks/current.md` — daily-task-prep's persistent task list, touched by `clawchief:daily-task-prep` cron
- `~/.hermes/memory/briefing-YYYY-MM-DD.md` — archived briefs (per prior convention)
- DM `D0AFTLEJGJU` thread — canonical delivery target

## When to escalate the dedup rule itself

If the user complains "I missed something important" or "you're not posting often enough":
1. Check `conversations_history(D0AFTLEJGJU, limit=20)` — was there a gap > 4h with material change?
2. If yes, the dedup is too aggressive for their cadence — back off to posting every 60 min on the dot regardless of content.
3. If no, the missed item was in a channel the EA sweep doesn't monitor — extend §3 of `SKILL.md` (Slack action items) to include that channel.
