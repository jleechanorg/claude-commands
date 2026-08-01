# Recurring failure pattern: evidence-attach (2026-07-02 → 2026-07-14)

**The data behind the Pre-Send Gate.** This is the 4-incident chain that
proves the reactive `evidence-attach-not-path-cite` SOUL.md rule was
insufficient — and motivated the v1.5.0 Pre-Send Gate + the v1.6.0 OAuth
preflight.

## Incident 1 — 2026-07-02, PR #8139 (first time)

**User message (verbatim, Slack C0AH3RY3DK6):**
> "Let's /green and show screenshots here
> <https://github.com/$GITHUB_REPOSITORY/pull/8139|...>"

**What the agent did:** Emitted 4 `MEDIA:/Users/.../evidence/*.png` text
tokens + 1 `MEDIA:/Users/.../*.gif` token in the reply. All rendered as
literal text — the user saw a wall of `MEDIA:` paths with no inline images.

**User reaction (next turn):**
> "you are showing me a file path you need to upload the actual media to
> this thread"

**Root cause identified at the time:** Agent treated `/Users/.../evidence/foo.png`
as if it were a shared path the user could browse. Slack renders file paths
as text; the user only sees attachments inline.

**Fix attempted:** Created `evidence-attach-to-slack` skill v1.0 with the
3-stage `files.completeUploadExternal` recipe. Marked as
"auto-load when user complains about missing screenshots."

## Incident 2 — 2026-07-10, PR #7953

**User message (verbatim, paraphrased):** "Where's the screenshot? I asked
for evidence in the PR description AND the Slack thread."

**What the agent did:** Successfully uploaded 4 PNGs via the 3-stage flow.
BUT — the channel-bridge leaked 6-8 internal narration messages (think-block
prose, `:gear: mcp__slack__conversations_add_message:` echoes,
`:snake: execute_code:` chatter) into the thread AFTER the uploads. The
attachments got buried under bot chatter. The user saw a wall of bot
messages and assumed no screenshots were posted.

**User reaction (next turn):**
> "I need the media evidence on this thread" / "you keep skipping this"

**Root cause identified at the time:** The uploads succeeded but the cluster
anchor (a summary message naming each attachment) was missing. The user
scrolled past the attachments and replied.

**Fix attempted:** Skill v1.1 added the **summary-as-cluster-anchor** step
(Stage 3½) and the **verify-after-summary** Pattern B (later refined to
**verify-before-summary** Pattern A in v1.3.0).

## Incident 3 — 2026-07-13, PR #8337

**User message (verbatim, paraphrased):** "Why are you failing the upload
again? Try the gist fallback."

**What the agent did:** Attempted Stage 1 with `-d '{"filename":...,"length":...}'`
JSON body. Slack API returned `invalid_arguments` with
`missing required field: length, filename`. JSON silently drops the form
fields. Pivoted to gist-raw-URL fallback, but bot AND xoxp tokens both
returned `missing_scope: files:write:user`.

**Root cause identified at the time:** Two bugs:
1. Stage 1 wants `application/x-www-form-urlencoded` form fields, not JSON.
2. Both Slack tokens lack `files:write` scope. The user must reinstall.

**Fix attempted:** Skill v1.4 added (a) the form-encoding recipe for Stage
1 + Stage 3, (b) the third-tier gist-raw-URL fallback as canonical when
both tokens lack `files:write` scope.

## Incident 4 — 2026-07-14, PR #8139 (second time) ← THIS SESSION

**User message (verbatim, Slack C0AH3RY3DK6/1783487028.812529):**
> "You always fail to attach images to a slack thread see slack shistory
> and /ms and /history and lets run /harness to roto cause. I need it
> visible here why do you always forget?"

**What the agent did:** Acknowledged the failure, ran /ms + /history +
/harness in parallel, root-caused to "reactive rule, not proactive gate",
applied 4 harness fixes:
1. SOUL.md `## COMMIT: evidence-attach-presend-gate` (NEW)
2. `evidence-attach-to-slack` v1.5.0 (added Pre-Send Gate section)
3. `tests/test_evidence_attach_presend_contract.py` (8 tests, all green)
4. Memory entry: "recurring-correction → pre-send gate, not post-hoc remediation"

