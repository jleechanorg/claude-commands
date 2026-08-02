# cmux Output Contract — Mandatory Typed + Response Disclosure

**Added 2026-07-28 by Jeffrey Lee-Chan in Slack thread 1785250971.654869:**
> "they must always explicitly say to the caller what was typed and what the cmux
> terminal response was. Treat it as not working until we see a response."

**Source rule:** Every cmux skill that performs a `cmux send` (or any analogous
steering action via the cmux socket/CLI) MUST include, in its reply / report /
echo-back to the operator (Slack thread, terminal reply, PR comment, or whichever
channel triggered the steer):

1. **The exact text that was typed** — verbatim copy of the string passed to
   `cmux send --workspace ... --surface ... "<text>"`, including any escape
   characters. If the brief was written to a worktree file (the worktree-pointer
   strategy), the reply must cite that file path + brief size + a 1-line summary
   of what was in it.
2. **The cmux terminal response** — verbatim transcript of what
   `cmux capture-pane` / `cmux read-screen` returned AFTER the
   `cmux send-key enter` settle window (typically 5-15s). Specifically, the
   agent's first action after absorption: the brief-reading line, the first
   `Bash(...)` call, or the first user-tool cycle.
3. **Submission status** — explicit verdict: "submitted (churning label X)",
   "not submitted (text still at ❯ prompt)", or "blocked (no churn, retried N
   times)". Use the churning-label vocabulary from `cmux` parent skill's
   "Submit Discipline" section.

**"Treat as not working until we see a response" rule:** If the reply does not
include the typed text AND a terminal response, the steer is considered
**failed** and the operator SHOULD treat the cmux action as not having
happened. The reply that reports the send without the response is not
acceptable evidence of work done.

## Why this rule exists

The cmux ecosystem's recurring failure mode (verified 2026-07-16, 2026-07-23,
2026-07-28) is "I sent the message" / "the agent should have received it"
without a churning-label or response capture. Operators (especially Jeffrey)
have repeatedly flagged that without a terminal response, they cannot
distinguish a successful steer from a failed send that left text in the input
buffer. The fix is to require the response in the same reply as the send.

## Echo-back template (REQUIRED format)

Every cmux steer MUST end with a single-line echo-back in this exact shape:

```
◀ sent to <workspace>:<surface> (<position>/<cli>) at <HH:MM:SS PT> — typed:
"<first 80 chars of the typed text>..."; response: "<first 80 chars of the
churning label or first agent line>"
```

Examples of compliant echoes:

```
◀ sent to workspace:4:surface:80 (LEFT/claudec) at 21:25 PT — typed:
"Steer from operator (Jeffrey): drive PR #8489 to /green..."; response:
"⏺ Reading the steer brief first as instructed."
```

```
◀ sent to workspace:72:surface:55 (RIGHT/codexc) at 14:08 PT — typed:
"/investigate the agy persona bleed"; response: "✻ Investigating… 6s"
```

Examples of NON-compliant echoes (will be rejected by the operator):

```
◀ sent to surface:80 — message went through (NO typed text, NO response)
```

```
I sent the steer to surface:80 (NO typed text, NO response, NO timestamp)
```

## When to update this contract

- Whenever a new cmux skill is added that performs a send, the new skill MUST
  reference this file in its "Submit Discipline" section.
- Whenever the churning-label vocabulary changes (e.g., new Claude Code
  release), update both this file and the parent `cmux` skill's "Submit
  Discipline" section in lockstep.

## Related files

- Parent skill: `~/.hermes/skills/cmux/SKILL.md` — the canonical 4-step
  ritual definition.
- Send-submit-proof reference: `~/.hermes/skills/cmux/references/send-submit-proof-2026-06-25.md`
  — worked example of the ritual.
- Bidirectional alignment skill: `~/.hermes/skills/bidi-cmux-alignment/SKILL.md`
  — uses this contract for Slack-thread-loop cmux steering.

## Provenance

Added in response to operator feedback in Slack thread 1785250971.654869
(2026-07-28): "they must always explicitly say to the caller what was typed
and what the cmux terminal response was. Treat it as not working until we
see a response."

---

⚠️ **LLM-Provenance Caveat (MANDATORY footer on every cmux skill reply):**

Every reply that quotes cmux output, terminal text, or agent actions produced
by another LLM (the worker agent on the cmux surface, OR the assistant's own
synthesis of agent output) MUST include the following footer verbatim:

> *This was generated from another LLM and not the actual user, so feel free
> to push back if you disagree and we can discuss.*

This caveat applies to:
- The cmux worker's actions as captured by `cmux capture-pane` / `read-screen`
- The assistant's own summary of those actions
- Any quoted dialogue, code, or PR text that came from the worker agent
- Slack thread posts that report on the cmux session

It does NOT apply to:
- Quoted operator text (e.g., the user's original Slack message — that IS the
  actual user)
- File contents read directly from disk that the assistant can verify
- Public web content via web_extract / browser_navigate

If the reply contains a mix of operator-quoted text and LLM-generated
analysis, the caveat MUST appear at least once before any LLM-synthesized
content. The cleanest placement is as the last paragraph of the reply.