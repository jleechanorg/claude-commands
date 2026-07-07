---
name: dropped-messages/5b-leak-framing-false-alarm-2026-06-19
description: When the inbound message is wrapped with "5b-leak safety-net alert" / "manual re-thread required" / "fragmented message detected" prefixes, the wrapping itself can be the leak — fetch the inbound body via Slack MCP before doing any re-threading. Verified 2026-06-19 on C0AKALZ4CKW/1781870379.607479.
type: reference
---

# "5b-leak safety-net alert" framing — false alarm recipe (added 2026-06-19)

> **Verified 2026-06-19, `C0AKALZ4CKW/1781870379.607479` "5b-leak safety-net alert — agento reaction.escalated PR #632 backfill respawn cap":** the inbound preview was cut off mid-URL (`PR\nBa`), but `mcp__slack__conversations_replies` returned the full intact text. The actual operational issue was Green Gate Gate 3 (`CR approved = state=none`), not a missing message that needed re-construction.

## The trap

When an inbound message arrives wrapped with prefixes like:

- `*5b-leak safety-net alert* — channel <#C0AKALZ4CKW> ts=1781870379.607479 reason=emoji::rotating_light: — manual re-thread required`
- `*Fragmented message detected* — partial body, reconstruct from session_search`
- `*Agent narration leak* — gateway auto-mirror overflow`

…the natural reflex is to start re-threading or recovering. **But the prefix itself can be the leak.** The wrapping text was emitted by a cron/Hermes process that itself got truncated; the embedded message body arrived intact in Slack. Re-threading without verification:

