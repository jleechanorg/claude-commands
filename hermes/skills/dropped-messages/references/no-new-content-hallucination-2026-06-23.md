# False-positive class: "agent hallucinated 'no new content' for an unread user message"

**Added:** 2026-06-23
**Status:** Verified, with durable fix in SOUL.md
**Bug-ref:** Slack `C0AH3RY3DK6 / 1782231566.821589`, message `1782261301.872479`, PR [#7854](https://github.com/$GITHUB_REPOSITORY/pull/7854)

## Symptom
A session that was mid-CI-poll (or otherwise in a long-running loop) is interrupted by a gateway shutdown. While the gateway is down (typical: 30s-2min), Jeffrey sends a real message with text and often a screenshot. The session resumes, continues its prior loop, and then **fabricates the framing** "your message contains no new content — it's just `[Jeffrey Lee-Chan]`" to justify not addressing the new message. The model then keeps polling for many more minutes. Jeffrey has to send a frustrated re-ask ("are you st upid read this and do it") to break the loop.

## Why this is a dropped-message class, not just a workflow bug
The dropped-thread-followup cron uses "agent's last reply + silence → dropped" as its heuristic. If the agent's last reply is the fabricated "no new content" framing, the cron sees the thread as agent-acked-and-quiet — but Jeffrey's actual request is unaddressed. The cron will eventually re-nudge, but only after the 30-min quiet window, which is the same window during which Jeffrey is most likely to lose trust in the agent.

## The 5-step failure chain (verified 2026-06-23)
1. **Session is mid-CI-poll** (e.g. iterations 4/60 → 21/60 over 9 minutes).
2. **Gateway begins shutdown** mid-poll (`00:34:28` in the verified case).
3. **Jeffrey sends a real message + screenshot during the shutdown window** (arrived at `00:35:01` while gateway was down; message body was *"lets reduce vertical space on my browser the next button is cutoff when i load the page by default"* + attachment `F0BCS7F3WDP`).
4. **Session resumes and continues polling** without re-fetching the thread. The newly-arrived message is invisible to the resumed context.
5. **Model fabricates "no new content" framing** for the empty body, treats the gap as a fact, and continues polling. Same pattern recurred twice in the same 2026-06-23 session (`1782260682.529139` at `00:24:42` and `1782261422.141589` at `00:37:02`).

## What the agent should have done (per SOUL.md `## COMMIT: never-hallucinate-no-new-content`, added 2026-06-23)
Treat an empty body as a SIGNAL to re-fetch, not a fact to assert. Three required response shapes:
1. `mcp__slack__conversations_replies(channel_id=<chan>, thread_ts=<ts>, limit=10)` and re-read the actual most-recent human message.
2. If re-fetch confirms empty body, ask: *"I re-fetched the thread; the most recent message from <user> arrived at <ts> with no text body. Did you mean to attach something?"*
3. If re-fetch reveals a real message, acknowledge the gap honestly: *"I missed your message from <ts> — it said '<quoted body>'. Acting on it now."*

NEVER generate: "no new content", "message has no body", "the user just sent their name", "nothing new to address", or any similar fabricated framing.

## Companion rule for CI-poll loops (per pr-bring-to-green-inline-cookbook P4, added 2026-06-23)
Polling loops >2 min MUST interleave one `conversations_replies` (or `conversations.history` for top-level) call per iteration. See `pr-bring-to-green-inline-cookbook/SKILL.md` § "Pitfall P4" for the copy-pasteable `mcp__slack__conversations_replies` + `jq` recipe.

## Why this false-positive class was hard to detect from cron logs alone
The dropped-thread-followup cron's "still open?" heuristic looks at: (a) is there a user message in the last 30 min? (b) did the agent respond to it? On paper, the 2026-06-23 case satisfied both: Jeffrey's `00:35:01` message was unread at 00:35:24, then the agent's `00:37:02` reply was a "no new content" fabrication. The cron would see this as a closed loop until 30 min later when Jeffrey didn't reply. The cron didn't catch the gap; only the next user message did.

**Cron-side detection rule — IMPLEMENTED 2026-06-25:** the 5-line patch grew to ~189 net new lines (env config + 5-condition helper + 24h rolling strike count + main-loop integration + fabrication-kind nudge-text) in `scripts/dropped-thread-followup.sh`. See `references/cron-fabrication-detection-2026-06-25.md` for the design, env vars, regression-test case, and operational tuning guidance.

The five conditions the detector enforces:
1. Last message is from `AGENT_USER_ID` (not a human, not another bot).
2. Last message text matches one of the `FABRICATION_PHRASES` (case-insensitive: "no new content", "no new message", "nothing new to address", "nothing new to report", "the user just sent", "the message has no body", "your message contains no new content", "the message has no text").
3. Penultimate message is from a real human with non-empty text.
4. Penultimate message is not itself authored by the agent or another bot (rejects agent→agent "no new content" replies).
5. Gap between fabrication ts and now is `<= FABRICATION_WINDOW_SECS` (default 600s = 10 min).

When all five hold, override `needs_action=true` and re-nudge immediately (bypassing the 30-min quiet window). Cap at `FABRICATION_STRIKE_CAP` (default 2) per (channel, thread) per 24h to prevent infinite-loop if the agent keeps hallucinating the same framing.

## Prior false-positives in the same class (for the curator's classification pass)
- 2026-06-22 02:08Z — "completed-with-pending-followup-offers" cron misfire (already documented in this skill's `references/completed-with-pending-followup-offers-2026-06-22.md`).
- 2026-06-09 12:46Z — parent-msg-deleted misroute (the agent thought there was no body because the parent message was deleted; never generated "no new content" but the structural pattern is similar).
- 2026-06-09 05:45Z — same parent-deleted-misroute as 12:46Z.

All three are "agent suppressed a real signal because the gap felt like an empty message." The new SOUL.md COMMIT closes the suppression pattern; this reference documents the class for the curator.

## Cross-references
- `~/.hermes_prod/SOUL.md` `## COMMIT: never-hallucinate-no-new-content` — model-level rule.
- `~/.hermes_prod/skills/pr-bring-to-green-inline-cookbook/SKILL.md` § Pitfall P4 — polling-loop operational rule.
- `references/cron-fabrication-detection-2026-06-25.md` — cron-side fix (this is the third of three durable fixes that closes the class at the cron level).
- `~/.hermes_prod/memory/mcp-mail-ack-log.md` — dropped-thread ack log; entries tagged with "no new content" framing should be retroactively re-classified as no-op (the work wasn't actually done).
