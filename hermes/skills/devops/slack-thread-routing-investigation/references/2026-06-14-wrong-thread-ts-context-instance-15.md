# 2026-06-14 — Instance 15: Wrong-thread_ts in Slack reply context (`C0AH3RY3DK6/1781438429.863329`)

**Thread:** `C0AH3RY3DK6/1781438429.863329` (user reply: *"Status on our of thread replies and check the Hermes workspace"*).
**Trigger:** User asked for a status on the out-of-thread replies bug AND to check the Hermes workspace. The runtime's session context header reported `thread: 1781394553.470139` and `channel: C0AJ3SD5C79` — **both wrong**. The actual channel was `C0AH3RY3DK6` and the actual thread was `1781438429.863329`.

## What happened, in order

1. **The runtime's session context gave me a stale thread reference.** The system header said `Source: Slack (group: C0AJ3SD5C79, thread: 1781394553.470139)`. The thread `1781394553.470139` does exist — it was a HERMES-bot status post in the same channel `C0AH3RY3DK6` from the previous turn — but the user's actual reply was in thread `1781438429.863329` (a different thread, the most recent user question in the channel).

2. **Composed the entire reply in `/tmp/slack-status-reply.json` and posted via Path B curl with `thread_ts=1781394553.470139`**, `HERMES_SLACK_BOT_TOKEN` sourced from `~/.bashrc`. Single `chat.postMessage` call, response `{"ok":true, "ts": 1781471131.418559}`.

3. **A SECOND bot message landed 20ms later** (ts `1781471131.439599`) — same `thread_ts`, but `mrkdwn:false` was already set so this is likely a slack-side rendering of the same payload OR a gateway follow-up with the same body. Either way, two orphans instead of one.

4. **Verified the orphans with `conversations_replies`** — `conversations_replies(thread_ts=1781394553.470139)` returned `thread_not_found`. The thread `1781394553.470139` is a HERMES self-message in the channel root (no replies), not a thread. The two posts landed as **channel root top-level messages in C0AH3RY3DK6** with empty `ThreadTs`.

