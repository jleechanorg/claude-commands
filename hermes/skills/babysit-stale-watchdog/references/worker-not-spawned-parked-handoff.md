# Worker Never Spawned — Parked-Handoff End-State

## The pattern

A babysit cron task says: "check the AO worker spawned for `<repo>` on `<date>` to fix `<failure-class>`. Originating thread: `<channel>/<ts>`." You come in expecting a live session + a PR. Both are missing. The previous session disabled itself, the worker never came up, the user never replied. You're the +20m tick.

This is the third end-state for a babysit cron. The other two are:
1. PR is MERGED or CLOSED → terminal-state check wins → cancel.
2. PR is alive but user posted a human-approval gate → auto-merge superseded → cancel.

The third:
3. **Worker never spawned, PR never created, operator never replied** → state is `worker_not_spawned_parked_handoff`. The cron fires but there is nothing to watch. The originating session's A/B/C hand-off question is the canonical "ask" — if it had been answered, the babysit would have been armed against a real worker. Silence = the operator chose neither A nor B nor C = the work is parked.

## Three-way check (run all three before posting)

```bash
# 1. Was the worker ever created?
ao session ls --json 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
matches = [s for s in data.get('data', [])
           if s['projectId'] == '<PROJECT_ID>'
           and s['createdAt'] >= '<YYYY-MM-DD>T00:00:00Z'
           and s['createdAt'] <  '<YYYY-MM-DD+1>T00:00:00Z']
print(f'sessions: {len(matches)}')
for m in matches:
    print(f'  {m[\"id\"]}  status={m[\"status\"]}  lastActivity={m[\"lastActivityAt\"]}')
"
# Expected: empty if the worker never spawned.

# 2. Did the PR ever open?
gh pr list --repo <OWNER>/<REPO> --json url,state,headRefName,additions,changedFiles,createdAt | python3 -c "
import json, sys
prs = json.load(sys.stdin)
matching = [p for p in prs if p['headRefName'] == '<expected-branch>']
print(f'prs: {len(matching)}')
for p in matching:
    print(f'  {p[\"url\"]}  state={p[\"state\"]}')
"
# Expected: empty if no PR.

# 3. Did the operator ever reply to the A/B/C hand-off?
curl -fsS -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  "https://slack.com/api/conversations.replies?channel=<CHAN>&ts=<THREAD_TS>&limit=50" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
msgs = data.get('messages', [])
operator_msgs = [m for m in msgs if m.get('user') == 'U09GH5BR3QU']
print(f'operator replies: {len(operator_msgs)}')
"
# Expected: 0 if the operator never picked up the hand-off.
```

If checks 1 and 2 both empty AND check 3 zero → state is `worker_not_spawned_parked_handoff`.

## Cancel recipe

```bash
# 1. Post the 1-line status to the originating thread (NOT top-level, NOT in a different channel).
#    Use the same thread_ts the cron was armed against.
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{\"channel\":\"<CHAN>\",\"thread_ts\":\"<THREAD_TS>\",\"text\":\"Worker still iterating; no PR yet. (Cron <CRON_ID> — no <expected-session-name> AO session exists; <one-line root-cause>; user A/B/C decision never received. Self-cancelling this cron.)\"}"

# 2. Self-cancel the cron.
hermes cron rm <CRON_ID>

# 3. Verify removal.
hermes cron list | grep <CRON_ID>   # MUST return empty
```

## What NOT to do

- **Do NOT** call `ao spawn` to retry the spawn. The previous session already tried multiple times; the AO daemon pool bug that ate those attempts is daemon-side state, not something retrying solves at the cron layer. If the pool has recovered, the operator will re-spawn manually with a fresh prompt.
- **Do NOT** post a long investigation report. The cron firing IS the investigation. The 1-line status is the deliverable.
- **Do NOT** create a new cron. The hand-off is parked; new work = new operator action, not a new babysit.
- **Do NOT** post to `#ai-general` (home channel). Per SOUL.md `## COMMIT: slack-channel-routing-policy`, this is a direct reply to a user-originated thread → use the originating channel + thread_ts.
- **Do NOT** fabricate a "worker is making progress" message. The worker doesn't exist. The report is "no PR yet" verbatim.

## Worked example (verified 2026-07-22)

Cron: `5a771c731157` "fix-daily-0722 status" (Schedule: once in 20m, Repeat 1/1)
Thread: `C0AH3RY3DK6/p1784721612.183329`
Brief: `/tmp/wa-failures/2026-07-22/ao-worker-brief.md` (still on disk)
Beads: `rev-0f388` (P0), `rev-l04n0` (P1), `rev-iibtl` (P2)

- `ao session ls --json` → 53 total sessions, 0 matching `fix-daily-0722`. 12 ghost-idle sessions had been created in the last 6h (daemon pool was leaking workers) but none were the requested one — the operator's specific name never landed.
- `gh pr list --head fix-daily-0722` → 0 PRs.
- `conversations.replies` → 0 messages from `U09GH5BR3QU` since the original alert at ts `1784721612.183329`. The previous session's A/B/C question at ts `1784762069.577749` was 26h old with zero replies.
- Posted ts `1784763797.688999` to thread (verbatim message above).
- `hermes cron rm 5a771c731157` → "Removed job: fix-daily-0722 status (5a771c731157)".
- `hermes cron list | grep 5a771c731157` → empty.

## Why this is a third end-state, not a bug

The babysit cron is doing exactly what it was armed to do: poll periodically. The fact that the polling target never materialized is a hand-off problem, not a cron problem. The cron has three legitimate end-states:

1. **Worker merged PR** → success, post terminal, cancel.
2. **Worker closed PR** → failure, post terminal, cancel.
3. **Worker never existed** → parked, post parked-handoff, cancel.

The watchdog's job is to recognize all three. The original `is_pr_terminal()` check only handles 1 and 2. The parked-handoff check (this file) handles 3. Both end in `hermes cron rm <id>` plus one in-thread status post — the structure is parallel but the message text differs.
