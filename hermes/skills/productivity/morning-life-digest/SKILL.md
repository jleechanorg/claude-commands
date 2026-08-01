---
name: morning-life-digest
description: Generate the morning life-channel Slack digest — fetch unread Gmail, query next-24h Calendar across all known accounts, filter for "important" items, post to #life. Use for the `life:daily-important-email-calendar-8am` cron and any future variant (different time/channel, "morning brief" cron, "what's on my plate today" prompt) that hits the same fetch → filter → post pipeline. Also use when a user asks for a morning brief filtered to important-only items.
---

# Morning Life Digest

Class-level workflow for the `life:daily-important-email-calendar-8am` cron
(`~/.hermes/cron/jobs.json`, id `85a468088e16`, schedule `0 9 * * *`,
`deliver: "origin"` → #life / `C0AMM2B4319`) and any future variant.

## When to use

- The `life:daily-important-email-calendar-8am` cron fires (this skill IS the
  canonical handler)
- A user asks for a "morning brief", "what's on my plate today", or
  "important email + calendar digest"
- Any `life:*`-style cron that fetches Gmail + Calendar and posts to Slack
  (not the fixed-reminder `life:*` crons like `cindil-protein-reminder` or
  `honda-civic-dmv-setup-hourly` — those are static text)

## Workflow

### 1. Pre-flight: confirm cron config + delivery channel

```bash
jq '.jobs[] | select(.name | contains("email-calendar"))' ~/.hermes/cron/jobs.json
```

Note: `deliver: "origin"` means the assistant's reply body IS the cron payload.
You must echo the digest in the reply AND post to Slack (see step 6).

### 2. Fetch Gmail unread (last 3 days)

```bash
gog gmail search 'is:unread newer_than:3d' --max 30 --json
```

⚠️ Flag is `--max`, NOT `--max-results`. Other useful: `--plain`, `--oldest`,
`--timezone`. Auth auto from macOS keyring.

### 3. Fetch next-24h calendar across ALL known accounts

**Use `gog`, not `gws`.** `gws calendar events list` defaults to a Workspace
service account (firebase-adminsdk) and has NO `--account` flag — calling it
silently returns empty results and looks like a bug. `gog` reads per-user
tokens from the macOS keyring.

```bash
NOW=$(date -u +%Y-%m-%dT%H:%M:%S%z)
TOMORROW=$(date -u -v+24H +%Y-%m-%dT%H:%M:%S%z)
for ACCT in $USER@gmail.com jleechan2015@gmail.com $USER@your-project.com; do
  gog calendar events --account "$ACCT" \
    --from "$NOW" --to "$TOMORROW" --max 50 --all --json
done
```

⚠️ No `--today` shortcut — build `--from` / `--to` in shell.
⚠️ **JSON shape**: `gog calendar events --all` returns `{"events":[...]}`,
NOT `{"items":[...]}`. Always parse defensively:
`data.get("items", data.get("events", []))`.
⚠️ One account may fail with `No auth for calendar <email>` — fall through
and report the missing auth in the digest's "Action needed" section.

A verified helper script is at `scripts/fetch_calendar_next24h.py` — it runs
the loop, handles JSON shape, and emits structured output ready for
post-processing.

### 4. Filter Gmail to top-3 important items

See `references/email-importance-filter.md` for the full exclusion list.
Mental model: exclude self-sent system mail, transactional digests, and
newsletters; rank remaining by action signal (billing alerts > deadlines >
security > government).

### 5. Compose digest (format is FIXED by cron prompt)

```
📬 *Life Digest — <Day YYYY-MM-DD>*

• *Important unread emails:*
  1. <emoji> *<Sender>* — <subject summary + action signal>.
  2. ...

• *Upcoming calendar events (next 24h):* <list OR "None across primary calendars.">

• *Action needed:*
  – <bullet per important item>
```

If calendar is empty, write "None across primary calendars" rather than
omitting the section — the cron prompt mandates the format.

### 6. Post to #life AND echo in reply (both required)

```bash
TOKEN=$(bash -c 'source ~/.bashrc 2>/dev/null; echo -n "$HERMES_SLACK_BOT_TOKEN"' 2>/dev/null | tr -d '"')
[ -z "$TOKEN" ] && TOKEN=$(security find-generic-password -s "HERMES_SLACK_BOT_TOKEN" -w)

curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary "$(python3 -c "import json; print(json.dumps({'channel':'C0AMM2B4319','text':open('/tmp/digest.txt').read()}))")"
```

Then ALSO put the same digest text in the assistant reply body — the cron
system captures it via `deliver: "origin"`.

## Pitfalls

- **Don't rank by recency alone.** "Daily GCP cost $87.47" is informational;
  "444% of budget expected to be reached" is actionable. Always rank by action
  signal first.
- **Self-sent mail dilutes the digest.** Gmail filters out mail sent from
  `$USER@gmail.com` (cron outputs, deploy bots, daily reports) — exclude
  with `-from:$USER@gmail.com` in the search query, OR filter in the
  selection step.
- **`Using keyring backend: keyring` line breaks `json.loads`** (gog and gws
  both emit it). Strip the leading noise before parsing, or write a small
  helper.
- **`gog calendar events --all` returns `{"events":[...]}` not `{"items":[...]}`**
  — always `data.get("items", data.get("events", []))`. A 2026-07-27 run
  saw zero events for 5 calls before the real shape surfaced.
- **`gws calendar events list` defaults to a Workspace service account
  (firebase-adminsdk)** and has no `--account` flag — use `gog` for
  personal calendar queries.
- **Multi-account loop is mandatory.** A single-account query misses events on
  the your-project.com / jleechan2015 calendars. If one account returns
  `No auth for calendar <email>`, surface it in "Action needed" instead of
  crashing.
- **`deliver: "origin"` ≠ no-Slack-post.** It means the reply body is captured
  AND the cron also expects Slack visibility — do both.
- **Don't fabricate numbers.** "~$3.8K+ if 100% is ~$860/day" — only write that
  if you have explicit basis from the email body or related report. Otherwise
  quote the email's stated percentage verbatim.

## References

- `references/gog-gws-tool-quirks.md` — flag gotchas for `gog` and `gws`,
  JSON shape, recurring-event instances, keyring noise line
- `references/email-importance-filter.md` — Gmail noise filter pattern with
  concrete exclusion list (Chase/Monarch/Capital One/etc.)
- `references/slack-life-channel.md` — #life channel ID `C0AMM2B4319`, token
  sourcing chain, full curl recipe

## Scripts

- `scripts/fetch_calendar_next24h.py` — verified multi-account calendar
  fetcher; handles JSON shape + per-account auth failures; emits structured
  JSON ready for the digest composer.

## Origin

Captured 2026-07-22 from cron `85a468088e16` (run #78). Tool quirks captured
from the live `gog v0.10.0` and `gws events list` invocations.
