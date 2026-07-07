---
name: dropped-messages
description: "Diagnose and recover dropped Jeffrey messages — threads or standalone messages that got no response within 30 min. Use when Jeffrey asks about missed messages, the script reports drops, or you need to understand why a message was unanswered. Includes the 3-article redrive-reply recipe (MCP mail bot identity, mcp-mail-ack-log entry, skill-gotcha patch) for replying to mcp_agent_mail's dropped-thread followups."
type: skill
---

# Dropped Messages — Diagnosis & Recovery

## Replying to a dropped-thread followup — the 3-article recipe (HARD PREFERENCE)

When `mcp_agent_mail` posts a `[Dropped-thread followup]` into a thread asking the agent to either complete the work or explain the blocker, the reply is a **redrive**. Three articles, in this order:

1. **Post in-thread via curl `chat.postMessage` AS MCP mail bot** (`U0A4G7LDJ4R`, bot_id `B0A3MS7G08P`), using `~/.mcp_mail/credentials.json` — **NOT** `HERMES_SLACK_BOT_TOKEN`, **NOT** the `send_message` helper. Verified 2026-06-19: Jeffrey said *"remember you can't send meesage as `<@U0AEZC7RX1Q>` because Hermes will not reply. Send as me or `<@U0A4G7LDJ4R>`"*. See `references/2026-06-21-redrive-reply-mcp-mail-bot.md` for the full recipe.
2. **Append an entry to `~/.hermes_prod/memory/mcp-mail-ack-log.md`** in the standard format (per the `mcp-mail-ack` COMMIT in SOUL.md).
3. **Patch any skill gotcha discovered** while doing the work — fold it into the relevant skill NOW so the next session starts already knowing.

**Anti-patterns (verified 2026-06-21, `C0AH3RY3DK6/1781845061.761899`):**

- ❌ **Burn 5+ messages reasoning out loud** about whether a post path exists before trying curl. Each narration turn is auto-mirrored into the thread by the gateway. The curl `chat.postMessage` with the MCP mail bot token works from any shell — just try it.
- ❌ **Post as Hermes** (`U0AEZC7RX1Q`) because it's the most familiar path. Violates the hard preference; the cron will keep escalating. **Verified 2026-06-24, `C0AH3RY3DK6/1781868481.071689`:** Hermes replied at 11:07 PT with full correct status + 4 next-step options AS `U0AEZC7RX1Q`, and the dropped-thread cron still fired the GAVE UP state — the cron expects the ack from MCP mail bot (`U0A4G7LDJ4R`) specifically to silence the loop, regardless of whether the content answers the question. Wrong identity = cron keeps re-firing even when content is correct.
- ❌ **Try to delete a wrong-identity post with the MCP mail bot's xoxb token.** Slack returns `cant_delete_message` permanently — only Jeffrey's `SLACK_MCP_XOXP_TOKEN` (xoxp user token) can delete messages authored by the Hermes bot. **Verified 2026-06-25, `C0AH3RY3DK6/1782231566.821589`:** wasted 2 tool calls trying to delete a wrong-identity Hermes reply with the MCP mail bot token before switching to xoxp. Use `SLACK_MCP_XOXP_TOKEN` for the delete, then repost the corrected ack AS MCP mail bot (xoxb) — see `references/2026-06-21-redrive-reply-mcp-mail-bot.md` § "Delete-token gotcha (verified 2026-06-25)".
- ❌ **Post the test ping to the user's real thread.** Probe with `auth.test` or post to a private debug channel first.
- ❌ **Skip the `mcp-mail-ack-log.md` entry.** The cron uses the log to detect double-acks; missing the entry means the next tick fires on the same thread again.
- ❌ **Every `terminal` call gets auto-mirrored into the thread** (verified 2026-06-25, `C0AH3RY3DK6/1782231566.821589`). When you post via curl from a terminal tool, the gateway mirrors the curl command itself as a separate Hermes message — and every subsequent terminal call (verification, more curl, even the delete-batch) ALSO mirrors, creating a cleanup loop. **One real reply + 8–10 narration mirrors is normal.** The fix: delete the narration mirrors with `chat.delete` using `$SLACK_MCP_XOXP_TOKEN` (Jeffrey's xoxp user token — Hermes bot's xoxb cannot delete its own mirrors: `cant_delete_message`). Recipe: `references/narration-mirror-cleanup-2026-06-25.md`. **Pro tip:** if you're about to post a redrive reply and then verify, expect 1 real + ~5 narration mirrors. Budget the cleanup.

