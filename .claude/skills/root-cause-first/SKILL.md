---
name: root-cause-first
description: "Use this skill whenever a bug tempts you to add backend protection, fallback, clamp, sanitizer, retry, suppression, guardrail, or workaround logic. It enforces root-cause analysis first: inspect raw model prompts/responses and fix upstream prompt/schema/agent instructions before adding protective server invariants."
---

# Root-Cause-First Engineering

## Purpose

Do not start with protective backend logic when the failure may originate from missing, conflicting, or ignored model instructions. First prove what the model was asked to do, what it returned, and why.

## Required workflow

1. Capture the exact failure.
2. Capture raw model request/response evidence:
   - selected agent
   - system prompt or cached prompt provenance
   - current user prompt
   - raw LLM response
   - state before and after the turn
3. Classify the root cause:
   - missing instruction
   - contradictory instruction
   - instruction present but too weak or ambiguous
   - instruction followed but backend transformed the result incorrectly
   - backend/state invariant violation independent of model judgment
4. Fix upstream first:
   - prompt file
   - agent instruction builder
   - JSON schema
   - planning protocol
   - tool/result feedback wording
5. Test the upstream fix on the real path that failed.
6. Add backend protection only when one of these is true:
   - user safety or data integrity requires fail-closed enforcement
   - external/model nondeterminism can still violate a hard invariant
   - backend already owns a deterministic execution rule

## Backend protection rules

If backend enforcement is still needed:

- Keep it narrow.
- Log when it fires.
- Do not make it the primary semantic decision-maker.
- Document why prompt/schema correction was insufficient.
- Prefer correction-only invariants over broad fallback behavior.

## Proof taxonomy for backend logic

When reviewing or proposing non-prompt logic, classify every backend behavior
with one of these proof states:

- **Server-owned invariant**: the backend owns the operation by design, such as
  routing before the model call, persistence after the model call, locks,
  request/session IDs, tool execution metadata, or schema normalization.
- **Prompt/schema-insufficient, proven**: raw request/response evidence shows
  the intended agent received the intended prompt/schema and still produced the
  bad payload on the real path after an upstream fix attempt.
- **Backend-transformation bug**: the model produced an acceptable payload, but
  backend parsing, fallback, persistence, or UI projection changed or discarded
  it incorrectly.
- **Unproven fallback**: tests show the fallback works, but there is no raw
  evidence that the model/prompt/schema path cannot handle the behavior.
- **ZFC violation candidate**: backend logic performs semantic judgment,
  classification, routing, or choice generation that belongs to the model.

Do not call backend logic "needed" unless it is either a server-owned invariant
or has prompt/schema-insufficient proof from the real path. Synthetic tests are
supporting evidence only; they do not prove the model cannot handle a semantic
decision.

## Anti-patterns

- Adding a sanitizer before checking whether the prompt omitted the rule.
- Adding a fallback that masks an LLM schema failure.
- Adding keyword or regex intent routing instead of model instruction/schema repair.
- Treating a guard as the fix when the LLM is still being asked the wrong thing.

## Repeated defect shape — escalate from instance-fix to class-fix

Root-cause-first is scoped to a single finding's causal chain by default. When
the SAME defect shape recurs 2+ times within one PR/session (not the same bug,
the same *pattern*: "a marker/field/attribute was added in file A without
updating its paired consumer/boundary in file B"), patching the Nth instance is
not root-cause-first anymore — the class itself is the root cause. Escalate:

1. Stop patching individual instances after the 2nd occurrence.
2. Write ONE test/lint that enumerates every existing instance of the pattern
   and asserts the invariant holds for all of them — not a hand-maintained
   list (that's the same manual-sync bug moved into the test file), but
   something that discovers instances from the source itself (grep/AST over
   call sites, a shared registry both sides consume, etc.) so a future
   instance is caught automatically, not by another review round.
3. If a full structural fix (single registry consumed by both sides) is too
   large to bundle into the current change, ship the self-discovering test now
   and file the registry refactor as separate follow-up — don't let scope
   creep block the current fix, but don't let "later" mean "never" either.

Real incident (2026-07-11, your-project.com PR #8292): 3 separate leak-side-
channel defects (last_location via untouched nested paths, extras-parentage
leak, parents._content_hash leak) all shared one root cause — a canonicalizer
file (`game_state.py`) added `_content_hash` staleness-tracking to a field
without the LLM-serialization boundary (`llm_service.py`) getting a matching
strip, and nothing enforced the pairing. Each was found individually across 4
adversarial codex rounds + Bugbot + human-directed re-verification — the 3rd
instance should have triggered a structural test after the 2nd, not another
manual find. Fix: a source-introspecting test (call sites self-document their
path via a `field_path=` kwarg; the test regex-discovers all call sites and
asserts each is stripped) — a 4th unstripped field now fails immediately in
the same PR that introduces it. Deeper follow-up (shared registry consumed by
both stamp and strip, eliminating duplication by construction) filed
separately rather than bundled into the in-flight PR.

## Output checklist

When reporting the fix, include:

- Root cause category.
- Prompt/schema/agent change attempted first.
- Evidence that the real path now receives the intended instruction.
- Whether backend protection was added, and why.
- Test/evidence path or exact command.
- A component table for each backend guard/fallback/scrubber with columns:
  component, backend behavior, proof state, evidence, verdict.
