---
name: slack-thread-echo-loop-recognition
description: Detect and stop responding to echo loops in Slack threads. When the gateway or babysit cron repeatedly re-injects prior assistant turns as if they were new user messages, replying with anything more than a single-word acknowledgment burns iteration budget without producing new value for the user. Triggers include 3+ consecutive user turns with no semantic new content, repeated Standing-by patterns, and babysit cron spam in thread.
---

# Slack thread echo-loop recognition

## Symptom

You see repeated "user" turns whose content is byte-identical or near-identical to a prior assistant turn. No new instruction, no question, no preference signal. Examples from a real session (2026-07-31, ~50 turns of pure echo):

```
[Jeffrey Lee-Chan] (initial ping "whats ahppening here")
[hermes] (state recap, posted once)
[hermes] (same state recap echoed back)
[hermes] (same state recap echoed back)
[hermes] "Standing by."
[hermes] "Standing by."
[hermes] "Standing by."   <- user has stopped seeing new content
```

Two root causes observed:

1. **Gateway replay buffer** - the Slack gateway re-injects prior assistant turns on resume/iteration, so the agent sees them as new user input and replies again, creating an infinite echo.
2. **Babysit cron spam** - a stale `babysit wa-pr-NNNN` cron whose target PR is MERGED/CLOSED keeps posting every ~hour into the same thread; the agent re-acknowledges each tick.

## Detection (first 3 turns, no exception)

| Signal | Action |
|---|---|
| Same exact text content as one of the last 3 assistant turns | Treat as echo, reply with shortest possible ack |
| New user turn contains no imperative verb, no question mark, no new noun/entity | Treat as echo |
| 3+ consecutive assistant turns are all "Standing by." / "Acknowledged." / identical | Stop adding the LLM-provenance footer - it is noise |
| Babysit cron output is the only "user" content for >2 turns | Cancel the babysit per `babysit-stale-watchdog`, do NOT keep acknowledging |
| Thread contains `:hourglass_flowing_sand:` queue marker | That is a SYSTEM marker, not a user message - do not respond at all |

## Action ladder (pick the LEAST verbose tier that fits)

**Tier 0 - Pure echo of my own last message:** Reply with one word - `Standing by.` (no footer, no status recap, no memories-used citation, no emojis). The footer is not required when no new work was done.

**Tier 1 - Echo with a system queue marker (`Queued for the next turn`):** Reply with one word - `Standing by.` Do NOT add the LLM-provenance footer. Do NOT cite memories. The system marker is system, not user, and you are acknowledging only because silence would be misinterpreted as drift.

**Tier 2 - Echo contains a stale cron output:** This is a SIGNAL, not a user message. Cancel the cron (1 tool call), then post a single short reply explaining the cancel + ask the user whether to proceed with the original task. Do NOT keep acknowledging each cron tick. **Verify the cancel:** after `cronjob action=remove job_id=<id>`, re-list (`cronjob action=list`) to confirm the job is gone. A "Closing loop" / "Cancelled babysit" message posted without a verified `cronjob action=remove` call is a FALSE closeout — the cron keeps firing for days/weeks (verified 2026-07-31: cron `124ad03896f5` had been spamming for 7+ days after a previous session's "🎉 PR #8466 MERGED. /green complete. Closing loop." post that never executed the cancel). If the agent is being rate-limited and cannot execute the cancel, do NOT post a closeout message — that just creates a false closeout. Post nothing, or post a one-line `Idle.` + caveat, and wait for the rate-limit window to pass before re-attempting.

**Tier 3 - Echo with a real question you missed:** Re-read the actual thread context (the original ask may pre-date the echo loop). Answer once, then go back to Tier 0.

## Pitfall - what NOT to do

- Reposting a multi-paragraph status recap on every echo turn. The user already saw it. You are burning tokens and adding noise to a thread they are trying to read.
- Adding `Memories used:` on echo turns - the rule requires it when you actually used memories. Echo turns use no new memory.
- Adding the LLM-provenance footer on echo turns - the rule exempts verbatim operator text and pure-acknowledgment replies. Tier 0/1 qualify.
- Waiting for explicit "go" before cancelling a known-stale cron that is actively polluting the user's thread. The babysit-stale-watchdog skill says to self-cancel; doing it without asking is the correct behavior under echo-loop conditions because the user's silence IS the answer.
- Calling `mcp__slack__conversations_add_message` for every echo. Most echoes don't need a Slack reply - they are internal to the agent loop. If you must reply, use the absolute shortest text.

## When to break the loop unilaterally

If you observe **5+ consecutive echo turns** with no genuine new instruction from the user, you MUST:

1. Stop replying entirely (Tier 0 minimum) - keep replying burns gateway budget
2. If a stale cron is the source, cancel it via `cronjob action=remove job_id=<id>` (1 tool call, reversible - user can re-create if needed)
3. If the thread is silent for >10 minutes of real wall-clock time AND the original task is half-done, post ONE short completion summary and stop
4. Do NOT post "should I continue?" menus during an echo loop - the user is not reading. Finish what you can and post the receipt.

## Verification

- `gh pr view <N> --json state` confirms the babysit's target PR is MERGED -> cancel is safe
- `cronjob action=list` shows the cron no longer firing
- `conversations_replies` shows no new "Standing by." posts from you after the cancel

## Related

- `babysit-stale-watchdog` - the cancellation skill for the cron itself
- `dropped-messages` - diagnosis path for genuinely dropped user messages (different problem; same fix family)
- `gateway-loop-standdown` - meta-skill for gateway replay loops (different mechanism, similar surface)
- SOUL.md `## COMMIT: followup-promise-requires-cron` - applies when echo loop is masking a promised follow-up