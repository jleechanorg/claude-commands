# Preventing Scene Backtracking and Missed God-Mode Corrections

*Last updated: 2026-02-05*

This plan reorients the safeguards away from emitting blocking errors and toward
proactive prevention, automatic state repair, and low-friction guidance. Current
implementation covers preventive guards in `mvp_site/preventive_guards.py`
(wired via `mvp_site/world_logic.py` with tests in
`mvp_site/tests/test_preventive_guards.py`). Auto-reshot and resubmit mechanics
described below remain planned follow-ups.

## 1) God-mode directives are applied automatically
- Detect god-mode directives in `llm_service.continue_story` prompt prep and
  set `pending_god_mode` on `GameState.custom_campaign_state`.
- When the flag is set, pre-apply the directive as a state delta (e.g., forced
  location/time rewrites, inventory tweaks) before generating narrative so the
  model is steered into the corrected context.
- Inject a concise "god-mode applied" bullet list into the system prompt and
  require a short acknowledgement field in the structured response schema,
  but treat omissions as auto-reshots instead of user-facing errors. The
  processor should transparently resubmit with the same prompt until the
  acknowledgement appears.

## 2) Time/resource updates are auto-filled instead of erroring
- Teach `structured_fields_utils.extract_structured_fields` to infer
  high-impact events (loot, combat, travel) and auto-fill default deltas in the
  structured response (e.g., +gold from loot tables, +travel time from map
  heuristics) before validation runs.
- Add a preflight in `world_logic.process_action_unified` that patches missing
  `state_updates` with these defaults and logs the patch to the core-memory
  stream, avoiding user-visible failures.
- If the model omits critical deltas twice in a row, silently perform a single
  guided reshot with an expanded prompt reminder rather than surfacing an
  exception.

## 3) Continuity locks guide the model forward
- Track `last_scene_id`, `last_location`, and active entities in
  `custom_campaign_state` after each accepted turn; include this fingerprint in
  the next prompt as a "do not rewind" anchor.
- Extend `NarrativeSyncValidator` to auto-adjust minor regressions (e.g.,
  missing NPC) by merging prior state into the candidate response instead of
  throwing an error. Only severe conflicts trigger an internal reshot with a
  forward-only reminder, keeping the user flow uninterrupted.
- Add integration tests in `mvp_site/tests/` that confirm rewinds trigger
  auto-forward reshots and that god-mode corrections are acknowledged without
  surfacing validation errors to the player.
