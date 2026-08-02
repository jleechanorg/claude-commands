# Asymmetric Bot Channel Access — Fallback Recipe (verified 2026-07-15 16:04 PT)

## Symptom

After a Slack bot rotation, the bot may be a member of SOME channels but not others.
Unlike a fully locked-out bot (which fails everywhere), the asymmetric case is sneaky:
- `conversations.history` works for `#all-$USER-ai` (bot in channel) → 40 messages
- `conversations.history` returns `not_in_channel` for `#worldai`, `#ai-general`, `#worldai-alerts`

A naive sweep that just checks `r.get('ok')` and falls back to xoxp on failure
will work, but the next step (`conversations.replies` to check thread state) will
**also fail on xoxp** for the same channels where the bot is locked out.

## Verified failure mode (2026-07-15 16:04 PT)

```
[worldai-alerts "make followup" ts=1784151461] xoxp: replies=0  (returned only the parent)
```

The xoxp user token has visibility into `conversations.history` for channels the
USER is in, but `conversations.replies` does NOT return thread children for
channels the BOT can't see (verified 2026-07-15 16:04 PT on #worldai-alerts).
Symptom signature: `{"ok":true, "messages": [<parent only>]}` — the thread is
truncated to just the parent, no replies array entries.

## Recipe: cheap thread-reply-state via parent `reply_count`

Skip `conversations.replies` entirely. The parent message returned by
`conversations.history` already carries a `reply_count` field. Use it:

```python
import json, urllib.request, re, subprocess

xoxp = subprocess.run(['bash','-lc','source ~/.bashrc && echo "$SLACK_MCP_XOXP_TOKEN"'],
                     capture_output=True, text=True).stdout.strip()

def call(url, tok):
    headers = {'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json'}
    req = urllib.request.Request(url, headers=headers)
    raw = urllib.request.urlopen(req, timeout=30).read()
    clean = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', raw)
    return json.loads(clean.decode('utf-8','replace'))

# Fetch history (works on xoxp even when bot is locked out)
r = call('https://slack.com/api/conversations.history?channel=C0BCVG4F560&limit=100', xoxp)
msgs = r['messages']

# Find the target post by ts and read its reply_count
target_ts = '1784151461.936279'
parent = next((m for m in msgs if m.get('ts') == target_ts), None)
if parent:
    n_replies = parent.get('reply_count', 0)
    latest = parent.get('latest_reply', '')
    # n_replies == 0 → unanswered
    # n_replies > 0 → check latest for recency
```

This works regardless of bot vs xoxp access because `reply_count` is on the
parent message itself.

## Fallback chain (rank by cost)

1. **Bot token `conversations.history`** — cheapest; use first. If `ok=True`, you
   have channel access and `conversations.replies` will likely also work.
2. **XOXP `conversations.history`** — works across all channels the user is in.
   Pull `reply_count` from parent messages directly; do NOT try
   `conversations.replies` for channels where bot is locked out.
3. **For deeper thread inspection (who replied, what was said):** needs the bot
   to be in the channel. If only `#all-$USER-ai` is bot-accessible, do the
   full ranking on the cheap probe, then only fetch full thread contents for
   the top-N asks in channels where bot has access.

## Why this matters

In the 2026-07-15 16:04 PT sweep, the prior brief (12:04 PT) had cited 4
unanswered asks in `#worldai` and `#ai-general` with ts values like
`1784141476`, `1784080634`, `1784016996`, `1784062081`, `1783981197`. None of
those ts values appeared in the latest 100-message `conversations.history`
window — they had scrolled out of the cheap-probe range. The cheap
`reply_count` probe via `oldest=<ts>` parameter is the only way to verify
prior-brief citations without scrolling deeper.

`conversations.history` accepts `oldest=<ts>` to set the lower bound of the
returned window. Use it for any ts that's not in the latest 100 messages.

## Fix the underlying problem

`/invite @mcp_agent_mail` to each channel where bot is locked out. Until then,
the asymmetric fallback chain above is the operational workaround.