**Tool-call budget:** 3 + investigation. If past 6 without the post in the thread, you're narrating, not working. **Special case:** if you've already posted the reply, mirror cleanup is normal and doesn't count toward the budget — budget separately and don't keep posting new terminal-mirrored commands.

For the daily escalation thread in `#all-$USER-ai` (different scenario, different identity), see `references/daily-escalation-thread-reply-2026-06-20.md` — that one posts as Hermes, not MCP mail bot.

## A dropped-thread followup can target a SIBLING message in the same thread — address each one separately

`mcp_agent_mail`'s dropped-thread cron fires per-message, not per-thread. A single Slack thread (`thread_ts` shared across messages) can have multiple sibling user messages, each independently eligible for a dropped-thread followup. Verified 2026-06-25, `C0AH3RY3DK6/1782032160.683689`:

- Sibling 1: `1782032160.683689` "Run /repro seems like planning block leaked future event" (campaign `ZlkhIbuvQwOyROOQPQAb`)
- Sibling 2: `1782033618.587949` "Read the latest responses from the LLM here it seems to be aware of the first horgus event so pretty sure you are wrong that it's due to compaction" (campaign `btF3Nu4mqQRTVLG6F7tu`)

Both siblings share `thread_ts = 1782032160.683689`. The dropped-thread cron fired twice, once per sibling.

**Anti-pattern:** Reply once, addressing only one sibling, and consider the thread "done." Result: the other sibling's dropped-thread followup keeps firing and the user has to escalate again.

**Required shape:**

1. When a dropped-thread followup arrives, **pull the FULL thread** (`mcp__slack__conversations_replies(channel_id, thread_ts, limit=30)`) and **enumerate sibling user messages**. Siblings have `ts != thread_ts`. The followup will quote ONE specific sibling's text, but other siblings in the same thread may also be pending.
2. **Address each sibling in its own reply** to the same `thread_ts`. Do not collapse them. Even if the two questions are related (e.g. two `/repro` URLs in the same thread), post one consolidated reply per sibling so the user can ack each independently.
3. **Use a different MCP mail ack-log entry per sibling** — each redrive produces one ack, not one per thread. Format: `[YYYY-MM-DD HH:MM] ACK redrive thread=<ts> sibling=<sibling_ts> channel=<chan> identity=mcp-mail-bot reason=<one line>`.
4. **Search prior memory for the other siblings.** A redrive often hits a thread where past work landed but wasn't acknowledged. Pulling `session_search` for keywords from each sibling (campaign IDs, character names) is cheaper than redoing the work. If the prior work is sound, the reply can be a brief restatement + ack-log entry pointing at where the prior work is recorded.

Verified 2026-06-25 incident: agent posted a single reply at `1782357565.807979` addressing only sibling 1. The MCP mail cron re-fired for sibling 2. Recovery reply `1782371916.715849` addressed sibling 2 in the same thread. Cost: 1 extra round-trip; lesson: enumerate siblings in step 1.

## Diagnosis gotcha: "compaction" is the wrong default when `core_memories` is the actual path

When a user says "the LLM is aware of [something] — pretty sure you're wrong that it's due to compaction," they are usually RIGHT and the prior agent was wrong. Compaction would mean a compressed summary artifact carrying the awareness across sessions. But the canonical mechanism for LLM awareness of past narrative in this stack is **`custom_campaign_state.core_memories[]`** in Firestore — a deterministic LLM-managed list sent in full every turn.

Verified 2026-06-25, campaign `btF3Nu4mqQRTVLG6F7tu`:

- `core_memories` = 246 entries, 34 mention Horgus/Hellrider
- First Horgus mention was introduced by the LLM at story-idx=31, 2026-06-15 19:55:30, then continuously reinforced through 134 of 875 story turns (15.3%)
- This is **canonical state persistence**, not compacted-prompt recall

