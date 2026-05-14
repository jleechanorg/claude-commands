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
   - whether the failing selected agent actually loaded the prompt file you plan to edit
3. Classify the root cause:
   - missing instruction
   - contradictory instruction
   - instruction present but too weak or ambiguous
   - instruction followed but backend transformed the result incorrectly
   - backend/state invariant violation independent of model judgment
4. Fix upstream first:
   - prompt file
   - agent instruction builder
   - agent routing/precedence when the wrong agent handled the modal/state
   - JSON schema
   - planning protocol
   - tool/result feedback wording
5. Test the upstream fix on the real path that failed.
6. For level-up work, do not add backend enforcement unless the human explicitly approves enforcement in-thread.
7. Add backend protection only when one of these is true:
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

## Anti-patterns

- Adding a sanitizer before checking whether the prompt omitted the rule.
- Editing `LevelUpAgent` prompts when logs prove `RewardsAgent` or another agent handled the failing turn.
- Adding a fallback that masks an LLM schema failure.
- Adding keyword or regex intent routing instead of model instruction/schema repair.
- Treating a guard as the fix when the LLM is still being asked the wrong thing.

## Output checklist

When reporting the fix, include:

- Root cause category.
- Prompt/schema/agent change attempted first.
- Evidence that the real path now receives the intended instruction.
- Evidence that the selected agent/routing path is the intended one.
- Whether backend protection was added, and why.
- Test/evidence path or exact command.
