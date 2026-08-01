# Two-pronged root cause pattern: "render drops field" + "persist drops field"

**When one user-visible symptom has two independent root causes that both need to be fixed.**

A recurring pattern in the god-mode-directive + lineage bug class: the LLM complains about a user-visible field being missing or wrong, but the actual cause is **two orthogonal bugs** that both need to fire for the symptom to appear.

## The pattern

The user reports: "LLM keeps doing X wrong even after I correct it." Investigation reveals:

1. **Render-side bug**: The field is correctly persisted in Firestore, but the system-prompt constructor (`get_character_identity_block`, `build_god_mode_directives_block`, etc.) cannot read it from the persisted location, so the LLM never sees it in its prompt.
2. **Persist-side bug**: User-level corrections (god-mode directives, in-character corrections) are added to `directives.add` or `state_updates` but the save logic on the production code path silently drops them, so they never make it back into the persisted state.

Both bugs are usually latent — each one alone may not produce a visible symptom. The user-visible symptom only appears when BOTH fire together (LLM has no field in prompt AND corrections don't stick).

## Canonical example: campaign `xK3fp5XrV24oarIINTF7`, 2026-07-08 (issue #8283)

User reports: "LLM keeps calling me 'daughter of the queen' and ignoring my correction."

### Bug 1 (render-side) — fixed by [PR #8265](https://github.com/$GITHUB_REPOSITORY/pull/8265)

`validate_and_correct_state()` moves `parentage` out of `player_character_data` into `custom_campaign_state.player_character_data_extras` on every state validation. `get_character_identity_block` reads from `player_character_data` only — so the LLM never sees lineage. Without explicit lineage in the prompt, the LLM infers from loose context (Rhaenyra in the scene) and hallucinates "daughter of Rhaenyra."

### Bug 2 (persist-side) — fixed by [PR #8132](https://github.com/$GITHUB_REPOSITORY/pull/8132)

`llm_parser.stream_story_with_game_state` was the production-primary path but had ZERO god-mode directive-processing logic. Only the legacy non-streaming `world_logic.process_action_unified` path called `apply_god_mode_directives()`. Every god-mode directive issued through streaming was silently discarded. The user's 04:28:28 UTC correction added 3 `directives.add` rules that were never re-injected on subsequent turns.

### Why both bugs are needed for the visible symptom

- Bug 1 alone: LLM has lineage text from `god_mode.setting` ("bastard daughter of Daemon"). May be wrong sometimes but not consistent.
- Bug 2 alone: User's god-mode corrections stick. LLM eventually gets the right lineage through re-injection.
- **Both fire**: LLM has no lineage in prompt AND user's corrections don't stick → consistent "daughter of Rhaenyra" hallucination across many turns.

## Diagnostic recipe (use when symptom is "LLM ignores my correction" + "field appears wrong")

1. **BQ forensic on the LLM request payload** — does the LLM receive the field in its system prompt? (Check for `## <FIELD> HEADER` block, or for known substring of the field's value.) If NO → Bug 1 (render-side).
2. **Firestore forensic on the persisted state** — after the user issues a correction, is the field updated in the doc? If NO → Bug 2 (persist-side).
3. **Story-doc forensic** — does the LLM's response_text actually emit the correction as a `state_updates` write? If YES but the write doesn't land → Bug 2 (save logic drops it).
4. **Sibling fix PRs** — before proposing a new fix, search the open PRs for ones that already address Bug 1 or Bug 2. The user is asking for /repro / green because they assume no fix exists; the answer may be "fix already exists, just drive it."

## How to know which bug is the proximate cause

| Symptom | Likely proximate cause |
|---|---|
| Field is wrong from campaign start | Bug 1 (render never had it) |
| Field was right, then broke after scene N | Check if a state mutation in scene N stripped/popped the field. Both bugs possible. |
| Field resets every turn despite persistent directive | Bug 2 (directives not re-injected) |
| Field oscillates correct/wrong across turns | Bug 1 + Bug 2 interaction (LLM sometimes gets it from `god_mode.setting` text, sometimes hallucinates) |

## How to write the user-facing verdict

When you identify the two-pronged pattern, do NOT just merge them into one "root cause" sentence. The user needs to know:

1. Proximate cause (which bug fires when)
2. Underlying cause (the deeper data-flow bug)
3. Which existing fix PRs cover each
4. Why the user remembers "it used to work better before" — usually because the surface context that masked Bug 1 (e.g. `god_mode.setting` text being a stronger signal) changed.

## Sibling instances to date

- #8283 (Visenya "daughter of queen") = render-side (parentage) + persist-side (streaming save-drop) — fix #8265 + #8132
- #8103 (multi-verse + divine directive) = persist-side (streaming save-drop) — fix #8132
- #8275 (queen-level-14) = render-side (level) + persist-side (streaming save-drop) — multiple axes
- #8277 family (companion_request not rendered) = render-side (narrative render) + may have persist-side sibling

When a repro surfaces the god-mode-directive-missing class, **always probe for the render-side sibling**. The user often thinks it's "one bug" but it's typically two.

## Related references

- `references/god-mode-directive-missing-subclasses.md` — covers Bug 2 in detail
- `references/npc-status-persistence-bug.md` — covers confused-state sub-classes (write semantics); often confuses with render-side because both look like "the LLM said X but state doesn't reflect X"
- `references/static-evidence-sufficient-no-live-turn.md` — when to skip the live LLM turn and rely on static state