**When evaluating a "compaction" hypothesis:**

1. Pull `custom_campaign_state.core_memories` from Firestore — count entries, count mentions of the entity in question.
2. If the entity appears in `core_memories[]`, the LLM's awareness is canonical-state-driven, not compaction-driven. Reject "compaction" as the diagnosis.
3. The two bugs that DO get framed as "compaction" are actually lifecycle-staleness bugs: stale background events surviving past `STALE_EVENT_TURN_THRESHOLD`, fixed by PRs #7766, #7774, #7790, #7800, #7822. If the user's claim is "the LLM knows about X," check that path FIRST before reaching for the compaction explanation.
4. If `core_memories` is empty or missing, THEN consider compaction as a candidate.

**Redrive-reply framing:** when this comes back as a dropped-thread followup, do not echo the prior "compaction" diagnosis. Acknowledge the misdiagnosis explicitly, show the `core_memories` count as proof, and offer 2-4 next steps (no compaction-based remediation).

## Reply shape (hard preference, 2026-06-25)

- **ALWAYS include the original Slack permalink** in redrive + daily-summary replies, not just `channel_id/thread_ts` numerically. Use `https://jleechanai.slack.com/archives/<chan>/p<ts_no_dot>` (drop the dot in ts). Jeffrey: "remember to always link the threads you redrive."
- **Per-thread reply shape:** thread link → 1-line classification → verdict pointer (PR links) → 2-4 next-step options → STOP.
- **Ad-hoc redrive lookback window = last 60 min** ("redrive dropped threads from the last hour"). Full-log sweep is the daily-escalation thread's job, not the ad-hoc redrive's. When redriving ad-hoc, grep `~/.hermes/logs/dropped-thread-followup.log` for events with timestamps inside the last hour, plus any in-flight `pending` followups not yet `gave_up`.

## When to invoke this skill

- Jeffrey asks "why didn't you respond to X?" or "did you miss my message?"
- The dropped-thread-followup script (`scripts/dropped-thread-followup.sh`) found drops (action items in `~/.hermes/logs/dropped-thread-followup.log` show `ESCALATED + GAVE UP` events)
- An MCP Agent Mail `[Dropped-thread followup]` message arrives in a Slack thread (the cron is asking the agent to re-do work that went cold)
- A `mcp_agent_mail` daily escalation thread arrives in `#all-$USER-ai` (different workflow — see `references/daily-escalation-thread-reply-2026-06-20.md`)
- **Jeffrey says "computer crashed" / "find dropped threads" / "redrive top N" / "use my identity"** (added 2026-06-22) — bulk batch redrive across all actionable threads in the lookback window. Use `references/top-10-redrive-ranking-2026-06-19.md` "Edge cases → Computer crash / bulk redrive" + audit-lock bypass pattern; reply shape per thread follows `references/2026-06-21-redrive-reply-mcp-mail-bot.md`. Identity: default MCP mail bot, OR Jeffrey's own (`xoxp` user token from `~/.bashrc` → `SLACK_MCP_XOXP_TOKEN`) if explicitly requested.
- **Jeffrey says "redrive dropped threads"** (added 2026-06-25) — ad-hoc redrive, lookback = last 60 min only. Scan log + in-flight pending. Reply per thread with permalink + classification + verdict + 2-4 next-step options. Do NOT do a full-log sweep.

## Diagnosis flow (high level)

1. **Read the log:** `grep "ESCALATED + GAVE UP" ~/.hermes/logs/dropped-thread-followup.log | grep "$(date +%Y-%m-%d)"` — find today's escalated threads.
2. **Pull thread context:** `mcp__slack__conversations_replies(channel_id=<chan>, thread_ts=<ts>, limit=30)` for each escalated thread.
3. **Classify:** false-positive (work landed) vs genuine (work incomplete). The classification table is in `references/daily-escalation-thread-reply-2026-06-20.md` (it generalizes to any escalation).
4. **Reply with the 3-article recipe** above for redrive scenarios, OR the daily-summary format from `references/daily-escalation-thread-reply-2026-06-20.md` for daily escalations.
5. **Log the ack** in `~/.hermes_prod/memory/mcp-mail-ack-log.md` per the `mcp-mail-ack` COMMIT in SOUL.md.

