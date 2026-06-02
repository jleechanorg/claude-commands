---
name: zero-framework-cognition
description: Use when designing or reviewing model-owned contracts, output schemas, backend guards, routing, semantic parsing, intent detection, or data fields where application code might duplicate judgment or ask a model for redundant facts.
---

# Zero-Framework Cognition

## Core Principle

Models decide; server executes.

Application code must not replace model judgment with keyword routing, regex
intent detection, heuristic classification, duplicate semantic checks, or
redundant field computations. The backend should execute tools, persist state,
and normalize deterministic output shape. Backend correction is a last resort:
first prove the prompt/schema/agent contract cannot prevent the bad payload on
the real path, then add only the narrowest correction-only invariant.

Reference: [Zero Framework Cognition: A Way to Build Resilient AI Applications](https://steve-yegge.medium.com/zero-framework-cognition-a-way-to-build-resilient-ai-applications-56b090ed3e69).

## Model Decision Engines

In this repository, "model" means:

- The LLMs used by the application for reasoning, narration, schema output,
  routing decisions that require context, and semantic judgment.
- The FastEmbed semantic intent classifier where the repository already uses it
  as a model-backed local classifier.

Do not replace either with new application-code heuristics. New regex,
substring checks, weighted keyword lists, or phrase maps for semantic judgment
are ZFC violations.

## Minimal Semantic Fields

Ask the model for the smallest set of fields that expresses the semantic
decision. Do not ask the model to emit multiple equivalent fields that can drift
apart.

Prefer:

```json
{
  "current_level": 4,
  "target_level": 5
}
```

Over:

```json
{
  "level_up": true,
  "level_up_available": true,
  "current_level": 4,
  "target_level": 5,
  "new_level": 5,
  "current_turn_exp": 6900,
  "total_exp_for_next_level": 6500,
  "additional_exp_to_next_level": 0
}
```

The first contract has one semantic fact: the model believes the target state
is level 5 from level 4. The second contract gives the model many chances to
contradict itself.

## Field Ownership

Every shared field needs one authoritative writer.

Use this split:

- **Model-owned semantic fields:** decisions, selected intent, target state,
  narrative meaning, choices, reasons.
- **Backend-owned deterministic derivatives:** aliases, display labels,
  normalized booleans, progress percentages, IDs, timestamps, persistence
  wrappers, UI payload formatting.
- **Server-owned control state:** locks, in-progress flags, tool execution
  results, commit status, request IDs, modal session state.

If two fields mean the same thing, delete one or derive it deterministically
outside the model contract.

## Correct Pattern

1. Give the model enough context to make the decision.
2. Request the minimal semantic output needed to express that decision.
3. Use schema constraints to make the minimal output explicit.
4. Capture raw request/response evidence when the model emits a bad payload.
5. Fix the prompt, schema, or selected-agent instruction first.
6. Derive display and compatibility aliases in deterministic backend code.
7. Persist tool results and state changes server-side.
8. Add backend guards only as a last-resort, narrow correction of contradictory
   explicit payloads after the prompt/schema path is proven insufficient.

## Banned Patterns

- Keyword or substring routing for user intent.
- New regex or regexp-based semantic classification, intent detection, routing,
  or policy judgment.
- Hardcoded phrase-to-action maps.
- Hand-tuned keyword scores.
- Explicit `if` / `else` chains that infer meaning from user text.
- Asking the model to emit redundant booleans, aliases, totals, and deltas for
  the same semantic decision.
- Backend recomputation of semantic decisions that should belong to the model.
- Backend guards added before capturing raw request/response and checking
  whether the model received the right prompt/schema.
- Treating a backend correction as the fix when the model is still being asked
  for redundant, ambiguous, or server-owned fields.

## Redundant Field Review Checklist

When adding or reviewing a model output field, ask:

- Is this field the minimal semantic decision, or a display derivative?
- Can it be derived exactly from another accepted field?
- Is another field already expressing the same fact?
- Who is the authoritative writer?
- What happens if this field contradicts its sibling fields?
- Can schema shape remove the contradiction surface?
- Has the raw model request/response proven the prompt/schema gap?

If the field is redundant, remove it from the model contract and derive it
deterministically after the model response is accepted.

## Allowed Deterministic Code

ZFC does not ban mechanical code. These are allowed:

- Syntax parsing, lexing, type checking, JSON serialization, URL encoding.
- Schema validation and structural validation.
- File existence checks, path resolution, process-state checks.
- Deterministic transformations with no judgment call.
- Tests with explicit expected outputs.

If the code asks "what does this mean?" or "what should we do?", use a model.
If the code asks "is this JSON valid?" or "does this file exist?", deterministic
code is appropriate.

## Backend Guard Rule

Backend protection is allowed only after the root cause has been checked at the
prompt/schema layer. The first fix attempt should be upstream: selected agent,
prompt wording, schema shape, or tool-result feedback. Backend guards are the
last resort, not the primary design.

For backend adjusters, corrections, defaults, suppressions, clamps, retries,
rollbacks, fallbacks, or composition logic around model-owned output, also run
`.claude/skills/zfc-adjuster/SKILL.md`. The adjuster proof standard requires
root-cause-first proof, immutable or redacted raw-path evidence, state-aware
scope, conflict/rollback/composition behavior, and a proven need that
prompt/schema correction alone cannot handle.

Allowed guards:

- Suppress stale or contradictory explicit payloads.
- Normalize deterministic aliases for compatibility.
- Protect server-owned locks, session state, and tool execution state.
- Log narrow correction events for evidence and follow-up.

Disallowed guards:

- Compute the model's semantic decision from backend heuristics.
- Create a second source of truth for intent, eligibility, target state, or
  narrative meaning.
- Patch over prompt ambiguity without documenting why prompt/schema correction
  was insufficient.
- Correct a field that should have been removed from the model contract.

## Relationship To Domain Skills

Domain-specific ZFC skills can add file boundaries and contracts. For level-up
and rewards work, also use `.claude/skills/zfc-leveling-roadmap/SKILL.md`.
