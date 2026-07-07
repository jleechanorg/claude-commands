---
name: finish-the-job/2026-06-19-originating-incident
description: Verbatim source message + the dropped-thread evidence that motivated the finish-the-job skill, plus the user's explicit rule.
type: reference
---

# The originating incident — 2026-06-19

## User's verbatim ask (Slack thread `C09GRLXF9GR/1781899673.923589`)

> Look at the last week of slack threads with work that started but didn't finish. I am able to start threads but not enough time to steer them to a conclusion. Is there some way we can /skillify Hermes to be more hands off? I want it to fully drive everything to a conclusion like a final /green PR that has non unit test evidence or a finished chsnge or dry run to local machine state for non PR work. Look at the /fs and /f command maybe we should always use that? I would rather invest more time up front in Q&A versus needing to intervene in the middle for sometimes steering that seems like the AI could've done it. I ln the middle I want AI to use its best judgement and I am ok with outcomes that aren't my goal as long as they are correct ie. Green PR, real evidence, like correct but misinterpret is fine but stopping halfway is not

Follow-up reply (selected option):

> Let's do 1) full solution for end2end

## The drift patterns observed

From the last week of dropped-thread data (`dropped-thread-followup.sh` audit, 2026-06-12 → 2026-06-19):

1. **Ack + design prose + silence** — agent acknowledges, writes 200 lines of design options, asks one more clarifying question, never executes.
2. **Started + fork + multi-option question** — agent reads files, makes a local commit, hits a judgment call, posts a 3-option menu. User doesn't reply (busy). Thread goes cold.
3. **Investigation without end-state** — agent reads 6 files, posts "Here's what I found: …" with no PR, no commit, no dry-run. The "I'm waiting for the right moment to ship" trap.

## The user's explicit rule (load-bearing)

> I am ok with outcomes that aren't my goal as long as they are correct ie. Green PR, real evidence, like correct but misinterpret is fine but stopping halfway is not.

Translation:

- The agent MAY choose a different outcome than the user originally asked for, AS LONG AS that outcome is **provably correct** (green PR, real evidence, finished state).
- The agent MAY NOT stop without producing a provably-correct end-state.

This rule is **load-bearing** — it overrides the assistant's default "ask before guessing" behavior. When in doubt, make the call.

## Why the skill was created as `finish-the-job` (not `auto-finish` or `hands-off`)

The skill name should describe the **pattern class**, not the user's specific scenario. `finish-the-job` captures the contract: when a goal has been handed off, finish it. The trigger phrases are the user's actual phrasings from this incident.

## Why the SOUL.md `## COMMIT:` block is mandatory

Without the SOUL.md commit, the skill only loads when the user types `/finish <goal>` or one of the trigger phrases exactly. The user's actual pattern is to describe goals in natural language ("Investigate how did this happen", "Read my email which keys got leaked", "Make a /green PR using AO to switch the order") — without the commit, those goals do not auto-route to `finish-the-job`. With the commit, every goal-shaped user message triggers Phase 0 classification.