## Operator contract (harness clarity)

- **Not config drift:** Changes to this script's heuristics live in **`scripts/dropped-thread-followup.sh`** (git-tracked, in `~/.hermes/`). They do **not** rewrite **`hermes.json`**, **`~/.cursor/mcp.json`**, or Slack tokens unless an operator edits those files.
- **Overrides:** Prefix the script with env vars (`DROP_LOOKBACK_HOURS`, `DROP_THREAD_REPLY_LIMIT`, `DROP_EXCLUDE_CHANNELS`, `DROP_JEFFREY_ONLY_CHANNELS`, …). LaunchAgent / plist can set them for stable "my settings."
- **Audit trail:** `git log -p -- scripts/dropped-thread-followup.sh` (in `~/.hermes/`) is the source of truth for why default behavior changed.
- **Staging-vs-prod discipline:** Edit `~/.hermes/scripts/dropped-thread-followup.sh` (staging, git-tracked) → verify with `bash -n` + `DRY_RUN=1 bash <script>` → `cp` to `~/.hermes_prod/scripts/dropped-thread-followup.sh` to catch up prod. Launchd runs staging, so the cron picks up the fix on the next tick. See `references/cron-staging-prod-drift-2026-06-17.md` for the full pattern.

## References

| Reference | When to read |
|---|---|
| `references/2026-06-21-redrive-reply-mcp-mail-bot.md` | **READ FIRST** — the 3-article recipe for replying to a dropped-thread followup. Identity (MCP mail bot, not Hermes), token resolution, curl recipe, ack-log entry, anti-patterns. |
| `references/completed-with-pending-followup-offers-2026-06-22.md` | New false-positive class (2026-06-22): agent posts answer + "Want me to (a)/(b)/(c)?" drilldown offers, cron flags as dropped. Triage checklist + 4 durable fix candidates. |
| `references/redrive-post-as-mcp-mail-bot-2026-06-19.md` | Parent reference for the hard user preference: redrive replies MUST post as `U0A4G7LDJ4R`, NOT `U0AEZC7RX1Q`. |
| `references/daily-escalation-thread-reply-2026-06-20.md` | **OPPOSITE IDENTITY** case: the daily escalation thread in `#all-$USER-ai` posts as Hermes, not MCP mail bot. Includes the reply shape (one consolidated message, classified list, 4 proposed durable fixes). |
| `references/sylphina-recovery-2026-06-11.md` | Canonical "what NOT to do" example: 37-message polluted thread from 19 narration messages + cleanup pitfalls. 4-call disciplined shape that should have been used. |
| `references/2026-06-13-dropped-thread-recovery.md` | (in `slack-messaging/`) The Sylphina-style worked example showing the gateway auto-mirror of `terminal` tool output. |
| `references/top-10-redrive-ranking-2026-06-19.md` | "Top-N actionable" redrive ranking format — when the user explicitly asks for a prioritized list of stuck threads. |
| `references/session-2026-06-20-auto-resolve-stale-pending.md` | Pattern for auto-resolving stale `pending` followups when the underlying work has clearly landed. |
| `references/5b-leak-framing-false-alarm-2026-06-19.md` | The 5b-leak detector false-positive case (`:rotating_light:` reaction on `reaction.escalated` text) — classified as expected delivery, not misroute. |
| `references/iter-budget-exhausted-2026-06-15.md` | When a dropped thread hits the iteration budget before resolution — recovery options. |
| `references/stale-mkdir-lock-bypass-2026-06-19.md` | Stale `/tmp/mkdir` lock detection in the dropped-thread-followup script. |
| `references/investigate-how-did-this-happen-2026-06-18.md` | Post-mortem pattern: when a drop is genuinely unexpected, dig into the cron logs to find the heuristic that misfired. |
| `references/cron-staging-prod-drift-2026-06-17.md` | The staging-vs-prod drift pattern: edit `~/.hermes/`, `cp` to `~/.hermes_prod/`, verify with `DRY_RUN=1`. |
| `references/cron-gave-up-state-mismatch-2026-06-17.md` | The `was_nudged_recently` short-circuit on `gave_up=true` (legacy string vs `{last, count, gave_up}` object mismatch). |
| `references/circuit-breaker-design.md` | The circuit-breaker pattern for the dropped-thread-followup cron — when to stop nudging a thread. |
| `references/no-new-content-hallucination-2026-06-23.md` | **NEW CLASS** — agent fabricates "your message contains no new content" framing for an unread user message after a gateway interrupt. Pairs with SOUL.md `## COMMIT: never-hallucinate-no-new-content` (model-level rule) and pr-bring-to-green-inline-cookbook P4 (operational recipe). |
| `references/cron-fabrication-detection-2026-06-25.md` | **NEW** — cron-side fabrication-detection patch landed in `scripts/dropped-thread-followup.sh`. Detects "no new content" framing within 10 min, re-nudges immediately (bypassing 30-min quiet window), capped at 2 nudges per (channel, thread) per 24h. Closes the false-positive loop at the cron level (third of three durable fixes). |
| `references/canonical-state-vs-compaction-2026-06-25.md` | **NEW** — when the user pushes back on a "compaction" diagnosis, this is almost always wrong: the canonical mechanism is `core_memories[]` in Firestore. Includes the inline Firestore probe recipe + redrive-reply shape. Pairs with `repro` skill's workflow-preferences.md 2026-06-25 entry. |
| `references/bot-read-tracking-scope-gap-2026-06-23.md` | **NEW** — `chat:write` does NOT clear the unread badge; need `channels:write` + `conversations.mark` after every post. Root cause of the 6-entry "9+" unread on `#worldai`/`#all-$USER-ai`. Class-level pattern for any post-and-tracker agent. |
| `references/narration-mirror-cleanup-2026-06-25.md` | **NEW** — bulk-delete recipe for the 5–10 narration mirrors that auto-appear when you post via `terminal`-executed curl. Pairs with the prior-agent wrong-verification lesson (the prior agent at `ts=1782385813.392319` hallucinated "0 matches" when the script had 49). Use `$SLACK_MCP_XOXP_TOKEN` (xoxp), not Hermes xoxb. Verified 2026-06-25. |
| `references/cross-channel-post-unreachable-workspace-2026-06-25.md` | **NEW** — when the dropped-thread's workspace is unreachable from this runtime (`Cross-channel Slack misroute prevented` + `no_service` webhook), the 3-article redrive recipe in `2026-06-21-redrive-reply-mcp-mail-bot.md` cannot be applied. 3-step recovery: do the work in this session, append ack-log entry with `identity=mcp-mail-bot-unreachable`, reply inline to the followup with the full deliverable. Verified 2026-06-25 on `C09GRLXF9GR/1782196882.961889`. |
| `references/cron-sibling-channel-verdict-heuristic-2026-06-25.md` | **NEW** — cron-design lesson: when an agent verdict lands in a SIBLING channel (not the originating thread) because `send_message` is misroute-blocked, the cron's `was_nudged_recently` + `gave_up` heuristics see nothing in the originating thread and keep escalating. Proposes a `verdict_delivered_to_sibling_chat` heuristic that searches for the same `thread_ts` in any channel the agent has access to within a configurable lookback. Pair with `cross-channel-post-unreachable-workspace-2026-06-25.md` (runtime-side recovery) and `narration-mirror-cleanup-2026-06-25.md` (post-path cleanup). Verified 2026-06-25 on `C0AH3RY3DK6/1782032160.683689` daily-escalation audit. |

## Cross-reference

- `slack-messaging` — the post primitive; this skill composes with `slack-messaging`'s curl recipes and the "no `send_message` for threaded replies" rule.
- `slack-thread-routing-investigation` — the 5 known failure modes (gateway self-thread, runtime tool-surface gap, etc.); Failure 4 (narration-leak) is what the 5+ noise messages in this skill's anti-patterns describe.
- `slack-misroute-detector` — the 5b-leak false-positive detection (when a `:rotating_light:` reaction triggers the safety net on its own delivery).
- `wa-user-activity-report` — when a dropped-thread followup is about your-project.com user activity, this skill returns the per-campaign breakdown (and the `wa-user-activity-report` SKILL.md encodes the timestamp-vs-created_at schema).
