# Daily Digest Cron Recipe (Gmail + Calendar → Slack)

Verified 2026-07-12 against `gog v0.10.0` on macOS. Used by a scheduled cron job that posts a concise morning digest to a designated Slack channel.

## What it produces

A short Slack message containing:
- Top N important unread emails (priority + from + subject + one-line context)
- Calendar events in the next 24h (with Meet links if any)
- Action-needed call-out (billing alerts, reply-required threads, etc.)
- "No important items" fallback when the lists are empty

## Working account

Use the personal Gmail OAuth account, not the service account:

```bash
GOG="gog -a $USER@gmail.com"
```

`gog auth list` shows which accounts are configured and the auth type per account. Confirm with `gog auth list` before running — service-account calendars return `items: []` even when fully authorized.

## Gmail search (important unread)

```bash
gog gmail search "is:unread is:important" --max 5 --json --results-only -a $USER@gmail.com
```

Returns:
```json
[
  {
    "date": "2026-07-11 19:00",
    "from": "Gary <garylue@gmail.com>",
    "id": "19f540e29f164dc1",
    "subject": "Accepted: gary / jeff chat @ Sun Jul 12, 2026 2pm - 2:30pm (PDT)",
    "labels": ["UNREAD", "IMPORTANT", "INBOX"],
    "messageCount": 1
  }
]
```

`--json --results-only` is the right flag pair: `--results-only` drops the envelope (`nextPageToken`, etc.) so `python3 -c 'import json,sys; json.load(sys.stdin)'` parses cleanly.

`is:important` is Gmail's own importance classifier — surfaces account-level signal without per-mailbox tuning. For raw counts use `is:unread` alone.

## Calendar next 24h

Do **not** use `--days N` — that returns `404 notFound` on `gog ≤ 0.10.0`. Use `--from` / `--to` with RFC3339 UTC timestamps:

```bash
FROM_TS=$(date -u -v+0H "+%Y-%m-%dT%H:%M:%SZ")
TO_TS=$(date -u -v+24H "+%Y-%m-%dT%H:%M:%SZ")
gog calendar list --from "$FROM_TS" --to "$TO_TS" --json --results-only -a $USER@gmail.com
```

`date -v+24H` is BSD/macOS syntax (GNU `date` uses `-d '+24 hours'`). On Linux, swap to `date -u -d '+24 hours' "+%Y-%m-%dT%H:%M:%SZ"`.

Returned events include `summary`, `start.dateTime` (with timezone), `end.dateTime`, `attendees[]`, `hangoutLink`, and `htmlLink` — enough to render a digest without a second API call.

## Posting to Slack

```python
# In a Hermes session:
mcp__slack__conversations_add_message(
    channel_id="C0AMM2B4319",  # #life (or whichever channel the cron is bound to)
    content_type="text/markdown",
    text=digest_body,
)
```

Verify the post by checking the returned `MsgID` row has `BotName=hermes` and the expected channel. See `slack-reply-inherit-thread-ts` in SOUL.md for thread-routing pitfalls.

## Filtering "important" out of the digest

Three signals worth elevating above the standard `is:important` flag:

1. **Billing alerts** — match `from:cloudplatform-noreply@google.com` or `from:noreply@stripe.com` in the subject. Always call out, regardless of importance flag.
2. **CPA / legal / tax** — match `subject:tax return`, CPA firm domains, etc. These need a reply within days, not weeks.
3. **Calendar-meeting acceptance emails** — usually low-signal noise; drop them from the digest body but keep the corresponding calendar event.

## Pitfalls

- **`gog calendar list --days N` is broken on gog ≤ 0.10.0.** Always pass `--from`/`--to` instead.
- **`-a <email>` is required** even when only one OAuth account is configured; `gog` otherwise uses the default and may pick the service account.
- **`--max 5` on `gmail search` is the max page size**, not the global cap. For more, use `--all` (slower, paginates through) or pass a tighter query.
- **Timezone drift**: `date -u` always returns UTC. Calendar events return local `dateTime` with offset. When the user is in PDT and the cron runs at 09:01 PDT, the "next 24h" window is `16:01Z` to `+24h`. No drift, but worth double-checking on DST boundaries.
- **Empty digest**: if both Gmail and Calendar return `[]`, post literally `No important emails/events right now.` per the cron contract — do not post a verbose "everything is fine" report.

## Related

- `references/gmail-search-syntax.md` (in the bundled `google-workspace` skill) — full Gmail query operator reference.
- `slack-channel-routing-policy` in `~/.hermes/workspace/SOUL.md` — which channel to post a cron-driven digest to (default `#ai-general`, not `#all-$USER-ai` unless user-specified).