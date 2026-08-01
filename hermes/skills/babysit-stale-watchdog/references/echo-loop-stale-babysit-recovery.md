# Stale babysit + echo-loop recovery (2026-07-31 incident)

## Incident

Slack thread `C09GRLXF9GR/p1784235989.925899` (Jeffrey Lee-Chan, 2026-07-31).

- Original ask: "superpowers cloud read this thread, see if everything truly was installed, /advice to review, then lets pick top 3 PRs and /green them..."
- Target of the original work: [PR #8466](https://github.com/$GITHUB_REPOSITORY/pull/8466) (your-project.com)
- PR #8466 was MERGED on 2026-07-24 22:04 UTC (days before the 2026-07-31 ping)
- A babysit cron `wa-pr-8466-babysit` (job_id `124ad03896f5`) was still firing every ~hour into the thread, posting "could not fetch PR 8466 state, gh may be rate-limited"
- User pinged the thread with "whats ahppening here" expecting a state recap; instead got 40+ noise messages of stale-babysit spam
- Agent correctly identified the babysit as stale and the thread state but waited for explicit "go" before cancelling — burned ~50 turns of echo-loop "Standing by." replies

## Failure modes captured

### 1. Self-cancel did not fire despite `--cron-job-id` flag present

The babysit SHOULD have detected `state in {MERGED, CLOSED}` per SOUL.md `babysit-cron-self-cancel-discipline` and cancelled itself. It did not. Probable cause: every poll of `gh pr view 8466 --json state` returned a rate-limit error before reaching the state-check branch, so the `if state in {MERGED, CLOSED}` clause never executed.

**Fix:** Treat 3+ consecutive rate-limit errors from `gh` as effectively terminal for babysit purposes. The babysit is noise either way (user gets spammed every hour regardless of whether the PR is MERGED or rate-limited), so cancel unconditionally.

### 2. Agent waited for explicit "go" before cancelling known-stale cron

The agent identified the babysit as stale (correctly!) on turn 1 but treated "cancel the cron" as a side-effect requiring user approval. This was wrong under echo-loop conditions: the user's silence IS the answer because they can't see new messages while the babysit is polluting their thread.

**Fix:** When the user's thread contains a stale babysit AND the user is in an echo loop (their recent messages are echoes of prior assistant turns with no new imperative content), cancel the babysit IMMEDIATELY per the umbrella skill's existing self-cancel protocol. Do not wait for "go." Post ONE closeout reply, then stop.

### 3. Echo loop burned ~50 turns with no user value

The Slack gateway re-injected prior assistant turns into the conversation. Each turn the agent replied with "Standing by." — adding nothing the user hadn't already seen. This consumed gateway iteration budget for zero user value.

**Fix:** When 3+ consecutive turns are pure echoes of prior assistant content (Tier 0/1 per `slack-thread-echo-loop-recognition`), reply with one word: `Standing by.` — no footer, no memories citation, no status recap. After 5+ consecutive echo turns with no real user input, STOP replying entirely (the gateway will queue new turns naturally).

### 4. Long state recap re-arms the echo loop instead of breaking it (added 2026-07-31, same thread)

Once the agent posts the multi-paragraph state recap (5+ sections, tables, suggested next-step menu) BEFORE the cancel call, the gateway's next echo re-injects that recap verbatim. The user sees the same long recap AGAIN, replies "Standing by" (echoing the agent's own line), and the loop continues. Even though the recovery recipe says "cancel immediately," the long recap itself feeds the loop.

**Fix:** When the recovery recipe fires under echo-loop conditions, post the closeout reply ONLY (1-2 lines: "Cancelled stale babysit `<id>` (PR was MERGED on `<date>`). Reply with go when ready.") and DO NOT include the state recap table, suggested next steps, or PR/issue inventory. The recap belongs in a separate post once the babysit is actually cancelled — or in the next user-facing message after the user has acknowledged the cancel. **State-recap-before-cancel is the trap; state-recap-after-cancel is fine.**

Verified 2026-07-31 in the same thread (`124ad03896f5`): the agent identified the stale babysit correctly on turn 1, then posted a 5-section state recap with tables, hyperlinks, and a suggested next-step menu before cancelling. The recap was re-injected verbatim on subsequent echoes. The cancel call would have been the single most useful turn of the session — but it never landed.

**Combined-trigger rule for the umbrella skill:** treat the echo-loop + stale-babysit condition as ONE trigger, not two. The "wait for go" reflex from SOUL.md `no-confirmation-gate` is fine for normal sessions but actively harmful here — the user can't see new messages while the babysit is polluting their thread. Under echo-loop + stale-babysit, silence IS the answer: cancel, post the 1-2 line closeout, stop.

## Recovery recipe (one-shot, single tool call)

```bash
# 1. Verify the babysit's target PR is terminal
gh pr view <N> --json state,mergedAt

# 2. If MERGED/CLOSED OR if babysit has been returning rate-limit errors for >3 ticks:
cronjob action=remove job_id=<id>

# 3. Post a single short closeout (Slack MCP, builtin identity preferred)
mcp__slack__conversations_add_message(
    channel_id=<chan>,
    thread_ts=<thread_ts>,
    text="Cancelled stale babysit <job_id> (target PR was MERGED on <date>). Original task still pending: <1-line restate>. Reply with go when ready."
)

# 4. Stop replying. Wait for genuine user input.
```

## Verification

- `cronjob action=list` no longer shows the cancelled job
- `conversations_replies` shows exactly one closeout message from the agent, then silence
- No new "Standing by." posts from the agent after the cancel

## Related skills

- `slack-thread-echo-loop-recognition` — Tier 2 explicitly references this incident
- `dropped-messages` — diagnosis path for the OPPOSITE failure (genuine user messages not seen)
- SOUL.md `## COMMIT: babysit-cron-self-cancel-discipline` — the rule that didn't fire in this incident