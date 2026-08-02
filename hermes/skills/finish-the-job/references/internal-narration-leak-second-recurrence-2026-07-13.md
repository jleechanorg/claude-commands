# Internal narration leaks — second recurrence (2026-07-13)

## The bug

`finish-the-job` v1.11.0 sharpened the "Internal narration leaks" anti-pattern with: "compose ENTIRE final reply in ONE `think` block, then issue EXACTLY ONE `conversations_add_message` call". Verified on PR #7953 evidence drive.

It did NOT survive a different shape of the same bug: a `delegate_task` worker that posts its own single consolidated "Done" reply, then the **gateway session** continues to verify with terminal calls + a *second* consolidated reply. The gateway's verification polls (mcp__slack__conversations_history, mcp__slack__conversations_replies) echo as bot text via the Slack channel-bridge, and any narration `think`-block prose that mentions the tools also gets posted.

## Verified incident (merge_train PR #43, 2026-07-13)

Thread `C09GRLXF9GR/p1783983750.302659` ended up with this bot-text sequence:

1. `Worktree clean, patch applies. Now spawn the AO worker with the full context.` ← gateway think-block narration, posted as bot message
2. `:twisted_rightwards_arrows: delegate_task: Apply the supplied patch to /Users/jl...` ← tool-call name echo from the channel-bridge
3. `:white_check_mark: Done: PR 43 opened, awaiting CI pytest matrix...` ← the **worker's** single consolidated Done post (this one is real)
4. `Worker completed end-state B PR open, awaiting CI. Let me verify the live PR state from the gateway session to confirm the workers claim, then post the consolidated Slack reply.` ← **another** gateway think-block narration
5. `:computer: terminal\nexport GH_TOKEN=GH_TOKEN_AGENTF g...` ← gateway's verification poll, echoed
6. `📊 Live CI update (ignore the chatter above — that was internal narration):...` ← **another** "Done" reply from the gateway, telling the user to ignore 5 above it

Six bot messages where one was meant. The user's real signal was buried under 5 lines of chatter.

## What v1.11.0 missed

The v1.11.0 wording was framed as a gateway-only discipline: "issue ONE conversations_add_message only; for verification polls use terminal/read_file (NOT mcp__slack__conversations_history or conversations_replies which both echo as bot text)". But:

- It didn't say **the worker must also post exactly once** — workers can drift into multiple Slack posts too, and the worker post is the first bot message the user sees.
- It didn't account for the gateway's **own think-block prose** between tool calls getting echoed as bot text — every "let me confirm..." / "now spawning..." / "worker reports X" line posted BEFORE the actual Done reply is noise.
- It didn't say the **Done message MUST be the absolute last bot message in the thread** before the user reads it. If anything echoes after the Done, it pollutes the anchor.

## The 4-step recipe (v1.15.0)

1. **Worker must post exactly one Slack reply, in its own think block, with no follow-up tool calls that echo.** Compose the entire Done text first, then issue ONE `conversations_add_message`. Do not call `conversations_history` / `conversations_replies` for verification — use `terminal` + `gh api` / `curl` instead. If chatter has already started in the worker, post ONE short "ignore the chatter above — real deliverable is X" note and STOP.

2. **Gateway does NOT poll `mcp__slack__conversations_history` / `conversations_replies` after worker completion.** Both calls echo as bot text in the thread. Use `terminal` + `gh pr view N --json ...` / `curl -H "Authorization: Bearer ***" https://api.github.com/repos/OWNER/REPO/pulls/N` for verification. The Slack replies poll is ONLY for confirming the worker's post landed in the right thread (one call, BEFORE the Done reply is composed, not after).

3. **The gateway's own think-block narration between tool calls gets posted as bot text by the channel-bridge.** Avoid: "let me confirm...", "worker reports...", "now spawning...", "Live CI update..." preamble text. Phrase every narration as either (a) part of the final Done reply compose, or (b) pure internal thinking that never mentions tool calls by name.

4. **The "Done" message MUST be the absolute last bot message in the thread.** If any tool call (including verification polls) might echo AFTER the Done, do not post the Done yet. The Done anchor is the line the user scrolls to — anything after it is noise that defeats the Slack reply format (`✅ Done / Proof / Judgment calls / Memories`).

## Anti-pattern audit checklist (run before posting the final Slack reply)

```
[ ] Last bot message in thread is mine, not a tool-call echo?
[ ] No "Worktree clean..." / "Let me confirm..." / "Worker reports..." preamble lines between tool calls?
[ ] mcp__slack__conversations_history / replies NOT called after worker completion?
[ ] Done reply is ONE message with the ✅ Done / Proof / Judgment calls / Memories shape?
[ ] No follow-up apology message after Done (chat.update the original instead)?
```

If any answer is NO, patch the reply before posting. If chatter already happened, post ONE short corrective line + STOP — do not continue verification polls.

## Why this keeps recurring

The Slack gateway channel-bridge is the same surface that powers `mcp__slack__*` — so every `think`-block sentence that mentions a tool by name gets posted alongside the tool result. The agent doesn't see the noise (it's a side-channel artifact), but the user does. The discipline has to be enforced at compose time, not at execute time — by the time the LLM is choosing between two replies, the chatter is already in the thread.

The bug also recurs because `delegate_task` workers have their own Slack compose discipline. If the gateway author of v1.11.0 was the worker author of v1.15.0, both sides of the handoff must follow the same rule. **The fix is one shared rule applied at every Slack-compose moment**, not gateway-side policing of worker behavior.
