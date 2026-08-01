# Stacked Unanswered Operator Asks — Triage Recipe

## Problem

The sweep finds 3+ $USER posts across 2+ monitored channels with no thread reply. Listing them as a flat dump:

```
- #life (11h old) — Find this email / Venmo / headless browser
- #worldai — Status on difficulty
- #worldai — Look at my most recent campaign
- #worldai — trim additions to 20 new lines then merge approved
- #worldai — Did we finally get UI evidence
- #all-$USER-ai — lets remove the archive from the PR
- #all-$USER-ai — Look at all the launchd and other recurring jobs
```

is technically accurate but operationally useless — the operator can't tell which one to act on first.

## Symptom

- `len(action_items) >= 3` AND
- `len({action_item.channel for action_item in action_items}) >= 2` AND
- All have `reply_count == 0` (or no bot reply in thread)

## Triage ranking

Score each $USER post on three axes, highest first:

| Axis | Weight | Rule |
|---|---|---|
| **Recency** | ×3 | `(now - post_ts)` in minutes; lower is better |
| **Channel priority** | ×1 | `#life`=3, `#all-$USER-ai`=2, `#jleechanclaw`=2, `#worldai`=1, `#agent-orchestrator`=1, `#ai-general`=0.5 |
| **Actionability** | ×2 | Concrete brief (e.g. "trim 20 lines then merge approved" / "audit the 12 launchd jobs and post in #ai-general") = 3; vague status check ("status on X") = 1; pure FYI ("FYI X is happening") = 0 |

```python
CHANNEL_WEIGHT = {
    'C0AMM2B4319': 3,    # #life (personal, high-signal)
    'C09GRLXF9GR': 2,    # #all-$USER-ai (operator direct)
    'C0AJ3SD5C79': 2,    # #jleechanclaw (harness)
    'C0AH3RY3DK6': 1,    # #worldai (product)
    'C0ALSKLU9KM': 1,    # #agent-orchestrator (ops)
    'C0AJQ5M0A0Y': 0.5,  # #ai-general (system reports)
}

ACTIONABILITY_PATTERNS = [
    (re.compile(r'\b(merge|ship|push|approve|build|fix|deploy|run)\b', re.I), 3),
    (re.compile(r'\b(audit|review|check|status|update)\b', re.I), 2),
    (re.compile(r'\b(why|how|what|when|where)\b', re.I), 1),
]

def score_post(post, now_ts):
    age_min = (now_ts - post['ts']) / 60
    recency = max(0, 100 - age_min)  # linear decay over 100 min
    channel = CHANNEL_WEIGHT.get(post['channel_id'], 0.5)
    actionability = max((s for r, s in ACTIONABILITY_PATTERNS if r.search(post['text'])), default=1)
    return (recency * 3) + (channel * 1) + (actionability * 2)
```

## Render recipe

```python
# Sort, take top 5, render as numbered list
ranked = sorted(action_items, key=score_post, reverse=True)[:5]
print('  :pushpin: *Slack — unanswered operator asks (last 18h)*')
for i, p in enumerate(ranked, 1):
    print(f'  {i}. *{p["channel"]}* ({p["age_human"]} old) — {p["text"][:200]!r}')
```

## Closing offer

Replace the generic "Anything you want me to act on?" with a **ranked action prompt** that mirrors the top 3 ranked items:

```
Want me to act on any of these? (a) <top-1 brief as concrete ask>, (b) <top-2 brief>, (c) <top-3 brief>, (d) all of the above via AO dispatch.
```

## Verified example: 2026-07-14 08:02 PT sweep

Input: 7 $USER posts (1 #life + 4 #worldai + 2 #all-$USER-ai).

After triage + ranking:
```
:pushpin: *Slack — unanswered operator asks (last 18h)*
- #life (11h old) — "Find this email and try to do this you did similar things before..." [no thread reply yet]
- #worldai — "Status on difficulty"
- #worldai — "Look at my most recent campaign under $USER@gmail.com — not sure if dialog working?"
- #worldai — "trim additions to ~20 new lines in dialog system instruction then merge approved and test using agy cli provider but fullrun until you merge"
- #worldai — "Did we finally get UI evidence for this retelimti stuff?"
- #all-$USER-ai — "lets remove the archive from the PR and modify /exportcommands to stop exporting it" (15h old, no reply)
- #all-$USER-ai — "Look at all the launchd and other recurring jobs..." (17h old)
```

Closing offer:
```
Want me to act on any of these? (a) kick off the Venmo/email headless-browser task, (b) triage the 4 #worldai asks into an AO dispatch, (c) investigate the Level Up Test FAILED scenarios, (d) check on the launchd/recurring-jobs Slack-routing sweep.
```

## Reference

- SKILL.md P45 — the stacked-asks triage pitfall (the brief that motivated this)
- `references/ea-dedup-protocol.md` — 30-min sliding-window dedup discipline (orthogonal to triage ranking, but the brief format they share)
