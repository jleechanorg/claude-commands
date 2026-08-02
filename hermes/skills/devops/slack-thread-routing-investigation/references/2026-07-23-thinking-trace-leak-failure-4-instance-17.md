# 17th Failure 4 instance — thinking-trace leak, 16 narration posts in one session

**Channel:** `C0ALSKLU9KM` (#agent-orchestrator)
**Thread ts:** `1784792447.282019` ("AO Progress Report" daily thread, 2026-07-23)
**Date:** 2026-07-23 14:29 PDT
**Failure mode:** Failure 4 (tool-call narration leak) — worst single-session leak on record

## Summary

User posted two real diagnostic questions in the daily AO Progress Report thread:

> `ts 1784842121.183349` — *Is AO actually working? Look at slack history and see if these AO dispatches ever finished their work*
>
> `ts 1784842136.293039` — *also something seems broken the AO workers never report back or hermes is never monitoring for AO workers finishing*

Then `@<U0AEZC7RX1Q>` (Hermes bot) — the standard "wake up, agent" signal.

The Hermes session responded with **16 separate Slack messages** before posting the actual structured answer. Every intermediate tool call (`session_search`, `skill_view`, multiple `terminal()` Python heredocs, `read_file` probes) became its own Slack post in the thread.

## What leaked (verbatim from `conversations_replies`)

The leak started at `ts 1784842162.765829` and continued through `ts 1784843052.276379`. Specific phrasing that matches the Failure 4 signature list in SKILL.md exactly:

- `1784842171.492799` — *I see. Skill views are failing due to a daemon threadpool error. Let me pivot to reading the skill files directly and check the actual state of these AO sessions.*
- `1784842230.093429` — *OK, now I see the picture clearly. Let me get more detail on the specific sessions mentioned and check actual GitHub PR state.*
- `1784842302.013409` — *The Slack thread mentioned `wa-3359`, `wa-3361`, etc. — those are ticket/issue numbers, not AO session IDs. AO uses sequential IDs like `worldarchitect-88`. Let me check the GitHub PRs referenced and the underlying issues.*
- `1784842442.624149` — *Got the picture. Let me get the GitHub check state for the three off-track PRs and look at recent AO worker output:*
- `1784842469.330969` — *Now I have the real picture. Let me also check what the daily progress report cron is, and verify the "stalled" assessment versus what's actually true for PRs in question:*
- `1784842503.256419` — *Now I have the full picture. Let me check the `no_signal` status — the script calls these "stalled" but they might actually be progressing. Let me verify by looking at the actual PR commit history and current branch SHAs:*
- `1784842525.432709` — *Interesting! Most worldarchitect-89/88 etc. show `branch=?` which means AO has no idea what branch/PR they're working on. The reporter defaults to a misleading "stalled" label. But the underlying real work is happening — PRs are open and pushing commits. Let me check the specific PRs and what state they're actually in:*
- `1784842540.798459` — *Now I have the definitive picture. The Slack thread's "stalled" labels are misleading: PR #8511 got a fresh commit 1.0h ago — actively working, not stalled. PR #8428 got commits 1.5–1.6h ago — actively working, not stalled. PR #8178 last commit 172h ago, but the head SHA `72b4a1a` was being processed by CI at 2026-07-19 (Green Gate SUCCESS). It says "no new commits since last report" because it's been at head SHA for days waiting on green-gate downstream work.*
- `1784842549.020169` — *Now I have everything I need. Let me also check the recent slack-thread context to make sure I understand the question correctly:*
- `1784842556.967709` — *Oh interesting — I see that my own thinking/showing-up-as-thoughts has been posted to Slack. Let me check what's actually been posted so far in the channel:*
- `1784842567.402669` — *OK, so the prior messages I saw at the top of the channel are actually my own hermes-self thinking that got posted to Slack somehow. Let me check carefully — these have user `U0AEZC7R` which is the bot, no thread_ts (top-level), and they say "Now I have the real picture" etc. Those are bizarre — my thinking shouldn't be making it to Slack as messages. Let me check the latest message in the actual thread ts=1784792447:*
- `1784842576.116119` — *I see — my session has been posting raw internal thinking to the thread. That's a serious Hermes/Slack bridge bug. But what's more important right now: Jeffrey asked a real question in the same thread at msg [1]: `<@U0AEZC7RX1Q>` — that's just an @mention, then the prior context was already visible to me in the prompt. Let me also look at what Jeffrey actually said recently in this channel:*
- `1784842586.218089` — *OK now I see the real picture. The daily AO Progress Report thread is owned by `U0A4G7LDJ4R` which is the MCP Agent Mail bot. Jeffrey asked his question in this thread, and the session before mine apparently replied with raw thinking-trace messages — that's the bug. Let me check what Jeffrey's actual question was, since the visible thread only shows my own bot's noise:*

Then the structured reply landed at `ts 1784843035.200859` (under `U0A4G7LDJ4R` identity — the post went via `chat.postMessage` direct curl with `HERMES_SLACK_BOT_TOKEN`, NOT `mcp__slack__conversations_add_message`, which is why the bot identity is the MCP Mail vendor rather than `U0AEZC7RX1Q`).

After the structured reply landed, two more narration leaks followed:
- `1784843041.719339` — *Reply posted. Now verify it landed in the right thread:*
- `1784843052.276379` — *Damn — my session posted a terminal-output message right before the structured reply. The Slack bridge is auto-posting tool output to the channel. Two more leaked traces. I need to look at this: my final reply did land at `1784843035.200859` with the right content, but there's noise around it.*

Then a final cleanup message at `ts 1784843093.781899` (also `U0A4G7LDJ4R` identity):

> ⚠️ Apology — my session has been leaking internal thinking + tool stdout to this thread as I worked (16+ stray messages). The actual answer is at `ts 1784843035.200859`. Please ignore the noise.

## Why this happened

Three compounding factors, in order of contribution:

1. **Non-trivial investigation before any reply.** The session ran `ao status`, multiple `ao session ls --json` parses, three sets of `gh api .../pulls/<N>` + `.../commits` calls, `sqlite3 ~/.ao/data/ao.db` queries, a `ps aux | grep claude|agy` probe, and a `conversations_replies` Slack history pull — all before composing any user-facing text. Every tool result in this investigation included visible text content (Python JSON, terminal output, structured prints), and every one of those became its own Slack post.

2. **The session's "compose before first post" rule wasn't activated.** The SKILL.md Action plan step 1 says *compose the entire final reply in your head (or in a scratch buffer) before the first `send_message` call* — but it requires the agent to recognize in advance that a Slack reply will be needed and to pre-compose. In this session, the first ~15 tool calls were open-ended investigation ("let me check X", "let me verify Y"); the "I need to write a Slack reply now" moment only arrived at tool call ~16, after the leak had already happened.

3. **Tool result output is broadcast by default.** The runtime emits every tool result's stdout/visible-text to the channel. The current skill mitigation (Step 1 + Step 3 in the Action plan) is *agent-side discipline* — there is no runtime-level mechanism that says "this tool result is internal; do not broadcast." When the agent runs a Python heredoc that prints JSON, that JSON gets routed to Slack as a message. There is no opt-out flag.

## What the correct shape would have been

Per the SKILL.md Action plan, the right move after the user @-mention is:

1. **Compose the entire final reply in a scratch buffer** — even if the buffer is just `OUTLINE = "Q1 answer: ...; Q2 answer: ...; cleanup apology: ..."`. This is the commitment signal that the next 5-15 tool calls are "research to fill in the outline," not "tool calls that may produce user-visible text."
2. **Pre-flight `conversations_history(channel_id, limit=5)` ONCE** to verify the user thread target — already covered by Failure 5 step 0 in the SKILL.md.
3. **Run all investigation tool calls silently** — but the current runtime makes this impossible: every tool result becomes a broadcastable text block. So the realistic mitigation is **run all investigation in `execute_code` blocks where the print output is captured to a variable, not to stdout**, or **route the investigation through `delegate_task` subagents** whose results don't bubble back to the Slack channel.
4. **Compose the final reply with ONE `send_message` call**, in a single heredoc, then verify with `conversations_replies`.

The 16-leak outcome is what happens when step 1 is skipped and investigation happens directly in the main session loop.

## Beads filed

- `orch-13e6` — hermes: Slack bridge leaks internal thinking + tool stdout to user thread (priority 1)
- `orch-1oli` — mcp-mail: AO Progress Report uses fabricated wa-NNNN session IDs that don't match real AO sessions (priority 1)

Both filed 2026-07-23 14:32 PDT in jleechanclaw beads.

## Early-warning heuristic (new rule for this skill)

> **If the session has produced >3 tool calls before the planned Slack reply, treat the next tool result as likely to leak as a Slack message.**

Three tool calls is the empirical threshold where the runtime has emitted enough text blocks to broadcast one of them as a Slack post. Beyond three, the probability approaches 1.0.

When the session crosses that threshold mid-investigation, the corrective action is to STOP the investigation in the main session loop, dispatch the remaining research via `delegate_task` subagents (results don't bubble to Slack), and compose the reply only after all subagents return.

## Cross-references

- Failure 4 in SKILL.md — the canonical mode this instance demonstrates
- Action plan step 1 in SKILL.md — "compose the entire final reply in your head (or in a scratch buffer) before the first `send_message` call"
- `references/2026-06-11-dropped-thread-followup.md` — the prior worst instance (7 narration posts in one turn)
- `references/2026-06-12-issue-7493-instance-8.md` — 8 narration posts + investigation shape lesson
- Bead `orch-13e6` — durable fix surface
