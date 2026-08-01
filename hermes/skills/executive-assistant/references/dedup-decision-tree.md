# EA Sweep Dedup Decision Tree

Compact pseudocode for "full re-brief vs delta vs [SILENT]" — extracted from P41, P46, P52, P53 of the parent SKILL.md. Run this BEFORE composing the brief.

## Step 1 — find the last bot brief in DM

```
mcp__slack__conversations_history(channel_id=D0AFTLEJGJU, limit=10)
filter rows where BotName == "hermes"   # not UserID — bot self-replies in operator threads also match U0AEZC7RX1Q
last_brief = max(rows by ts)
```

If no bot brief found in last 24h, skip to step 4 (full sweep).

## Step 2 — compute gap

```
gap_minutes = (now_unix_ts - last_brief.ts) / 60
gap_hours = gap_minutes / 60
prior_day = date_of(last_brief.ts)   # local PT
today = local_date_today
```

## Step 3 — pick the mode

```
if gap_minutes < 30:
    return SILENT                        # P50/P52 — same-sweep repeat

if prior_day != today:
    return FULL_REBRIEF                  # P41 — cross-day gap (e.g. 20:00 → 08:00)

if gap_hours >= 4:
    return FULL_REBRIEF                  # P46 — same-day ≥4h gap (08:01 → 16:01)

# Sub-30-min OR sub-4h same-day: check material change
material = OR(
    new calendar event starting within next 2h,
    new IMPORTANT-marked email from human sender,
    new operator top-level ask in monitored channel,
    deploy failure,
    system-status red,
    on-call ping
)
if material:
    return DELTA                        # 2-3 line update, not full re-brief
else:
    return SILENT
```

## Step 4 — what "full re-brief" means

- Pull calendar (next 24h, PT), Gmail (flagged + IMPORTANT + unread-newer-than-1d), all monitored Slack channels (history + replies for open threads), system probes (uptime, disk data-volume, processes, launchd jobs, port-8643 health, cron list, PR list).
- Compose ~5-8 KB brief (curl path, not MCP — P50).
- Always include the open operator asks, not just "nothing new" — the operator wants to know what's still pending.

## Step 5 — what "delta" means

Tight 3-5 line message:
```
:spiral_calendar_pad: *Delta brief — Tue Jul 7, 12:02 PDT*
4h gap since 08:03 PDT morning brief. No new operator asks.
System delta: load X/Y/Z (vs baseline), disk X Gi free, N procs, port-8643 status.
Material change: <one bullet or "none">.
Want me to: <one offer or "skip next two sweeps?">
```

## Step 6 — what [SILENT] means

Output the literal string `[SILENT]` and nothing else. The cron delivery model suppresses the message. Use this aggressively for sub-30-min repeats — re-posting spams the DM.

## Watch-outs

- **`BotName=hermes` filter** is canonical, NOT `UserID=U0AEZC7RX1Q`. The bot's own self-replies in operator threads also have UserID=U0AEZC7RX1Q but empty BotName. Filtering on UserID over-counts and inflates the apparent last-brief time.
- **Top-level post, not thread reply.** Per P51, pass `{"channel":"D0AFTLEJGJU","text":...}` and OMIT `thread_ts`. Threading hides the brief under the prior operator message.
- **Curl path for ≥3KB briefs.** Per P50, if the payload is ≥ ~3,000 chars OR > ~20 newlines OR > ~10 emoji shortcodes, post via curl from the start. Don't try MCP first.