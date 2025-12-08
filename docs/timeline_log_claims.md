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
- Early revisions divided the story budget by 2.05 even though no duplicated timeline text was sent, which reduced retained context without preventing overflow. The guard is now gated via `TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST = False`, so the structured request path keeps the full story budget.
- Tests document both behaviors: current (timeline_log not serialized, guard dormant) and hypothetical (guard active if we re-enable serialization).

## Suggested Next Steps
- Keep the duplication guard gated unless a prompt path explicitly serializes timeline_log text; flip the flag and update tests/docs if that happens.
- If timeline log text must be sent, add it to `LLMRequest` and size it explicitly instead of relying on legacy prompt concatenation.
