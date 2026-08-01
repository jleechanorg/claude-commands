# 2026-07-30 noon ea-sweep session — lessons for future sweeps

This note captures concrete techniques that worked (or would have saved time) during the Thu Jul 30 12:02 PDT midday ea-sweep run on macOS 15.5. It is meant as a hands-on companion to the canonical `~/.hermes/skills/executive-assistant/SKILL.md` (which already encodes the resolver-recovery, destination-override, and bot/xoxp fallback rules).

## 1. Confirm where the brief lands BEFORE composing it

The cron prompt overrides the configured deliver channel. Run:

```bash
hermes cron list 2>&1 | grep -B 1 -A 6 -iE "(sweep|exec)" | head -60
```

Find the matching `clawchief:ea-sweep-hourly` row. For this session:

```
2f942031797e [active]
  Name:      clawchief:ea-sweep-hourly
  Schedule:  0 8,12,16,20 * * *
  Deliver:   slack:C0AJQ5M0A0Y     # = #ai-general
  Skills:    executive-assistant
```

If the prompt says "Deliver to #X" and `Deliver:` matches: no separate post needed; the scheduler's auto-delivery will route your final response. If they diverge, honor the prompt and note the divergence in the reply.

## 2. Token-source gotcha inside execute_code

`HERMES_SLACK_BOT_TOKEN` and `SLACK_USER_TOKEN` are set in `~/.bashrc` but bashrc uses an interactive guard that prevents them from re-exporting into non-interactive child shells. Inside `execute_code`'s Python subprocesses the env is **empty** even when `bash -c 'source ~/.bashrc && echo $HERMES_SLACK_BOT_TOKEN'` works from a terminal.

Reliable path:

```bash
bash ~/.hermes/scripts/launchd-env-wrapper.sh python3 /path/to/script.py
```

This calls `_extract_bashrc_var` for known tokens (canonical; matches what launchd cron jobs see). Verified working: `HERMES_SLACK_BOT_TOKEN` (58 chars `xoxb-9541820...`) + `SLACK_USER_TOKEN` (80 chars `xoxp-9541820...`) both surface correctly.

Anti-pattern (does NOT work):

```python
# inside execute_code, without wrapper
bot = os.environ["HERMES_SLACK_BOT_TOKEN"]   # KeyError — env is empty
```

## 3. Channel-access probe pattern

Before fetching history from each monitored channel, check `is_member`:

```python
chans = call("conversations.list",
             {"limit":"200","types":"public_channel,private_channel"}, bot)
for c in chans["channels"]:
    if c["id"] in monitored_ids:
        print(c["id"], c["name"], "is_member=", c.get("is_member"))
```

For $USER workspace the bot is a member of: `#all-$USER-ai` (C09GRLXF9GR), `#ai-general` (C0AJQ5M0A0Y), `#worldai` (C0AH3RY3DK6), `#life` (C0AMM2B4319), `#mcp-mail` (C0A0AG6EELB), `#worldai-alerts` (C0BCVG4F560), `#spicy-llm` (C0B99HSKBH6), `#agent-orchestrator` (C0ALSKLU9KM). If `is_member=false`, fall back to xoxp user token.

## 4. Service-account accounts can't read calendars

`gog auth list` shows two account types:

```
$USER@gmail.com                  oauth           (works for Calendar/Gmail)
$USER@your-project.com          service-account (Calendar returns 401 unauthorized_client)
```

Skip service-account calendars rather than report them as broken. Don't retry the API call — it will fail the same way.

## 5. Calendar untitled events are real busy blocks

`gog calendar events` returns ~10 timed events/day with empty `summary`, `description`, `attendees`, `creator`. These are auto-generated Outlook/work-block placeholders (no creator metadata means they're locally-authored focus-time blocks). Don't list them in the brief — surface only titled events plus the multi-week carry-forwards ("Trip to Dublin"-style junk that `--days=1` doesn't filter — drop them client-side when `start.dateTime` is more than 24h before window start).

## 6. Gmail inbox sweep — the highest-signal query

For a midday sweep, the single most useful query is:

```bash
gog gmail search "in:inbox newer_than:1d -category:promotions -category:social -category:updates" \
  --account $USER@gmail.com --max 25 --json --results-only
```

This pulls real correspondence (recruiters, finance alerts, deploy notifications, Cron failure emails, Uber receipts) while filtering marketing noise. Star/important queries miss deploy/cron emails because those don't get starred.

Cron failure emails from `[GCP Cron]` and `[Hermes]` show up here — surface them in the brief's Slack/deploys section if they're not already in #ai-general.

## 7. Recent Slack (last 16h, not just 12h)

Default "last 12h" misses the morning 9am cron failure that fires ~9:01 and the noon-run sweep at 12:00 itself. Use 16h cutoff:

```python
cutoff = time.time() - 16 * 3600
```

## 8. System probes (added 2026-07-29 to canonical SKILL.md)

```bash
df -h / | head -3       # surface Avail < 30G as Risky
uptime                  # load avg > 10 (40-user laptop) as Risky
hermes status 2>&1 | head -25   # missing API keys as Risky
```

## 9. Past abort evidence lives in #ai-general history

If a previous sweep aborted (wrong-machine scenario, OAuth failure, missing tokens), the abort message is in the channel history. The 12h-or-16h history scan will pick it up. Don't trust that absence of recent abort means current run will succeed — re-verify.

## 10. LLM-provenance caveat is mandatory

Every brief must end with:

```
This was generated from another LLM and not the actual user, so feel free to push back if you disagree and we can discuss.
```

Per SOUL.md `## COMMIT: llm-provenance-caveat`. Skipping it makes the brief indistinguishable from a real operator message and is a SOUL.md violation.

## 11. Common pitfalls in this domain

| Symptom | Cause | Fix |
|---|---|---|
| `conversations.history` returns `invalid_auth` from execute_code | Token not exported into Python subprocess | Wrap with `bash ~/.hermes/scripts/launchd-env-wrapper.sh` |
| `gog calendar events` returns `401 unauthorized_client` | Service-account can't read Calendar | Skip that calendar; use oauth account |
| `json.loads` raises on Slack API response | Raw `\n` (0x0a) in message text | `re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', raw)` before parse |
| Brief lands in operator DM instead of #ai-general | Prompt didn't override, scheduler defaulted | Confirm `Deliver:` field in `hermes cron list` |
| `skill_view('executive-assistant')` returns ambiguous | Two skills share the name (canonical + hermes-imports overlay) | Use `skill_view(name='hermes-imports/executive-assistant')` or `read_file ~/.hermes/skills/executive-assistant/SKILL.md` |