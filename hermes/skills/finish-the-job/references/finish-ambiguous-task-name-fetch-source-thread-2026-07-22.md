---
name: finish-the-job
version: 1.7.2 (addendum)
last_verified: 2026-07-22
trigger: short user-given task label (e.g. `add-gemini-flash-models-to-settings`) where the actual instruction lives in a Slack thread the user referenced by shorthand (`rt=100`, `the bug thread`, etc.)
---

# Resolve ambiguous task labels by fetching the source Slack thread BEFORE classifying

## When this fires

User says something like:

> "Run `/finish add-gemini-flash-models-to-settings` for the `rt=100` thread (#worldai)."

The task name (`add-gemini-flash-models-to-settings`) is **clear about WHAT** but **ambiguous about WHICH** model(s), WHAT scope, WHAT URL/references. The `rt=100` shorthand is an internal thread-id convention that does not appear in `conversations.history` or `br search`. The actual verbatim instruction + URLs + scope lives in the referenced Slack thread.

The wrong path is to classify the task using only the short label and spawn a worker on a guessed scope. The right path is to fetch the source thread first.

## Concrete recipe (verified 2026-07-22, Slack `C0AH3RY3DK6` `rt=100` / `ts=1784653940.616829`)

1. Parse the channel + thread_ts from the user message. `rt=100` is the user's shorthand for a real thread_ts (`1784653940.616829` in the verified case). The verbatim instruction always lives in the **root** message of that thread, not in replies.
2. Fetch the thread history via Path B curl (mcp__slack__* tools are not always surfaced in dispatch-mode gateways):
   ```bash
   curl -fsS -H "Authorization: Bearer ${HERMES_SLACK_BOT_TOKEN}" \
     "https://slack.com/api/conversations.replies?channel=<chan>&ts=<thread_ts>&limit=20" \
     -o /tmp/thread.json
   python3 -c "import json; d=json.load(open('/tmp/thread.json')); [print(m['ts'], m.get('text','')[:500]) for m in d.get('messages',[])]"
   ```
3. Read the **first** human user message (not bot, not hermes self-message). That is the canonical instruction.
4. Pull the verbatim text + any URLs + any "iterate and test" / "show proof" / "use /browser" sub-instructions. These become required fields in the spawn brief.
5. THEN classify per Phase 0 and dispatch.

## Why this avoids a clarification question

Without this recipe, Phase 0's "ONE clarifying question" carve-out fires because `add-gemini-flash-models-to-settings` doesn't specify *which* Gemini Flash models, *what* scope (just dropdown? dropdown + backend + tests?), *what* proof (unit test? browser video? BQ telemetry?). Each of those could be a separate question → violates `no-pick-one-menus` + `no-confirmation-gate`. Fetching the source thread resolves all of them in one read.

## Pitfall — `thread_not_found` on the first attempt

The first `conversations.replies` attempt can return `{"ok":false,"error":"thread_not_found"}` even when the thread exists, because:
- The bot may not be a member of the channel yet (`not_in_channel` is a separate error; `thread_not_found` can mean the ts was malformed)
- The thread_ts may need re-formatting — Slack timestamps are `seconds.microseconds` and the user shorthand may drop the dot
- The bot identity in `HERMES_SLACK_BOT_TOKEN` may belong to a different workspace than the target channel

If `thread_not_found`:
```bash
# First, verify the channel is in the bot's workspace:
curl -fsS -H "Authorization: Bearer ${HERMES_SLACK_BOT_TOKEN}" \
  "https://slack.com/api/conversations.info?channel=<chan>" | python3 -m json.tool | head -20

# Second, fall back to channel history and scan for the parent message by date range:
curl -fsS -H "Authorization: Bearer ${HERMES_SLACK_BOT_TOKEN}" \
  "https://slack.com/api/conversations.history?channel=<chan>&limit=20" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('\n'.join(f\"{m['ts']} {m.get('user','?')}: {m.get('text','')[:200]}\" for m in d['messages']))"
```

Then identify the parent by user id (`U09GH5BR3QU` is Jeffrey in the verified workspace) and content match.

## Pitfall — bot identity mismatch (`MCP Agent Mail` vs hermes canonical)

When posting the spawn ack to the source thread, the `bot_id` returned in the response may be `B0A3MS7G08P` (`MCP Agent Mail`) rather than the canonical hermes bot. This is because `HERMES_SLACK_BOT_TOKEN` env var can resolve to either identity depending on `~/.bashrc` ordering vs `.profile`. NOT a blocker for functionality (the post lands in the right thread) but if the user expects "Hermes" to be the visible author, swap the token at the source (`grep -n 'HERMES_SLACK_BOT_TOKEN' ~/.bashrc ~/.profile` — see memory `bashrc-profile-xapp-drift-blocks-launchd`). Do NOT silently leave the wrong identity if the user explicitly asked for canonical hermes.

## Why this is an addendum, not a phase addition

Phase 0.5 already covers the disambiguation principle (one clarifying question). This file is the **recipe** for "fetch the source thread" — the concrete path that answers the question without asking the user. Future agents that load `finish-the-job` for an ambiguous-label task should load this reference BEFORE classifying.

## Cross-references

- `references/wrong-target-removal-stop-X-from-Y-2026-07-20.md` — Phase 0.5 disambiguation principle
- `~/.hermes/skills/agento/SKILL.md` v1.5.0 — companion pre-spawn harness authStatus check (`references/spawn-harness-preflight-2026-07-22.md`)
- `~/.hermes/workspace/SOUL.md` — `## COMMIT: slack-reply-inherit-thread-ts` (where to post the spawn ack)
- `~/.hermes/workspace/SOUL.md` — `## COMMIT: prefer-builtin-slack-mcp` (when MCP tools ARE available, prefer them over Path B)
