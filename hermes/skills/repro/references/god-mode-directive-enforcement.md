# God Mode Directive Enforcement Gap

**DEPRECATION NOTE (2026-07-08):** This reference captures the single-instance advisory-only gap from issue #7162/#7154. Five subsequent repros (#8012, #8080, #8103, #8065, #8275) revealed that "LLM ignored my directive" can be 4 different root causes — streaming-path save-drop (A), wrong-storage routing (B), stale streaming bundle (C, NEW), or backend override (D), with the original advisory-only gap now a tail case. For any repro where the campaign has multiple god-mode turns, defer to **`references/god-mode-directive-missing-subclasses.md`** first, which has the 4-factor matrix + BQ forensic recipe. Keep this file for the `_should_reject_directive` filter patterns (still canonical) and the original advisory-only framing when that's known to be the active root cause.

---

## Finding (2026-05-29, issue #7154)

God-mode directives are **advisory-only in the system prompt** — there is no runtime enforcement.
The LLM can and does narratively escalate past directives when its story logic pushes hard.

### Architecture

1. **Directive save path**: `world_logic.py` `_should_reject_directive()` filters → saved to
   `custom_campaign_state.god_mode_directives[]` in Firestore
2. **Directive injection path**: `agent_prompts.py` `build_god_mode_directives_block()` → `finalize_instructions()` → inserted into system prompt as `## Active God Mode Directives`
3. **No enforcement**: No structured field in the response schema prevents the LLM from
   narrating content that violates directives. No server-side guard in `world_logic.py` checks
   narrative output against directive constraints.

### `_should_reject_directive` filter patterns (world_logic.py:7759, confirmed 2026-05-29)

Rejects (directive NOT saved):
- **State value patterns**: "level is X", "hp is Y", "gold is Z" (followed by number or `=`)
- **One-time event patterns**: "you just killed", "you just defeated", "you just completed"
  - Escape hatch: if text after pattern contains `should`, `grant`, `affect`, `provide`, `give`,
    `drop`, `always` → treated as behavioral and NOT rejected
  - Also rejected if followed by "the/a/an" or proper noun (capitalized word)
- **Formatting patterns**: "always include", "format" (with formatting keywords like "in header")

Passes (directive IS saved):
- Behavioral rules: "Always apply Guidance", "Apply advantage to Stealth"
- Persistent mechanics, ongoing effects
- **Narrative gates**: "Delay X until Level 11" — passes all filters, gets saved

### Evidence from campaign ZMbCnA6bLVcjvyICXIHl

- **Issue:** #7162, **PR:** #7163 (draft)
- Directive saved: `"The Uchiha Rebellion/Coup arc is gated until Level 11, but political friction, surveillance events, and clan unrest must occur dynamically in the background."` (added 2026-05-29T05:15:00Z)
- Character level at violation: 5→6 during scene 45 (well below gate of 11)
- **Scene 36** (story line 893): LLM wrote *"finalize the deployment of the Military Police Force for a coordinated strike on the village leadership"* — user filed god-mode correction
- **Scene 37** (lines 907–912): God-mode correction applied, narrative pulled back to "Political Maneuvering" phase
- **Scene 45** (line 1090): LLM wrote *"the cold logic of your Neutral Evil orientation solidifies… catalyst for your ascension"* — violation recurred after correction with no further user intervention
- **Game state confirmed:** `player_character_data.level = 6`, `custom_campaign_state.god_mode_directives[0]` contains the directive
- **Verdict:** HISTORICAL RED ARTIFACT — original production data shows violation. Root cause confirmed as advisory-only enforcement (not save/filter/injection bug)
- **Source exports:** `/tmp/your-project.com/repro-exports/godmode-uchiha-directive-7162/source/`

### `build_god_mode_directives_block` (agent_prompts.py:2236, confirmed 2026-05-29)

Inserts directives into system prompt as `## Active God Mode Directives`. Confirmed: directive is present in prompt but LLM still violates it — this is the advisory-only gap.

### Fix options

1. **Structured field gate**: Add `narrative_gates` to response schema preventing certain story
   beats until conditions are met (most robust, requires schema change)
2. **Post-hoc check in world_logic**: After LLM response, scan for directive violations and
   auto-correct (reactive, may cause narrative jitter)
3. **Prompt hardening**: Stronger directive language with "FORBIDDEN" framing and consequence
   descriptions (weakest — still advisory)

### Investigation pattern for god-mode bugs

When a god-mode directive appears ignored:
1. Check Firestore `custom_campaign_state.god_mode_directives[]` — is it saved?
2. Check `_should_reject_directive` — would the directive have been filtered?
3. Check `build_god_mode_directives_block` output in system prompt — is it injected?
4. Check LLM response — does the narrative violate the directive despite it being in the prompt?
5. If (4), root cause is advisory-only enforcement, not a routing or save bug

**ADDITION (2026-07-08, #8275 verdict):** Steps 1-4 above can ALL pass (directive saved + injected + LLM respects it in the immediate turn) and the bug still recurs in later turns because of Factor C (stale streaming bundle) — the LLM reads game-state data from a bundle that doesn't reflect recent god-mode writes. Always cross-check the LLM-payload bundle against direct Firestore read for the same entity. See `references/god-mode-directive-missing-subclasses.md` for the full matrix.
