# 2026-06-13 — "We thought we fixed this?" — 11th instance + first user signal that the workaround is insufficient

## What happened

A prior session posted a deep review of a private architecture-review doc to Slack via the gateway `send_message` path. The 3-part `target=slack:C0BA4MCBPFB:1781384270.728329` form silently stripped the `:thread_ts` segment and the post landed in the home channel `C0AJQ5M0A0Y` as a **self-rooted top-level orphan** (TS `1781384270.728329`, `ThreadTs == MsgID`).

User reply: **"We shouldn't be replying here I thought we fixed the issue?"**

## Why this instance is different from the prior 10

Every prior mis-route (instances 1-10) was either:
- caught in-tooling (the bot's own runtime noticed the broken thread_ts),
- caught by the user as "you posted in the wrong place" (factual complaint, no expectation of a prior fix),
- or caught by a dropped-thread re-nudge from the watchdog.

This is the **first instance where the user explicitly invokes the prior fix as an expectation of resolution**: "I thought we fixed this?" That phrasing changes the response shape. A pure Path A/B recovery + apology is no longer sufficient — the user is telling us the workaround has stopped feeling like a fix. The next action is **file the durable gateway patch**, not add another workaround.

## Recovery (in-turn)

1. Loaded this skill (`slack-thread-routing-investigation`).
2. Called `mcp__slack__conversations_replies` on the parent thread `1781384270.728329` to confirm the mis-route (`ThreadTs == MsgID` self-rooted).
3. Checked env for `HERMES_SLACK_BOT_TOKEN` — **not present in runtime env**, must source from `~/.bashrc`:
   ```bash
   bash -c 'source ~/.bashrc && echo "$HERMES_SLACK_BOT_TOKEN"'
   ```
   Length=58, starts with `xoxb`. (This is the canonical token-source recipe — the runtime sandbox does not inherit shell rc files.)
4. Composed the entire 1.5 KB reply in a heredoc-written JSON file at `/tmp/slack-reply.json` (one post, no probing).
5. Single `curl` call:
   ```bash
   curl -sS -X POST https://slack.com/api/chat.postMessage \
     -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
     -H "Content-Type: application/json; charset=utf-8" \
     --data-binary @/tmp/slack-reply.json
   ```
   Response: `{"ok":true,"channel":"C0AJQ5M0A0Y","ts":"1781384946.008329"}`.
6. Verified via `mcp__slack__conversations_replies channel=C0AJQ5M0A0Y thread_ts=1781384270.728329` — new TS `1781384946.008329` has `ThreadTs=1781384270.728329` (correctly threaded). 3 narration siblings leaked (TS `1781384926/934/945`) before the final reply; gray-zone per the "1-2 acceptable, 5+ post cleanup" rule.

## Durable prevention (filed in same turn)

Per the user's follow-up "Make a bead and gh issue for slack misroute":

* **Bead** `$USER-88x` in a private project's `.beads` — `br create` with type=bug, priority=P2, labels=[gateway, slack, routing, slack-thread-routing-investigation].
* **GH issue** https://github.com/jleechanorg/agent-orchestrator-ts/issues/684 — filed against `jleechanorg/agent-orchestrator-ts` (the gateway that owns the broken `send_message` path), labels=[bug, P2, fragility-fix].
* **Cross-linked**: `br comments add $USER-88x <issue URL>`.
* **Issue body** asks for 4 things: (1) honor `target=slack:CHAN:thread_ts` by forwarding `thread_ts` to `chat.postMessage`; (2) fail loud on partial honors, no silent fallback to home; (3) regression test asserting `outgoing.ts.thread_ts == incoming thread_ts`; (4) same test for the 2-part form (currently non-deterministic).

## Two micro-lessons embedded

### `gh issue create --label` does NOT validate label existence — and the gateway repo does NOT have `gateway` or `slack` labels

`gh issue create --label gateway` failed with `could not add label: 'gateway' not found`. The `jleechanorg/agent-orchestrator-ts` repo only has: `bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`, `P0`, `P1`, `P2`, `trigger-ci`, `fragility-fix`. **Always `gh label list --repo <owner/repo> --limit 100 --json name` before `--label` in `gh issue create`** — not just for this repo, but for any repo you don't own. The retry used `[bug, P2, fragility-fix]` and succeeded.

### The `br comments add` argument syntax is positional, not `--body`

`br comments add <id> --body "..."` failed with `error: unexpected argument '--body' found`. The correct form is positional: `br comments add <id> "comment text"`. (Confirmed via `br comments --help` which lists `add` as a subcommand without explicit arg flags.)

## The lesson that should outlive this instance

**When a user says "I thought we fixed this?" / "isn't this patched?" / "we should not be doing this anymore," the response is not another workaround — it is a bead + GH issue for the underlying bug.**

The SOUL rule `slack-reply-inherit-thread-ts` (2026-06-09) was the right shape of fix **at the time**: it patched agent-side thread inheritance. But it was a workaround, and workarounds stop feeling like fixes the moment the user notices the bug recurring. The next time this comes up, the response should be: (a) confirm the prior SOUL rule is still loaded, (b) recover via Path B as usual, (c) **file a gateway-side bead+issue** (or check if `$USER-88x` is still open and re-ping it). The gateway patch in `jleechanorg/agent-orchestrator-ts` issue #684 is the durable fix; until it lands, this skill is the workaround of record.

## Timeline (TS values, in order)

- `1781384270.728329` — broken gateway post (deep review, self-rooted orphan in `C0AJQ5M0A0Y`)
- `1781384779.339679` — user reply: "We shouldn't be replying here I thought we fixed the issue?"
- `1781384926.772999` — agent narration leak: "You're right to flag this. Let me check…"
- `1781384934.615719` — agent narration leak: "Token not in env…"
- `1781384945.654499` — agent narration leak: "Token is in ~/.bashrc. Source it and post."
- `1781384946.008329` — final Path B recovery post, `ok:true`, `ThreadTs=1781384270.728329` ✅
- `1781384953.407009` — agent narration: "Posted at ts 1781384946.008329…"
- `1781386037.067769` — second Path B post in same thread confirming bead+issue were filed
- bead `$USER-88x` + issue https://github.com/jleechanorg/agent-orchestrator-ts/issues/684 filed
