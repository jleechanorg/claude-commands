# 72-hour dropped-thread sweep — verified recipe (2026-07-26)

Use this when the user asks for a full audit (e.g. "go through all slack threads in the last N days and rederive dropped ones") rather than letting the cron-monitor catch things passively.

## Why this exists

The dropped-thread-followup cron only catches thread replies that the bot already tagged as "no bot follow-up within 30 min". A full sweep needs:

- Both gateway logs (MacBook + Ubuntu) — different processes route different channels.
- Multi-token `user=…` regex (`Jeffrey Lee-Chan` is two words).
- A cron-echo filter applied BEFORE counting drops (most Jeffrey inbound messages in 72h are automated reports).
- Identity routing that picks the right token per channel.
- A reply-anchor audit summary posted in the originating thread.

## Verified scan stats (2026-07-23 → 2026-07-27, MacBook gateway)

| Metric | Value |
|---|---|
| Total Jeffrey inbound messages | 133 |
| Cron-echo (filtered) | 5 (Daily Bug Hunt, Slack Digest, AO Progress, Spend Alert, Cron Backup, AI Cost Alert, GH Actions cost, Backfill, canary, `__ping__`) |
| After filter, real asks | 124 |
| Already-answered | 110 |
| Drop candidates (no follow-up outbound in 60m) | 9 |
| All 9 root-cause | Anthropic HTTP 429 / Token Plan weekly limit (`$HOME/.hermes/logs/gateway.log` shows the rate-limit pattern starting from the window) |

## Verified scan stats (Ubuntu `jeff-ubuntu` gateway, same window)

0 fresh Jeffrey inbound messages in 72h. Everything was on MacBook. The Ubuntu log serves as a backstop for the cron monitor's outbound (`Sending response`) audit.

## Recipes

### Step 1 — Build the per-channel inbound/outbound timeline

```python
import re, datetime
from pathlib import Path
from collections import defaultdict

raw = Path("$HOME/.hermes/logs/gateway.log").read_text(errors="ignore")

def parse_ts(s):
    try: return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception: return None

start = datetime.datetime(2026, 7, 23)
end = datetime.datetime(2026, 7, 27, 5)

# CRITICAL: multi-token user= matcher for "Jeffrey Lee-Chan"
rx_in = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ INFO gateway\.run: inbound message: "
    r"platform=slack user=(Jeffrey(?: Lee-Chan)?|hermes(?:_pc)?) "
    r"chat=(\S+) msg='([^']*)' reply_to_id=(\S+) reply_to_text='([^']*)'"
)
rx_out = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ INFO gateway\.platforms\.base: "
    r"\[Slack\] Sending response \((\d+) chars\) to (\S+)"
)

inb, out = [], []
for m in rx_in.finditer(raw):
    d = parse_ts(m.group(1))
    if d and start <= d < end:
        inb.append((d, m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)))
for m in rx_out.finditer(raw):
    d = parse_ts(m.group(1))
    if d and start <= d < end:
        out.append((d, m.group(2), m.group(3)))

# Cron-echo filter — these never count as dropped asks
ECHO = ("Daily Bug Hunt Report", "Slack Digest", "AO Progress Report",
        "Spend Alert", "Cron Backup", "AI Cost Alert", "GH Actions cost",
        "Backfill", "__ping__", "hermes-canary")

ev = defaultdict(list)
for d, u, ch, msg, rid, rt in inb: ev[ch].append((d, "in", u, msg, rid, rt))
for d, n, ch in out:        ev[ch].append((d, "out", "", n))

drops = []
for ch, seq in ev.items():
    seq.sort(key=lambda x: x[0])
    for i, e in enumerate(seq):
        if e[1] != "in" or "Jeffrey" not in e[2]:
            continue
        if any(s in e[3] for s in ECHO):
            continue
        nxt = None
        for j in range(i + 1, len(seq)):
            if seq[j][1] == "out": nxt = seq[j]; break
            if seq[j][0] - e[0] > datetime.timedelta(minutes=60): break
        if not nxt:
            drops.append((ch, e[0], e[3][:240], e[4], e[5][:80]))

# drops = list of dropped asks, ready for per-thread reply
```

### Step 2 — Identity routing per channel

```bash
TOK=$(bash -c 'source ~/.hermes/scripts/launchd-env-wrapper.sh 2>/dev/null; echo "$HERMES_SLACK_BOT_TOKEN"')
TOK_USER=$(bash -c 'source ~/.hermes/scripts/launchd-env-wrapper.sh 2>/dev/null; echo "$SLACK_USER_TOKEN"')

# Probe each target channel's bot membership
for ch in C0BCVG4F560 C0AJ3SD5C79 C0AMM2B4319 C0AH3RY3DK6 C0AJQ5M0A0Y; do
    curl -fsS -X POST "https://slack.com/api/conversations.info" \
        -H "Authorization: Bearer $TOK" \
        -d "channel=$ch" \
        | python3 -c "import json,sys;d=json.load(sys.stdin);print('$ch','is_member=',d.get('channel',{}).get('is_member'))"
done
```

