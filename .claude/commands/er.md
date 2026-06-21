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

**Hard rule — Unit-only evidence is NOT ALLOWED.** If the only proof for a claim is unit tests (Layer 1, mocked/isolated), the verdict must be INSUFFICIENT and the user must be explicitly warned. Minimum: Layer 2 end-to-end integration tests (real callstack, mocks only at external API boundaries). LLM/external-service behavior claims require real-service evidence. **Exception:** unit-only proof IS acceptable for non-production changes (docs, tests, tooling/scripts) or for production changes under 100 delta lines of non-test code.