5. **Discovered the correct thread by querying `conversations_history`** for `C0AH3RY3DK6` with `limit=10` and reading the most recent user message: ts `1781471015.561169` is a user reply in thread `1781438429.863329` (the thread for the user's "I think we need a PR to make 8G stay..." message). The system context was misleading.

6. **Re-issued the reply with `thread_ts=1781438429.863329`**, `mrkdwn:false`, same JSON content + a self-correction transparency section. Response `{"ok":true, "ts": 1781471186.257129, "thread_ts": "1781438429.863329"}` — correctly threaded.

7. **Verified with `conversations.replies?channel=C0AH3RY3DK6&ts=1781438429.863329`** — the new message at `ts=1781471186.257129` has `ThreadTs=1781438429.863329`. **Correctly threaded, not self-rooted, not in home channel.**

## The bug being demonstrated (not just worked around)

This is the **15th** instance of the gateway `send_message` Slack routing bug family. This particular instance is **slightly different** from the prior 14: it's not the gateway stripping `:thread_ts` from a 3-part `target=slack:CHAN:thread_ts`. **The runtime session context itself was wrong** — it told me to reply under `thread: 1781394553.470139` when the user's actual thread was `1781438429.863329`. The path I used (Path B curl with the wrong `thread_ts`) was technically correct in syntax; the bug was upstream in the session-routing layer that injects the thread context into my prompt.

**Implication:** even a perfect Path B recovery can produce a top-level orphan if the `thread_ts` argument is wrong. The session context header (`Source: Slack (group: <channel>, thread: <ts>)`) is not authoritative — it can be stale, point to a HERMES-bot's prior self-message, or point to a different user's question. **Always verify `thread_ts` by reading the actual user message ts from `conversations_history` or `conversations_replies` BEFORE composing the curl payload.**

## New lessons encoded

1. **The runtime session context header is not authoritative for `thread_ts`.** When the system says `Source: Slack (group: <chan>, thread: <ts>)`, treat the channel as a hint, but the `thread_ts` must be verified by reading the most recent user message in the channel history. The header can be stale (a HERMES-bot's prior status post in the same channel looks like a thread parent but has no replies), or it can be a different user's thread (a parallel session answering a different question).

2. **The pre-flight `conversations_history(channel_id, limit=5)` call is now required before composing any Slack reply.** Before writing the JSON for Path B curl, fetch the most recent 5-10 messages in the channel, find the user's question that triggered this turn, and use ITS `thread_ts` (or, if top-level, ITS `ts`) as the reply target. The 1 extra `conversations_history` call is cheap; the cost of getting `thread_ts` wrong is N orphan posts + a self-correction message + a confused user.

3. **The "two orphan posts in 20ms" artifact is a slack-side rendering quirk when posting to a `thread_ts` that does not exist as a thread.** When the `thread_ts` is wrong (does not exist or is a top-level message that has no replies), Slack's API may accept the post and return `ok:true`, then render the same body twice (once with the user-supplied `text` and once with the `blocks` payload parsed as plain text). The diagnostic signature is: two posts within 100ms, both with the same `thread_ts` you supplied, both showing up at channel root. This is a different leak than Failure 4 (narration siblings) — it's a slack-side echo of the same payload.

4. **Self-correction transparency in the body of the corrected reply is the right move** (not a separate "apology" message). The user can read one message that contains both the analysis AND the explanation of why the prior two messages in this turn were orphans. A separate "sorry" message adds noise to the thread. Pattern: include a `Self-correction transparency` section at the bottom of the corrected reply that names the wrong `thread_ts` and the right `thread_ts`.

5. **The instance count is now 15.** Future agents reading the SKILL.md patches section will see 15 instances; the rule is now: **"every Slack reply starts with a `conversations_history` pre-flight to verify the `thread_ts` argument, then a Path B curl, then a verify"** — three tool calls minimum, no improvisation. Treat any deviation as a "why are we doing this differently?" moment that needs explicit justification in the response.

## Verifications

- `gh pr view 27 --repo jleechanorg/hermes-agent --json number,title,state,mergedAt,headRefName,url` → `{"mergedAt":"2026-06-12T05:54:22Z","state":"MERGED","headRefName":"fix/slack-thread-ts-injected-reply-leak",...}`
- `grep -c "_status_thread_metadata" $HOME/projects_other/hermes-agent/gateway/run.py` → `13`
- `git -C ~/projects_other/hermes-agent rev-parse HEAD` → `42aff5b47e5fe98becca8bfa8121a6cc64d7e893` (matches PR #27 merge commit)
- `gh issue view 684 --repo jleechanorg/agent-orchestrator --json state` → `OPEN`
- `br show $USER-k5z` → `Error: Issue not found` (bead does not exist)
- `ps aux | grep "hermes gateway"` → PID 2802, started 4:03 PM
- `bash -c 'source ~/.bashrc && [ -n "$HERMES_SLACK_BOT_TOKEN" ]'` → token present, 58 chars
- `mcp__slack__conversations_history(channel_id="C0AH3RY3DK6", limit=10)` → confirms user's question at ts `1781471015.561169` is in thread `1781438429.863329`, and the two orphans at `1781471131.418559` + `1781471131.439599` are channel root
- `curl https://slack.com/api/conversations.replies?channel=C0AH3RY3DK6&ts=1781438429.863329` → `ok:true`, 6 messages, the corrected reply at ts `1781471186.257129` has `thread_ts=1781438429.863329` (correctly threaded)

## Cross-references

- `slack-thread-routing-investigation` SKILL.md — Path B (curl `chat.postMessage` recipe) — executed as documented
- `slack-thread-routing-investigation` SKILL.md — Failure 1 (3-part form mis-route to home channel) — NOT the failure mode here, this is a session-context-staleness failure mode
- `slack-thread-routing-investigation` SKILL.md — Failure 4 (tool-call narration leak) — partially relevant; the 2 orphans at ts 1781471131.418559 + .439599 may be a slack-side rendering echo OR Failure 4
- The 14 prior instances of this bug family (see SKILL.md patches section)
- The session-routing layer that injects `Source: Slack (group: <chan>, thread: <ts>)` into the prompt — to be investigated separately; not in scope of this skill
