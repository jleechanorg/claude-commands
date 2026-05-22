---
description: Alias for /evidence_review (which now includes /es evidence-standards check)
aliases: []
type: orchestration
execution_mode: immediate
---

# /er — Alias for /evidence_review

Runs `/evidence_review`, which now includes the `/es` evidence-standards check as Step 4 (after evidence review completes).

**Usage**: `/er [subject or path]`

## Action

Invoke `/evidence_review` with the same `$ARGUMENTS`.

This is a thin alias — all logic (evidence review + evidence standards + synthesis) lives in `.claude/commands/evidence_review.md`.
