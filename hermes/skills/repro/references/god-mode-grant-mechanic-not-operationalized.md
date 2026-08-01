# God-Mode grants: narrative-only mechanic, no canonical schema

**Bug class:** A God-Mode grant at character creation (or mid-game) emits a **custom feature** as narrative text inside the agent's `god_mode_response`, but the same feature is **NOT** written to a machine-parseable canonical schema field. On subsequent turns the LLM has to re-derive the mechanic from old prose buried in 200+ turns of context, and the derivation drifts.

**Distinct from the 4-factor `god-mode-directive-missing` matrix** (A: streaming save-drop / B: wrong-storage routing / C: stale streaming bundle / D: backend override). That class is about **directive instructions** (e.g., "queen should be level 14") being dropped on the way to the LLM payload. This class is about **custom features** being granted in-narrative but never parameterized. The directive text reaches the LLM — the issue is that there's no schema for the LLM to apply.

**Distinct from `two-pronged-render-and-persist-bug`** (render-side field stripping + persist-side save-drop). That class is about existing canonical fields failing to roundtrip. This class is about the canonical field NEVER being created in the first place.

**Distinct from `npc-status-persistence-bug`** (LLM emits "X captured" in narrative but `state_updates.npc_data[X].status` write missing). Same family of "narrative outcome vs persisted state" but the target is **player features** (`player_character_data.features[]`), not NPC state.

## Smoking-gun diagnostic

The static-evidence grep from `phenotype-lock-static-evidence.md` returns 0 hits in `$PROJECT_ROOT/prompts/` and `$PROJECT_ROOT/`:

```
grep -rin "<feature_name>" $PROJECT_ROOT/prompts/                 # 0 hits
grep -rin "<feature_name>" $PROJECT_ROOT/ --include="*.py"        # 0 hits
```

If the user-reported name doesn't match any prompt or code symbol, **do NOT stop** at "natural-language LLM prose" — there's a second layer to check. Look at the twin's `current_state.player_character_data.features[]` array. The feature WILL appear there, as a plain string with no schema:

```python
# twin-export-game_state.json — player_character_data.features[]
"The Conqueror's Insight (1/Long Rest - Scaling Reroll)"   # ← 28 entries, all plain strings
```

The canonical field exists, the LLM can read it, but it has no `trigger_check_types`, `formula`, `dice_expression`, `rest_cycle`. The LLM has to guess every turn. Different guesses on different turns = the user-visible symptom of "the LLM keeps forgetting".

## Diagnostic recipe (the 3-step forensic)

**Step 1 — BQ raw payload inspection.** Query `worldarchitecture-ai.llm_forensics.llm_payloads` for the campaign. Look for the **two-row pattern per turn**:

| `event_type` | `turn_index` | `req_len` | What's in it |
|---|---|---|---|
| `stream_story_with_game_state` | populated | 100-500 bytes | The parsed user message only — too small to be the full payload |
| `gameplay_streaming` | NULL | 350000+ bytes | The full Gemini request — system prompt + character + history + state |

**Critical:** the small row (`stream_story_with_game_state`) is the *parsed* request, not the prompt that was sent. To see what the LLM actually saw, query the `gameplay_streaming` row. Grep that 350KB JSON for the feature name in context.

