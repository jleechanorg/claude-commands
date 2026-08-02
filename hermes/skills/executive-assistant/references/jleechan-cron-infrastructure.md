# Jeffrey's Cron Infrastructure — Verified 2026-07-16

Companion to `executive-assistant/SKILL.md`. Captures the live cron-job + delivery plumbing that the canonical sweep (`clawchief:ea-sweep-hourly`) depends on. Read this BEFORE running the sweep if you've never run it before, OR if a prior sweep reported `not_in_channel` / DM-misroute errors.

## The cron job

| Field | Value |
|---|---|
| Name | `clawchief:ea-sweep-hourly` |
| Job ID | `a790a5b54e61` |
| Schedule | hourly (StartInterval 3600s) — but actual gaps vary 4h–16h due to launchd flapping |
| Agent | `mcp_agent_mail` (bot identity, UserID `U0A4G7LDJ4R`) |
| Deliver target | `slack:D0A418NEHHC` (Jeff's DM with the bot) |
| Last known run | `2026-07-16T15:03Z` (this sweep), prior `2026-07-15T23:05Z` |

Verify with:
```bash
hermes cron list --name ea-sweep-hourly
# OR if hermes cron not available:
hermes cron list 2>&1 | grep -A1 ea-sweep
```

## DM channel IDs (verified)

| Channel | ID | Notes |
|---|---|---|
| Jeff's DM with `mcp_agent_mail` bot | `D0A418NEHHC` | **Canonical delivery target.** Verified via 3 prior brief archives (`~/.hermes/memory/briefings/2026-07-15/*`, `2026-07-14/*`). |
| Jeff's alternate DM (legacy) | `D0AFTLEJGJU` | Mentioned in env-var hints but NOT the active delivery target. Don't post here. |

The `$JLEECHAN_DM_CHANNEL` env var is **not set** in cron-launched sessions. Always read the canonical ID from a prior brief archive or the cron's `Deliver:` field — never guess.

## Brief archive path

```
~/.hermes/memory/briefings/YYYY-MM-DD/HHMM-ea-sweep.md
```

Verified 2026-07-16 — the cron writes one file per run. The first 5 lines of the file carry: timestamp, dedup header, DM channel ID, memories-used line. Use `head -5` to verify the cron landed in the right channel.

## Known channel-lockout state (verified 2026-07-15)

Bot `mcp_agent_mail` returns `not_in_channel` for:

| Channel | ID | Workaround |
|---|---|---|
| `#needs-jeff` | `C0BGM3A4ZC0` | xoxp fallback for reads; bot CANNOT post there |
| `#ai-general` | `C0AJQ5M0A0Y` | xoxp fallback for reads; bot CANNOT post there |
| `#worldai-alerts` | `C0BCVG4F560` | xoxp fallback for reads; bot CANNOT post there |
| `#agent-orchestrator` | `C0ALSKLU9KM` | xoxp fallback; bot CANNOT post |

Fix: `curl -X POST "https://slack.com/api/conversations.invite" -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" -d "channel=C0AJQ5M0A0Y&users=U0A4G7LDJ4R"` for each — but DO NOT do this without explicit user approval; re-inviting the bot can trigger auth-test rate-limit issues.

## Calendar accounts (verified 2026-07-16)

| Account | Purpose | How to filter |
|---|---|---|
| `$USER@gmail.com` | Primary work | `gog calendar events --all -a $USER@gmail.com` |
| `jleechanreclaim@gmail.com` | Reclaim focus blocks (untitled summaries + `:dart: Focus time`) | filter by `organizer.email == jleechanreclaim@gmail.com` |
| `stu3mschtqnk7o0il9s6trnfds@group.calendar.google.com` | Family / Therapy Cindil | filter by `organizer.email == stu3mschtqnk7o0il9s6trnfds@group...` |
| `brandon.pollack@polymarket.com` | Shared invites | look for non-self organizers |

## Gmail filter recipe (verified 2026-07-16)

```bash
# Starred (operator-curated priority)
gog gmail search 'is:starred' --json --results-only --max=20

# Unread last 24h (broader sweep)
gog gmail search 'is:unread newer_than:1d' --json --results-only --max=20

# Priority keywords (recruiter/legal/finance/urgent)
gog gmail search '(recruiter OR offer OR contract OR invoice OR legal OR urgent OR "action required" OR "please review" OR interview) newer_than:1d -is:starred' --json --results-only --max=15

# IMPORTANT label is unreliable in 24h windows for this account — skip it.
```

## Pitfall log (chronological)

| Date | Symptom | Fix |
|---|---|---|
| 2026-07-15 ~08:00 | Cron `Deliver:` was `slack:C0AMM2B4319` (#life) instead of DM | Skill pitfall **P37** patched: cron re-wired to `slack:D0A418NEHHC` |
| 2026-07-15 ~16:04 | Bot locked out of `#needs-jeff` / `#ai-general` | xoxp fallback recipe now standard; bot invites are NOT auto-fired |
| 2026-07-15 ~20:00 | All-day event "Client tech" swallowed time | Skill pitfall **P42**: extract from all-day row when an explicit time appears elsewhere |
| 2026-07-16 ~08:00 | `gog calendar events --all --today` returned ALL events | Skill pitfall (this patch): post-filter by `start.dateTime.startswith(today)` |