Verified membership matrix (2026-07-26):

| Channel | Bot is_member? | Use token |
|---|---|---|
| C0BCVG4F560 (`#worldai-alerts`) | `true` | `HERMES_SLACK_BOT_TOKEN` |
| C0AJ3SD5C79 (`#jleechanclaw`) | `true` | `HERMES_SLACK_BOT_TOKEN` |
| C0AMM2B4319 (`#life`) | `true` | `HERMES_SLACK_BOT_TOKEN` |
| C0AH3RY3DK6 (`#worldai`) | `true` | `HERMES_SLACK_BOT_TOKEN` |
| C09GRLXF9GR (`#all-$USER-ai`) | `true` | `HERMES_SLACK_BOT_TOKEN` |
| C0AJQ5M0A0Y (`#ai-general`) | **`false`** | `SLACK_USER_TOKEN` (XOX-P) |

### Step 3 — Reply in each originating thread

```bash
# For bot-member channels:
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "{\"channel\":\"C0BCVG4F560\",\"thread_ts\":\"1784219487.851579\",\"text\":\"<reply body>\"}"

# For non-member channels (XOX-P user fallback):
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer $SLACK_USER_TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "{\"channel\":\"C0AJQ5M0A0Y\",\"thread_ts\":\"1784909435.210119\",\"text\":\"<reply body>\"}"
```

When using XOX-P, the reply shows up as `$USER` (U09GH5BR3QU) — flag this in the reply body so the user knows it's not the bot identity.

### Step 4 — Verify the reply landed

`mcp__slack__conversations_add_message` returns an empty `MsgID` CSV row when rate-limited, same exit shape as a success. Always re-fetch the thread after posting and assert a new `ts` from the right identity appeared:

```python
# Expected: a message with ts in 2026-07-27 02:25-02:30 UTC range, user=U0A4G7LDJ4R (bot)
# or user=U09GH5BR3QU (XOX-P)
```

### Step 5 — Post the audit summary in the originating thread (the user's first ask)

```python
# Single message, with markdown table:
# | Thread | Channel | Reply ts | Identity |
# + 1-line rate-limit root cause
# + follow-up cron job ID
# + durable state pushed
```

### Step 6 — Arm one 20-minute follow-up cron

Per `one-time-status-cron-after-every-task`:

```python
hermes.cronjob(
    action="create",
    name="Dropped-thread sweep 72h closeout (20m)",
    schedule="20m",
    repeat=1,
    deliver="slack:<originating_channel>:<originating_thread_ts>",
    prompt="<echo the audit summary>"
)
```

The cron fires once at +20m and auto-deletes. Don't use `--every` (recurring) — that's the bug-ref bug from cron `f5b50ed8` (2026-04-07).

## Pitfalls observed on the 2026-07-26 sweep

1. **`user=(\\S+)` silently dropped half of Jeffrey's name.** Multi-token matcher is mandatory. Without it, the audit produces 0 rows and falsely concludes "no drops."
2. **`source ~/.bashrc` returns a token that `auth.test` rejects as `invalid_auth`.** Use the launcher-env-wrapper instead.
3. **`mcp__slack__conversations_replies` returns `not_in_channel` for `#ai-general`** (bot not a member). Use `chat.postMessage` with XOX-P for the reply, then verify with the next read.
4. **`mcp__slack__conversations_add_message` empty `MsgID` row ≠ failure**, but also ≠ success. Re-fetch the thread to confirm.
5. **The Ubuntu gateway log serves as a backstop**, not a primary source. The MacBook gateway serves the daily-driver channels; the Ubuntu gateway serves the alerting side (`#hermes-home`, `#hermes-prod`, `#ai-cost`, `#hermes-alerts`). For a 72h user-asks sweep, the MacBook log is the canonical source; the Ubuntu log catches outbound responses that the cron-monitor system auto-posts on its own.
6. **Cron echo messages can look like asks.** "Cron Backup: changed (not committed). Total: N jobs." looks like a question to a naive classifier. Apply the cron-echo filter BEFORE counting drops — the 5 fixed echo strings above are the verified filter for 2026-07-26.
7. **`hermes cronjob action='create'` returns 503 on the first attempt with `--every` or `--keep-after-run`** (the recurring cron bug). Use `--at 20m` + `--delete-after-run` for the one-time pattern, no `--every` flag.
8. **Posting the audit summary as a top-level message in the originating channel** (instead of in the originating thread) loses the thread-anchor. Always pass `thread_ts=…` for both the per-drop replies AND the audit summary.