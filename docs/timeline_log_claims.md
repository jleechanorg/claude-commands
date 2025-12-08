# Timeline Log Budgeting Claim Review

This note reviews the claims from the "Align timeline log budgeting evidence and reuse duplication constant" change set.

## Summary
- The PR asserts that timeline log text is present alongside `story_history` in the structured request sent to the LLM and therefore the story budget should be divided by a `TIMELINE_LOG_DUPLICATION_FACTOR` of 2.05. This is not accurate for the current request path.
- The structured `LLMRequest` only serializes the truncated `story_history` plus entity-tracking metadata; it does **not** serialize the timeline log string built for the prompt scaffolding.
- The API call helper `_call_llm_api_with_llm_request` sends only the JSON string from `LLMRequest.to_json()`, so any prompt text (including timeline logs) constructed earlier is excluded from the payload.
- Because the timeline log text never reaches the API, dividing the available story budget by 2.05 artificially halves the usable story context and can trigger premature truncation without preventing any duplication.

## Evidence
1. `LLMRequest.to_json()` emits structured fields for `game_state`, `story_history`, `entity_tracking`, `checkpoint_block`, `core_memories`, `selected_prompts`, and `sequence_ids`; it does **not** include the timeline log string constructed in `_build_timeline_log`.
2. `_call_llm_api_with_llm_request` converts the `LLMRequest` to JSON, stringifies it, and calls `_call_llm_api` with that single JSON string as the prompt contents. The earlier `full_prompt` that embeds the timeline log is not used when this helper is invoked.
3. The only remaining consumer of `timeline_log_string` before the request is built is `EntityInstructionGenerator.generate_entity_instructions`, which uses the string for heuristic classification but does not embed it in the serialized payload.

## Impact
- The code now divides the story budget by 2.05 despite no duplicated timeline text being sent to the LLM. This reduces the retained story context and can cause unnecessary truncation or loss of recent turns while providing no protection against actual token overflow.
- The regression test documenting "timeline_log duplication" is therefore verifying behavior that does not occur in the structured request path.

## Suggested Next Steps
- Remove the `TIMELINE_LOG_DUPLICATION_FACTOR` adjustment (or gate it to the legacy prompt-concatenation path, if that path is restored) and re-baseline the end-to-end budget test against the real serialized payload.
- If timeline log text must be sent, explicitly add it to `LLMRequest` and the serialized prompt and size it accordingly; otherwise, keep the budget aligned with the actual payload shape.
