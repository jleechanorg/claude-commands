# 2026-06-13 — "Another example" — 12th instance + user shares the bot's broken reply as live proof

## What happened

Jeffrey asked in C0AH3RY3DK6 `p1781394331.504119`: *"Why are replies still going out of thread and why are we struggling so much to fix? Look at PRs we merged and /ms to see all our failed attempts."* (4th invocation of "we thought we fixed this?" across this skill's lifetime — instance 11 was the first, instance 12 is the second.)

Then in the same channel he replied: *"Another example <https://jleechanai.slack.com/archives/C0AH3RY3DK6/p1781395161470019>"* — the link points to a **bot's broken top-level orphan** in C0AH3RY3DK6.

## What the link actually is (verified live)

```
ts:           1781395161.470019
thread_ts:    None            ← TOP-LEVEL ORPHAN, not self-rooted
user:         U0AEZC7RX1Q     ← hermes bot
channel:      C0AH3RY3DK6     ← WorldArchitect, NOT the home channel
```

The bot was supposed to post a CI-queue status follow-up to the wa-2346 thread, but the gateway stripped `:thread_ts` and the post fell to channel root. **10 seconds later the same bot posted a near-duplicate at `1781395171.140989`** — Failure 4 narration leak (runtime emitted a follow-up text block, gateway serialized it as a separate `chat.postMessage`, also top-level).

So Jeffrey's "another example" is a Failure 1 + Failure 4 combo: 2 orphans in C0AH3RY3DK6 channel root, neither threaded.

## Why this instance is special (deltas from instance 11)

1. **Jeffrey sent the bot's broken reply as the proof.** He didn't say "you posted in the wrong place" — he linked to the broken post itself. He's not asking for diagnosis; he's asking the gateway to be fixed. The diagnostic skill has done its job. The fix surface is `jleechanorg/agent-orchestrator#684`.
2. **Jeffrey added two earlier PR-search hints** in his question: *"look at PRs we merged and /ms to see all our failed attempts."* This is an explicit instruction to enumerate prior attempts. The honest answer is the workarounds list (11+ sessions, 3 post paths, 1 SOUL rule, 1 skill) — the assistant should NOT just say "use Path B."
3. **The right reply target was the orphan, not a new top-level.** Replying in a new channel-root message would have been a 3rd orphan. Replying via `send_message` would have re-triggered the bug. Replying via Path B curl with `thread_ts=1781395161.470019` made the broken orphan into the parent of the actual answer — the thread is now self-documenting for next time someone searches Slack for "out of thread."
4. **Confusion between the two Slack thread-routing bugs is the most common reply error.** The user said "out of thread." There are TWO bugs:
   - **Bug A** (channel-root leak on context compression) — `jleechanorg/hermes-agent#27` MERGED 2026-06-12, fix live in `gateway/run.py:14681` (`_status_thread_metadata`)
   - **Bug B** (`send_message` strips `:thread_ts` from `target=slack:CHAN:thread_ts`) — `jleechanorg/agent-orchestrator#684` OPEN, no PR
   PR #27 *looks* like the same bug (Slack thread, hermes-agent repo) but it's a different failure mode. Conflating them is what makes the user feel like the bug never gets fixed.

## How to verify the live `hermes` gateway has Bug A's fix

```bash
# 1. Where does `hermes` actually run from?
which hermes
# → $HOME/.local/bin/hermes (or similar)

# 2. Follow the shebang to the venv
head -1 $HOME/.local/bin/hermes
# → #!$HOME/projects_other/hermes-agent/.venv/bin/python3

# 3. Check the live gateway source for the fix
grep -n "_status_thread_metadata" $HOME/projects_other/hermes-agent/gateway/run.py
# → 14681:  _status_thread_metadata: Optional[Dict[str, Any]] = {
# → 14695:  _status_thread_metadata = {"thread_id": _progress_thread_id}
# → 14697:  _status_thread_metadata = self._thread_metadata_for_source(...)
# → 14709:  metadata=_status_thread_metadata,
# → 14851:  metadata=_status_thread_metadata,
```

5+ grep hits at the expected file is the proof that PR #27 is **actually running**, not just merged.

The `~/.hermes_prod/` tree is a Hermes-PROD worktree (different repo, the `jleechanclaw` consumer of the gateway), not the live gateway source. **`$HOME/projects_other/hermes-agent/gateway/run.py` is the source of truth** for what `send_message` does at runtime.

## Reply target decision tree (the new thing this session teaches)

When the user posts a Slack link to a *broken post* as proof of a bug, the right reply target is the **broken post itself**, not a new message:

| User's question shape | Right reply target | Wrong reply target |
|---|---|---|
| *"Why are replies still going out of thread?"* + Slack link to broken bot orphan | That orphan (`thread_ts=orphan.ts`) — make it the parent of the answer | A new top-level channel message (becomes a 3rd orphan) |
| *"You posted in the wrong thread"* | The intended parent (use the thread_ts the user is pointing at) | The broken post (adds noise to the wrong conversation) |
| *"Why is the bot narration leaking?"* | The same thread the user is in | A new thread |

**Rule:** reply target = whatever makes the broken thread self-documenting. If the user sent you a broken post as evidence, your answer belongs in that broken post's reply chain. Future agents (or the user re-searching Slack) find the diagnosis in the same place they found the symptom.

## Recovery recipe (re-verified)

```bash
# 1. Source the token (NOT in runtime env)
TOKEN=$(bash -lc 'echo $HERMES_SLACK_BOT_TOKEN')   # 58 chars, xoxb prefix

# 2. Compose the entire reply in a heredoc, write to disk FIRST
cat > /tmp/jeffrey_thread_reply.json <<'JSON'
{"channel":"C0AH3RY3DK6","thread_ts":"1781395161.470019","mrkdwn":false,"text":"..."}
JSON

# 3. Single curl, no probing, no retries
curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @/tmp/jeffrey_thread_reply.json
# → ok: True, ts: 1781395286.695109, thread_ts: 1781395161.470019

# 4. Verify via curl conversations.replies (not MCP — MCP read can be stale)
curl -sS "https://slack.com/api/conversations.replies?channel=C0AH3RY3DK6&ts=1781395286.695109&limit=1" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys; m=json.load(sys.stdin)['messages'][0]
print('match:', m['thread_ts']=='1781395161.470019')"
# → match: True
```

**Critical:** `mrkdwn: false` is required for the formatting (emoji shortcodes, asterisks) to render correctly. With `mrkdwn: true` (default), `*bold*` becomes Slack mrkdwn but emoji shortcodes like `:large_yellow_circle:` get fragmented by Block Kit `rich_text` parsing.

## What I should have done in this session that I almost didn't

- **Did not add a 12th SOUL rule.** The instinct on a "I thought we fixed this?" callback is to add a more specific rule. This session's lesson is the opposite: the rules list is already too long. The right move is to file (or re-ping) the gateway-side issue and offer to dispatch an AO worker for the actual patch.
- **Did not promise "I'll keep fixing workarounds."** I gave the user 3 options (dispatch patch, accept workaround, both) and asked for a call. The previous session's anti-pattern was reaching for Path A/B silently after a "we thought this was fixed" complaint.
- **Did not conflate PR #27 with issue #684.** When the user said "look at PRs we merged," the first instinct is "we merged PR #27, we're done." That's wrong. PR #27 is a *different* bug. Conflating them is what makes the user feel the fix never lands.

## Timeline (TS values, in order)

- `1781394331.504119` — bot dispatch ack in wa-2346 thread (Jeffrey's "why" question lives here, in a follow-up)
- `1781394553.470139` — user follow-up: "Switch worker to minimax cli and /skillify…"
- `1781394556.312829` … `1781394776.364749` — bot narration leak (10+ posts in the same thread, Failure 4)
- `1781394818.261689` — bot final report card
- `1781395004.893469` — agent's first Path B reply (the prior "Honest answer: two separate bugs, only one is fixed" diagnostic) — `thread_ts=1781394331.504119` ✅
- `1781395161.470019` — bot's NEW broken orphan (the link Jeffrey sent) — `thread_ts=None`, channel root
- `1781395171.140989` — bot's 10s-later near-duplicate, also top-level
- `1781395220.018889` — Jeffrey's actual follow-up: the `/wiki-ingest` Gemini gem request (top-level, unrelated to the broken orphan)
- `1781395286.695109` — agent's Path B reply to the orphan — `thread_ts=1781395161.470019` ✅
- Bead `$USER-88x` + issue `jleechanorg/agent-orchestrator#684` — already filed, no new ones needed this session