**Step 2 — `player_character_data.features[]` shape inspection.** On the twin's `current_state`, look at the `features` array. Note:
- All entries are plain strings (28/28 in worked example #8320)
- The feature has no schema for `trigger_check_types`, `formula`, `dice_expression`, `uses_remaining`, `rest_cycle`
- The LLM sees the string in context on every turn but has no machine-parseable way to apply it consistently

**Step 3 — Dice-roll rubric grep.** Search all prompt files under `$PROJECT_ROOT/prompts/` for the canonical dice-roll rubric (likely `dice_roll_instruction.md`, `combat_roll_instruction.md`, or a section in the system prompt). Check whether the rubric tells the LLM:
> "When `player_character_data.features[]` has `formula: "1d[level]_added"` and `trigger_check_types: ["persuasion", "insight"]`, the LLM MUST roll that bonus on every matching check turn."

In worked example #8320: rubric says nothing about custom features. The LLM has to infer "Conqueror's Spark → Persuasion insight bonus" from the narrative string.

## Mechanic-ambiguity diagnostic (advanced)

A subtler variant: the user and the LLM disagree on what the mechanic even IS. Worked example #8320:

- User wants: `1d[level]` (i.e. `1d17`) **ADDED** to the roll total.
- LLM produced earlier: `1d20+11` **reroll** (the "Conqueror's Insight" trait was being applied as a reroll, not a bonus).

Both are valid interpretations of `"The Conqueror's Insight (1/Long Rest - Scaling Reroll)"`. The plain-string feature doesn't disambiguate ADDED vs REPLACE.

**Diagnostic step:** grep the entire `story/` collection for every earlier turn where the user invoked the feature. The text reveals the user's intended mechanic. Cross-reference against the dice rolls in `dice_rolls[]` — if every previous invocation was a reroll, then the user's claim that the LLM "keeps forgetting to add 1d[level]" is actually a **regression** where the mechanic interpretation drifted. The fix needs to either:
1. Lock the mechanic in code/schema, OR
2. Persist the user's interpretation in the canonical feature schema (e.g., `formula: "1d[level]_added"` vs `formula: "reroll"`)

## Same-symptom verdict table (extended for this class)

| Original required symptom | New copied-run observation | Evidence | Verdict |
|---|---|---|---|
| Feature name absent from `player_character_data.features[]` | TBD (typically present as plain string) | twin `current_state` | `FEATURE PRESENT, SCHEMA MISSING` |
| `features[]` entry has `trigger_check_types`/`formula`/`dice_expression` | TBD | twin `current_state` | `TYPED-OBJECT / STRING-ONLY` |
| BQ `request_json` for the failing turn mentions the feature name | TBD | BQ turn N raw | `YES / NO` |
| `dice_rolls[]` for the matching check contains a separate roll with `purpose: <feature.name> Bonus` | TBD | BQ turn N parsed or twin `current_state` | `YES / NO` (this is the ironclad proof) |

Only `dice_rolls[]` containing the bonus roll AND `total` summing in that bonus count as REPRO for this class.

## Recommended fix direction (4-leg architecture)

Pattern lifted verbatim from PR #7864 / #8162 (`resource-registry-rest-tracking` 4-leg architecture):

| Leg | Where | What |
|---|---|---|
| 1. Prompt MUST-emit | `$PROJECT_ROOT/prompts/god_mode_instruction.md` | When emitting a `granted_feature` in `god_mode_response`, REQUIRE a structured `player_character_data.features[]` entry alongside the narrative text |
| 2. Backend validator auto-fill | `world_logic.py` / `llm_parser.py` / `process_action_unified.py` | After God-Mode agent parses the response, if any narrative feature mention lacks a structured schema entry, derive it from the narrative. **Pattern of last resort** — prefer leg 1 |
| 3. Canonical schema | `$PROJECT_ROOT/prompts/character_creation_instruction.md` (and `player_character_state_update_instruction.md` if it exists) | Define the feature schema: `{ name, trigger_check_types: string[], formula: "1d[level]_added" \| "reroll" \| "advantage" \| ..., dice_expression: string, rest_cycle: "long_rest" \| "short_rest" \| "none", uses_remaining: number }` |
| 4. RED tests | `$PROJECT_ROOT/tests/test_god_mode_feature_mechanic.py` | Given the structured feature, replay a matching check turn; assert `dice_rolls[]` contains the bonus roll AND `total` includes it |

**Hard rule (lifted from `feedback_2026-05-29_god_mode_broken_prompt_reference`):** the prompt rule must be **in-place text** in a file already in `GodModeAgent.REQUIRED_PROMPT_ORDER`. Do NOT cross-reference another prompt file from inside the rule — those references break silently.

## Sibling-campaign structural issue flag

When the campaign accumulates ≥3 of this class (or ≥3 of any God-Mode-grant class — directive-missing, two-pronged-render-persist, npc-status-persistence), the campaign has a **structural issue**: every reproduction exposes a different angle of the same root cause. In the issue body and PR description:

> "6th repro on this campaign — likely all 6 share root-cause class 'God-Mode grants emitted as narrative but never canonicalized as schema'. PR direction should aim at a SHARED underlying fix (4-leg architecture), not a per-repro workaround."

This prevents triage from treating each as a one-off. Verified from campaign `xK3fp5XrV24oarIINTF7` (issues #8266, #8275, #8277, #8283, #8293, **#8320**, all in 2026-07-08 to 2026-07-10).

## Worked example: campaign `xK3fp5XrV24oarIINTF7`, issue #8320, PR #8321

Filed 2026-07-10. Verdict: REPRO. Twin `BneOx13aEN3RcxW7chTM`. Evidence bundle at `evidence/issue-8320/`:
- `turn-275-gameplay-streaming-raw-payload.json` (350KB raw BQ payload)
- `turn-274-parsed-request-response.json` + `turn-275-parsed-request-response.json`
- `twin-export-story.txt` (1248KB, 862 entries) + `twin-export-game_state.json` (123KB)

Static-evidence greps: 0 hits in prompts/, 0 hits in code. Twin features[] = 28 plain strings. Mechanic-ambiguity variant: user wants ADDED, LLM was previously producing REROLL.

Recommended fix queued for an AO worker pickup. Green path requires leg 1+3+4 (leg 2 validator auto-fill is overkill for one feature — only add if the issue generalizes across campaigns).

## Related references (in same umbrella)

- `phenotype-lock-static-evidence.md` — the 3 static-evidence greps that flag this class via 0-hits in code/prompts.
- `god-mode-directive-missing-subclasses.md` — sibling class for directive text being dropped on the way to LLM payload (this class is about the GRANT not the DROPPED DIRECTIVE).
- `two-pronged-render-and-persist-bug.md` — sibling class for canonical fields failing to roundtrip (this class is about the canonical field NEVER being created).
- `npc-status-persistence-bug.md` — sibling class for narrative-only state changes (this class targets player features, not NPC state).
- `firestore-path-and-uid-resolution.md` — canonical path (`users/{uid}/campaigns/{cid}/game_states/current_state`) for the features[] read.