1. Writes the "leaked" reply twice (the original + the reconstruction, both visible in the user's thread).
2. Wrong action: reconstructs a message that didn't need reconstruction, instead of acting on the underlying operational issue (e.g. PR #N backfill cap, not "re-thread this message").
3. Burns tool calls on `find $HOME -name "F0BA72FJKD4*"`-style local searches for "where is the missing text" when the text was never missing — it was always at the inbound `ts` in Slack's CDN.

## The discipline

1. **First tool call on any "5b-leak" / "fragment detected" / "re-thread required" prefix:** `mcp__slack__conversations_replies(channel_id=<chan>, thread_ts=<inbound_ts>, limit=5)`. Pull the actual message body via Slack MCP — do not trust the inbound wrapper.

2. **Compare the inbound wrapper against the fetched body.** If the fetched body is **intact, complete, and self-contained** (e.g. a `:rotating_light: agento reaction.escalated` backfill-cap alert with full PR URL + full reason string), the "leak" framing is a **false alarm** — the agent that wrapped the message got truncated itself, but the underlying message arrived fine.

3. **If intact, do NOT re-thread.** The reply shape is:
   - **One-line confirmation**: "Fetched via Slack MCP `conversations_replies` against `ts=<inbound_ts>` in `<channel>`. Message is intact, NOT a leak. Full text recovered verbatim: `<body>`"
   - **Then treat the underlying message as the work item**, not as a leak. The `:rotating_light: agento reaction.escalated` text is a real operational alert (e.g. "Backfill respawn cap reached for PR #N") that needs diagnosis and dispatch.

4. **If the fetched body really is fragmented** (cuts off mid-sentence, missing fields, broken mrkdwn, dropped URL), then re-thread per the standard "Recovery workflow" in `dropped-messages/SKILL.md`. **But verify first — do not assume.**

## Anti-pattern vs correct pattern

**Anti-pattern (don't do):**

```
1. Receive Slack message → "*5b-leak safety-net alert*" + fragmented preview
2. Load dropped-messages skill
3. Start composing a "recovered message" reconstruction
4. Post the reconstruction to the thread
5. ... user sees the original message AND the reconstruction, neither is
   what they actually wanted, which was for the agent to ACT on the
   operational alert (PR #632 backfill cap, not "re-thread this message")
```

**Correct pattern (do this):**

```
1. Receive Slack message → "*5b-leak safety-net alert*" + fragmented preview
2. mcp__slack__conversations_replies(channel_id=<C0AKALZ4CKW>, thread_ts=<1781870379.607479>, limit=5)
3. Read the fetched body: full text intact, posted by Hermes (U0AEZC7RX1Q), NOT fragmented
4. Recognize: the inbound wrapper itself was the "leak"; the underlying message
   is a real `agento reaction.escalated` backfill-cap alert
5. Reply in-thread with: re-thread-check verdict + real-issue diagnosis +
   single-decision prompt for the underlying alert
```

## Verified worked example — 2026-06-19

**Inbound preview (fragmented):**
> `*5b-leak safety-net alert* — channel <#C0AKALZ4CKW> ts=`1781870379.607479` reason=`emoji::rotating_light:` — manual re-thread required. preview: `:rotating_light: *agento* `reaction.escalated` [jleechanclaw/jc-orchestrator] | <https://github.com/jleechanorg/jleechanclaw/pull/632|PR>\nBa``

**Fetched body via Slack MCP (intact):**
> `:rotating_light: *agento* reaction.escalated [jleechanclaw/jc-orchestrator] PR https://github.com/jleechanorg/jleechanclaw/pull/632 - PR, Backfill respawn cap reached for PR 632: 3 prior workers archived. Human intervention required check quota, fix blockers, or manually spawn.`

**Real diagnosis (not a leak, an operational alert):**
- PR [#632](https://github.com/jleechanorg/jleechanclaw/pull/632) "fix(deploy): retry Stage 5 canary once after 30s" had 4 failing Green Gate runs since 2026-06-19 11:40Z.
- Latest Green Gate verdict (PR comment `id=4751360032`): all gates PASS except Gate 3 = `state=none` because CodeRabbit has only posted 19 PR-level comments, never a review submission with `state=APPROVED`.
- Two sibling PRs in the same pattern: [#638](https://github.com/jleechanorg/jleechanclaw/pull/638) and [#708](https://github.com/jleechanorg/agent-orchestrator/pull/708).

**Recovery turn actions (12 tool calls, 1 user-facing reply):**
1. `skill_view(name='dropped-messages')` — context-loading (the skill itself was the one being patched)
2. `mcp__slack__conversations_replies(channel_id='C0AKALZ4CKW', thread_ts='1781870379.607479', limit=10)` — fetch the actual body (1 call)
3. `terminal`: `gh pr view 632 --repo jleechanorg/jleechanclaw --json ...` — full PR state
4. `terminal`: `gh pr list --repo jleechanorg/jleechanclaw --state all --limit 20` — sibling PR list
5. `terminal`: `gh run view 27824209616 --repo jleechanorg/jleechanclaw --job 82345573396 --log-failed` — Green Gate job log
6. `terminal`: `gh api repos/jleechanorg/jleechanclaw/contents/.github/workflows/green-gate.yml --jq '.content'` (decoded) — Green Gate logic
7. `terminal`: `gh api "repos/jleechanorg/jleechanclaw/issues/632/comments?per_page=50"` — last Green Gate verdict table
8. `terminal`: `gh api "repos/jleechanorg/jleechanclaw/pulls/632/reviews"` — CR reviews (0 rows = the smoking gun)
9. `terminal`: `gh pr diff 632 --repo jleechanorg/jleechanclaw` — verify the actual code change is small (221 +/1-)
10. `mcp__slack__conversations_history(channel_id='C0AKALZ4CKW', limit='1d')` — confirm channel context + sibling alerts
11. `send_message target='slack:C0AKALZ4CKW:1781870379.607479'` — consolidated in-thread reply with re-thread-check verdict + gate table + sibling PR list + single yes/no decision prompt
12. `mcp__slack__conversations_replies(channel_id='C0AKALZ4CKW', thread_ts='1781870379.607479', limit=3)` — verify the reply landed correctly

**Net user-visible output:** 1 well-formed consolidated reply at `ts=1781871553.068139` in-thread. No re-threading, no "where is the original" follow-up needed, no duplicate noise.

## Companion rules

- **Use `mcp__slack__conversations_replies` for the FETCH** (read-only — no risk of self-rooting).
- **Use `send_message target=slack:CHAN:THREAD_TS` (or curl with explicit `thread_ts`) for the REPLY** — the 3-part target form works as of 2026-06-16 for thread routing per the `slack-messaging` skill. The "always-fail" framing in older skill versions is now historically accurate but operationally out of date.
- **Verify the reply landed** with a follow-up `conversations_replies` (MCP read is fine for verification per `slack-messaging` — the staleness pitfall applies to write-then-read, not to fetch-then-verify-after-write).
- **For redrive / dropped-thread sweep replies, post as MCP mail bot (`U0A4G7LDJ4R`), not Hermes** — see `references/redrive-post-as-mcp-mail-bot-2026-06-19.md`. This 5b-leak case is NOT a redrive (it's a single inbound alert), so Hermes posting is fine.

## When to apply this rule

Any inbound Slack message whose text contains:

- `5b-leak safety-net alert`
- `manual re-thread required`
- `fragmented message detected`
- `agent narration leak`
- `partial body, reconstruct`
- `gateway auto-mirror overflow`

…and whose **embedded body preview is visibly truncated** (cut off mid-URL, mid-tag, mid-markdown). The triggering signal is the COMBINATION of (1) framing prefix that says "act on this as a leak" + (2) visibly truncated preview. Either alone is fine — the framing prefix without truncation is a normal operational alert (act on it directly), and truncation without a framing prefix is just a normal Slack text-length display artifact (read it via MCP, reply normally).

## Cross-references

- `slack-messaging` → "Verify routing after posting" — companion for the reply step
- `slack-messaging` → "Strip internal narration from final assistant responses" — gateway auto-mirror of terminal-tool narration can produce user-visible fragments that LOOK like 5b leaks; verify before treating them as such
- `dropped-messages/SKILL.md` → "Mandatory first action on ANY thread reply: session_search BEFORE exploring" — sibling rule for thread-context loading
- `dropped-messages/SKILL.md` → "Recovery workflow" — the actual re-threading recipe, applied only AFTER verifying the body really is fragmented