Then captured all 4 evidence PNGs from the PR branch, pushed to a public
gist, and posted via `chat.postMessage` with `unfurl_media: true` — the
third-tier fallback worked end-to-end. User saw all 4 images inline.

**User reaction (next turn):**
> (out-of-band message was the same content I sent — confirming receipt of
> the gist-embedded reply with all 4 images visible)

**Root cause (final, post-harness analysis):**
The agent's prompt-level defaults push toward `MEDIA:/path` text tokens
because that's the path of least resistance in the chat-UI context. The
reactive SOUL.md rule fires only when the user complains. Across 4
incidents in 12 days, the rule never fired proactively — only after the
user typed "you forgot" / "you always" / "stop doing X".

## Pattern analysis

**Trigger phrases the user actually typed (collected across all 4 incidents):**
- "you always fail to attach images"
- "you forgot the screenshot"
- "you are showing me a file path"
- "where's the screenshot?"
- "I need the media evidence on this thread"
- "you keep skipping this"
- "why do you always forget?"
- "stop forgetting use /harness and /learn and fix it"

**The signal that distinguishes this from a one-off:** when the user uses
"you always", "stop doing X", or "you forgot" (past tense, generic, not
specific to a single screenshot) — they are pointing at a PATTERN, not a
specific missing image. This is the trigger for the pre-send gate, not
the post-hoc fix.

**General principle (added to harness-postmortem v0.5.0, 2026-07-14):**
> **Recurring-correction rule:** when the same user correction hits ≥3 times
> across ≤30 days, the fix MUST move from "post-hoc documentation" to
> "pre-send invariant." Documentation-only fixes do not survive between
> sessions — the agent's defaults push toward the path of least resistance.
> A pre-send gate (regex matching the draft body, fired before the message
> tool is invoked) is the only durable countermeasure.

**Counter-evidence (lessons learned from fixes that DIDN'T work):**

| Fix type | Worked? | Why |
|---|---|---|
| Skill text documentation | NO | Doesn't auto-fire; agent doesn't proactively load it |
| SOUL.md post-hoc rule | NO | Only fires after user complains; the user has to see the bad output first |
| SOUL.md pre-send gate (regex + ordering) | YES | Fires before the message tool; doesn't depend on agent remembering |
| Test contract (8 tests) | YES (preventatively) | Catches future regressions; CI gate |
| OAuth scope reinstall | TBD (pending) | Would re-enable native Slack file attachments, but doesn't fix the deeper "agent defaults to text" issue |

The agent still has the same default behavior (`MEDIA:/path` text tokens
when not actively thinking). The Pre-Send Gate intercepts this at the
draft-composition step. The OAuth scope reinstall would just make the
gate's "use the canonical 3-stage flow" path actually work — but the
gate itself is what prevents the failure regardless of which path runs.

## Provenance

- Slack thread for incident 4: C0AH3RY3DK6/1783487028.812529
- Gist created during incident 4 fix: 7cfcc454079283f8973054271d19efe6
- PR #8139: https://github.com/$GITHUB_REPOSITORY/pull/8139
- SOUL.md COMMIT block added: `## COMMIT: evidence-attach-presend-gate`
- Test file: `tests/test_evidence_attach_presend_contract.py` (8 tests)
- Skill version bump: v1.4.0 → v1.5.0 → v1.6.0 (Pre-Send Gate + OAuth preflight)

## See also

- `~/.hermes/workspace/SOUL.md` — `## COMMIT: evidence-attach-presend-gate`
- `~/.hermes/workspace/SOUL.md` — `## COMMIT: evidence-attach-not-path-cite` (the older reactive rule, still useful as a safety net)
- `~/.hermes/skills/harness-postmortem/SKILL.md` — Phase 1.5d: recurring-correction → pre-send gate (added 2026-07-14)
- `~/.hermes/skills/evidence-attach-to-slack/SKILL.md` — the canonical skill
- `~/.claude/projects/*/memory/bashrc-profile-xapp-drift-blocks-launchd` — the xoxp token lives in `~/.profile`, not `~/.bashrc`