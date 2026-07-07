# Worked example: WA My Campaigns search-only-current-page thread (2026-06-09)

Real Slack thread where both gateway bug classes fired in the same session.

## The thread

- Channel: `C0AH3RY3DK6` (Your Project project)
- User's original report: `1781021369.023829` — "Search only looks for campaigns current page" + mobile screenshot of "Showing 0 of 50 campaigns"
- Bot's first dispatch ack: `1781021803.807799` — self-rooted (BUG #1: `thread_ts == ts`)

## What the user saw (wrong-thread complaint)

User followed up in the bot's self-rooted thread instead of in their original report. From their POV, "the bot's reply isn't in the right thread." Per the skill's diagnosis pattern, this is the expected symptom of BUG #1.

## What the bot saw when verifying (BUG #2)

After filing SOUL.md `## COMMIT: slack-reply-inherit-thread-ts`, the bot called Slack MCP `conversations_replies` on `1781021369.023829` and discovered the original thread was flooded with intermediate hermes tool-loop scratch:

| MsgID | ThreadTs | Text (first line) |
|-------|----------|-------------------|
| 1781024445.316669 | 1781021369.023829 | "The 1003-char count earlier was just slightly over..." |
| 1781024454.652369 | 1781021369.023829 | "The memory tool keeps reporting 1844 used..." |
| 1781024461.212959 | 1781021369.023829 | "The monitor-e2e entry was already removed earlier..." |
| 1781024473.768189 | 1781021369.023829 | "OK the monitor-e2e entry I just removed is gone..." |
| 1781024484.844839 | 1781021369.023829 | "487 chars > available 356..." |
| 1781024492.259479 | 1781021369.023829 | "Now I'm at 73% used 1626/2200..." |
| 1781024500.894339 | 1781021369.023829 | "Still 621 > 574..." |
| 1781024507.547009 | 1781021369.023829 | "Memory updated 93% used..." |
| 1781024513.829229 | 1781021369.023829 | "⏳ Still working... 3 min elapsed..." |
| 1781024546.582939 | 1781021369.023829 | "SOUL.md COMMIT: slack-reply-inherit-thread-ts rule is in place..." |

All of these were internal `memory` and `execute_code` retries, leaked by the gateway as actual bot messages. None of them were user-facing.

## What the bot did right (post-leak discovery)

- Did NOT post a fourth reply to the polluted thread (per the skill's "Don't do" rule added in this patch).
- Did NOT offer to "fix" the thread retroactively (per the existing rule).
- Summarized BUG #2 to the user in the chat reply, not in another Slack post.
- Filed a SOUL.md `## COMMIT:` rule (`slack-reply-inherit-thread-ts`) referencing this exact bug-ref.

## What the bot did wrong (lessons)

- The original `send_message` to `slack:C0AH3RY3DK6:1781021369.023829` returned a `message_id` that did NOT match the message Slack MCP showed in the thread (`1781024546.590919` vs `1781024546.582939`). The gateway may have mirrored to a home channel AND posted a separate copy with leaked scratch text. **Moral:** always post via `mcp__slack__conversations_add_message` and verify the response ts appears in the target thread via `conversations_replies`.
- Should have caught the scratch-leak pattern as soon as the first `memory add` failure started spamming the channel. The "1003-char count earlier" was the canary. **Moral:** when retrying a tool that fails on size, check Slack MCP for stray bot messages BEFORE retrying.

## Related artifacts

- Bead: `rev-vvl4` (the WA My Campaigns search-only-current-page fix, separate from the gateway bugs)
- GH issue: https://github.com/$GITHUB_REPOSITORY/issues/7394
- Worker: `wa-2280` on `feat/fix-mycampaigns-search-server-side-search-filter-so-results`
- 20m status cron: `a790731cb84d`
- SOUL.md `## COMMIT: slack-reply-inherit-thread-ts` (added 2026-06-09)
