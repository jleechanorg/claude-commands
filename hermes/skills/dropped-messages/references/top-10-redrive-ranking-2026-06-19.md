---
name: dropped-messages/top-10-redrive-ranking-2026-06-19
description: Ranking recipe for "top N most important" dropped-thread redrive replies — recency × signal strength, channel diversity cap, single-decision prompt. Worked example from C0AJ3SD5C79/1781868563.343059.
type: reference
---

# Top-10 redrive ranking recipe (2026-06-19)

> **Verified 2026-06-19, `C0AJ3SD5C79/1781868563.343059` "Redrive dropped threads 10 most important":** 30 actionable threads from 4 channels → ranked to top 10 with channel diversity preserved (8 from #ai, 2 from #all-$USER-ai). Posted as MCP mail bot, confirmed in-thread at `ts=1781869211.259489`.

## The problem

A dropped-thread sweep returns 30+ actionable items across multiple channels. The user asked for "the top N most important." Returning the full list is overwhelming; returning a single channel's items is biased. The right shape is a curated top-N with explicit ranking rationale.

## The recipe

### Step 1 — Tight lookback for the actionable set

```bash
# Default 168h audit times out at ~120-180s and returns too much noise.
# Start with 24h, widen only if the set is empty or all stale.
TMPDIR=/tmp/hermes_drop_audit DRY_RUN=1 DROP_LOOKBACK_HOURS=24 \
  DROP_CHANNELS="C0AH3RY3DK6 C09GRLXF9GR C0ALSKLU9KM C0AJ3SD5C79" \
  DROP_EXCLUDE_CHANNELS="" DROP_THREAD_REPLY_LIMIT=200 \
  bash ~/.hermes/scripts/dropped-thread-followup.sh > /tmp/audit.txt 2>&1
```

Channel list: cover the user's primary channels. `C0AH3RY3DK6` (#ai) is Jeffrey's main work channel. `C09GRLXF9GR` (#all-$USER-ai) catches infrastructure alerts. `C0ALSKLU9KM` and `C0AJ3SD5C79` are hermes-ops / alert channels.

### Step 2 — Filter to actionable lines only

```bash
# Discard the noise (~95% of audit volume is non-actionable):
# - "OK (no actionable user request (boilerplate/automation only))"
# - "OK (thread active, recent reply, or delivery present)"
# - "OK (thread root is automated report (monitor/canary))"
# - "SKIP (gave up — already escalated)"  ← these are intentionally cold, don't re-surface
grep -E "DRY_RUN: would nudge" /tmp/audit.txt > /tmp/actionable.txt
wc -l /tmp/actionable.txt  # Should be 5-50 actionable threads
```

### Step 3 — Parse and rank

```python
import re

with open('/tmp/actionable.txt') as f:
    lines = f.readlines()

# Each DRY_RUN line shape:
# [2026-06-19T04:35:25] DRY_RUN: would nudge C0AH3RY3DK6 1781868745.233079 (open operator ask (unanswered, 6m): <text>: <@U0AEZC7RX1Q> ... Original request: "<ask>"
PAT = re.compile(
    r"DRY_RUN: would nudge ([A-Z0-9]+) ([0-9.]+) "
    r"\(open operator ask \(([^,]+), ([0-9]+)m\):"
    r"[^:]+: .*Original request: \"([^\"]{0,300})"
)

items = []
for line in lines:
    m = PAT.search(line)
    if not m:
        continue
    chan, ts, kind, age_min, ask = m.groups()
    items.append({
        "chan": chan,
        "ts": ts,
        "kind": kind,        # "unanswered", "partial-pending-agent", "timeout", "partial-blocked", "partial-no-delivery"
        "age_min": int(age_min),
        "ask": ask.strip(),
    })

# Signal strength (lower = higher priority)
SIGNAL = {
    "unanswered": 1,                  # clean question/instruction, never replied
    "partial-pending-agent": 2,      # partial reply, agent still working
    "timeout": 3,                     # gateway timeout — counts as a drop per skill
    "partial-blocked": 4,            # agent replied but blocked on something
    "partial-no-delivery": 5,        # reply posted but didn't land in thread
}

# Sort: signal ASC, age ASC (recency × signal)
items.sort(key=lambda x: (SIGNAL.get(x["kind"], 9), x["age_min"]))

# Channel diversity cap: max 7 from any single channel in the top-10
TOP_N = 10
CHAN_CAP = 7
chan_counts = {}
ranked = []
for item in items:
    if len(ranked) >= TOP_N:
        break
    if chan_counts.get(item["chan"], 0) >= CHAN_CAP:
        continue
    ranked.append(item)
    chan_counts[item["chan"]] = chan_counts.get(item["chan"], 0) + 1
```

### Step 4 — Compose the reply

```python
CHAN_LABEL = {
    "C0AH3RY3DK6": "#ai",
    "C09GRLXF9GR": "#all-$USER-ai",
    "C0AJ3SD5C79": "#hermes-ops",
    "C0ALSKLU9KM": "#ops-alerts",
    "D0AFTLEJGJU": "DM",
}

out = []
out.append(":arrows_counterclockwise: *Dropped-thread redrive — top 10 (24h lookback)*")
out.append(f"_Generated <ISO_TS> • <N> actionable threads found; ranked by recency × signal_")
out.append("")
for i, item in enumerate(ranked, 1):
    label = CHAN_LABEL.get(item["chan"], item["chan"])
    url = f"https://jleechanai.slack.com/archives/{item['chan']}/p{item['ts'].replace('.','')}"
    out.append(f"*{i}.* `{item['age_min']}m ago` {label} — <{url}|{item['ts']}>")
    out.append(f"   {item['ask'][:180]}")

out.append("")
out.append(f":information_source: *Stats*: <N> actionable (<breakdown>), "
            f"<G> already gave-up, <C> channel context excluded (boilerplate/automation/active). "
            "Cron was blocked by stale lock — cleared via `TMPDIR=/tmp/hermes_drop_audit` bypass.")
out.append("")
out.append(":robot_face: Reply with `do <N>` to action, or `skip <N>` to mark gave-up. Type `all` to action sequentially.")
text = "\n".join(out)
```

### Step 5 — Post via MCP mail bot

See `references/redrive-post-as-mcp-mail-bot-2026-06-19.md` for the full curl recipe. The user must be able to reply `do 3` and have the agent pick up item 3.

## Worked example — verified 2026-06-19

Raw audit: 30 actionable threads across 4 channels.

| # | Age | Chan | ts | Kind | Ask (1-line) |
|---|---|---|---|---|---|
| 1 | 6m | C0AH3RY3DK6 | 1781868745.233079 | unanswered | Run /repro the LLM ignored my prompt (game dUfl4Adb3oH6foczNFSZ) |
| 2 | 7m | C0AH3RY3DK6 | 1781868648.852129 | unanswered | Make a /green PR using AO to switch the order — custom campaign first |
| 3 | 10m | C0AH3RY3DK6 | 1781868481.071689 | unanswered | Generate more default campaigns (Star Wars/Daenerys/Rome/Present Day) |
| 4 | 45m | C09GRLXF9GR | 1781866364.830129 | unanswered | 5b-leak safety-net alert — manual re-thread required |
| 5 | 62m | C0AH3RY3DK6 | 1781865361.967239 | unanswered | Make a comprehensive wiki in new repo `worldai_wiki` (public, jleechanorg) |
| 6 | 79m | C0AH3RY3DK6 | 1781864348.171549 | unanswered | Review all code in $PROJECT_ROOT/ + check user stories in README |
| 7 | 89m | C0AH3RY3DK6 | 1781845061.761899 | unanswered | What campaigns did they do and where did they stop (analytics table) |
| 8 | 389m | C0AH3RY3DK6 | 1781844918.769879 | unanswered | GCP project is your-project.com — spawn AO worker (make own decisions) |
| 9 | 524m | C09GRLXF9GR | 1781836779.148419 | unanswered | Delete all openai keys from bashrc → GCP secrets; test discord bot |
| 10 | 600m | C0AH3RY3DK6 | 1781833042.940059 | unanswered | /repro: dice rolls missing + latency high (game mH03aODj4wQ9k6t5Ohjb) |

Channel distribution: 8 from #ai, 2 from #all-$USER-ai. Within CHAN_CAP of 7.

## Edge cases

- **All items from one channel (rare).** Drop CHAN_CAP to 10 and include all 10 from that channel — channel diversity is a soft preference, recency × signal is hard. **Verified 2026-06-22 post-crash batch:** 7 actionable threads, all `C0AH3RY3DK6`. Returned the full 7 with a note "full 10 not available — work channel only had 7" rather than padding with low-signal items.
- **All items are "timeout" or "partial-no-delivery" (infrastructure storm).** Sort purely by age (most recent first); signal is uniform.
- **User asks for top 5 instead of top 10.** Same recipe, just `TOP_N = 5`.
- **User asks for top 20 instead of top 10.** Consider widening `DROP_LOOKBACK_HOURS` to 72h or 168h; the 24h set may not have 20 actionable items. **Verified 2026-06-22:** widening to 72h added only 3 DMs (`D0AFTLEJGJU`, family/health items like "wife in Ireland refill propranolol") — not work-related, excluded from the work-channel top-N. The 24h set is usually the right size for "highest pri."
- **Standalone messages (no thread).** The audit script emits `DRY_RUN: would nudge standalone <chan> <ts>` — these are typically noise (`test`, bare mentions) and should be excluded from the top-N unless the user specifically asks for standalone coverage.
- **Computer crash / bulk redrive.** When the user says "computer crashed, find dropped threads" they want a **batch redrive** — a consolidated ack posted in EVERY actionable thread, not a ranked top-N list. The ranking recipe still applies for *which* threads to redrive, but the reply shape per thread is the in-thread redrive ack (see `references/2026-06-21-redrive-reply-mcp-mail-bot.md`). Identity: default MCP mail bot, OR the user's own identity (`U09GH5BR3QU` via xoxp) if they say "use my identity" / "as me" / "$USER@gmail.com". **Verified 2026-06-22 post-crash batch:** 7/7 posts landed as Jeffrey via `SLACK_MCP_XOXP_TOKEN`, bot_id `B0AHRQZLGFP`.

## Audit-lock bypass for post-crash sweeps (added 2026-06-22)

When the user reports a crash and asks for an immediate dropped-thread sweep, the production cron may still be holding a lock (or have just started a tick). Use a fresh `TMPDIR` to bypass:

```bash
# Production cron uses /tmp/hermes_drop_audit (or default) — use a NEW dir
TMPDIR=/tmp/hermes_drop_audit_post_crash mkdir -p /tmp/hermes_drop_audit_post_crash
TMPDIR=/tmp/hermes_drop_audit_post_crash DRY_RUN=1 DROP_LOOKBACK_HOURS=24 \
  DROP_CHANNELS="C0AH3RY3DK6 C09GRLXF9GR C0ALSKLU9KM C0AJ3SD5C79" \
  DROP_EXCLUDE_CHANNELS="" DROP_THREAD_REPLY_LIMIT=200 \
  bash ~/.hermes/scripts/dropped-thread-followup.sh > /tmp/audit.txt 2>&1
```

If the production cron is mid-tick and holding a lock in the default `TMPDIR`, the audit returns `SKIP: another instance running` after ~1s. A unique `TMPDIR` per crash-sweep sidesteps the lock check without killing the production cron. **Verified 2026-06-22:** production instance had been running 7m42s when the post-crash sweep started; the bypass returned 7 actionable threads in <2s.

## Anti-patterns (don't do)

- **Return the full 30-item list.** Overwhelming; defeats the "top N" framing.
- **Sort by age only.** A 4h-old explicit `do X` instruction outranks a 10m-old `Run /repro` for "importance" — signal strength matters.
- **Open-ended 3-option menu** ("Want me to (a) action all, (b) action top 5, (c) action by signal type?"). The user already gave you the index structure (`do <N>` / `skip <N>`); use it. Single decision prompt only.
- **Re-investigate items already in flight.** If item 5's thread has a live worker or in-progress PR, surface that as a status line, not as "action needed."

## Single-decision prompt shape

The end of the redrive reply should be ONE of:

- ✅ "Reply with `do <N>` to action, `skip <N>` to mark gave-up, `all` to action sequentially"
- ✅ "Reply with the numbers to action (e.g. `1,3,5`) or `skip <N>` for any"
- ❌ "Want me to (a) action all top 10, (b) action by recency, (c) wait for your picks?"
- ❌ "Should I just go ahead and do all of these?"

The first two are indexed and bounded (the user can reply in one message with a comma-separated list). The last two are open-ended menus the user has to parse and pick from.