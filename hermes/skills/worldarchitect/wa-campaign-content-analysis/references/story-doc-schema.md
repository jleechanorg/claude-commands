# Story-doc schema reference — verified 2026-07-13

Source: 2,464 gemini-authored story docs across 10 campaigns (Visenya V8, Bg3 Nocturna good, swtor-tenebria, Re:zero Theresa, Visenya v7, Visenya v7 (forgot queen dead), Bran the broken, Bran the broken (ignore directive), Bg3 shy, Iseki v1) in the `worldarchitecture-ai` Firestore project.

This is the **canonical schema reference** for WA story docs. Update this file whenever the schema changes.

## Top-level fields

| Field | Type | Present in | Notes |
|---|---|---|---|
| `id` (doc id) | string | always | Firestore-generated; e.g. `1kOzccwl` |
| `actor` | string | always | `"user"`, `"gemini"` (LLM), `"system"` (rare) |
| `mode` | string | often | **USER INTENT mode** — what the player typed. Only 3 distinct values across 2,464 scenes: `character` (73%), `god` (19%), `think` (7%). NEVER equals `"dialog"` or `"heavydialog"` even when the actual agent is `DialogAgent`/`HeavyDialogAgent`. |
| `text` | string | always | Scene content (markdown narrative + quoted speech) |
| `timestamp` | timestamp/int/float | always | **MIXED TYPES**: `DatetimeWithNanoseconds` in some docs, epoch seconds in others, epoch millis in others. Use the `norm()` helper in the umbrella SKILL. |
| `part` | int | always | Sequence number within the campaign (1-indexed) |
| `debug_info` | dict | gemini only | Agent name, model, system instruction files, code execution results |
| `full_state_updates` | dict | gemini only | Structured state changes this turn |
| `state_updates_audit` | dict | gemini only | Audit trail of state changes |
| `planning_block` | dict | gemini only | Choices offered to player |
| `session_header` | string | gemini only | Lvl/HP/Gold/XP summary block |
| `rewards_box` | dict | gemini only | XP / loot / gold |
| `directives` | dict | gemini only | God mode directive additions/drops |
| `action_resolution` | dict | gemini only | Reinterpretation + mechanics |
| `outcome_resolution` | dict | gemini only | (deprecated alias) |
| `dice_rolls` | list | gemini only | Dice roll details |
| `resources` | string | gemini only | HD/spells/etc. formatted |
| `core_memories_snapshot` | dict | gemini only | New memories appended this turn |
| `god_mode_response` | string | gemini only | Free-form god mode answer |

### User-only fields

User entries (`actor=user`) typically have a much smaller doc: `part`, `timestamp`, `text`, `mode`, `actor`. No debug_info, no state updates.

## `debug_info` subfields (the critical analysis surface)

| Field | Type | Notes |
|---|---|---|
| `agent_name` | string | **THE AGENT that wrote this scene.** 13 distinct values observed: HeavyDialogAgent, GodModeAgent, StoryModeAgent, DialogAgent, LevelUpAgent, PlanningAgent, CharacterCreationAgent, FactionManagementAgent, CombatAgent, RewardsAgent, InfoAgent, SpicyModeAgent, CampaignUpgradeAgent |
| `llm_model` | string | `"gemini-3-flash-preview"` is the dominant model (verify per-campaign as model switches happen) |
| `llm_provider` | string | `"google"` / `"openai"` / etc. |
| `system_instruction_char_count` | int | Token size of the system prompt at runtime |
| `system_instruction_files` | list[string] | Filenames of the prompt files loaded (e.g. `["master_directive.md", "game_state_instruction.md", ...]`) |
| `code_execution_used` | bool | Whether code_execution was invoked for dice |
| `dice_seed_commitment` / `dice_server_seed` | string | Dice RNG seed (commit-reveal scheme) |
| `rng_verified` / `rng_detection_ms` | bool/int | RNG commitment verification |
| `json_parsing_ms` | float | Time spent parsing LLM JSON output |
| `parsing_duration_ms` | float | Total parse time |
| `_state_update_schema_gate_errors` | list | Schema gate failures (post-validation) |

## The mode vs agent_name trap

**Critical.** The `story_doc.mode` field is the **user's intent mode** at the time of the input. It does NOT identify which agent wrote the response. Example from 2026-07-13:

- A user types `"the king agrees to my offer"` while in dialog → `mode=character`, `actor=gemini`
- LLM routes this to HeavyDialogAgent (because `matches_game_state` is true) → `debug_info.agent_name="HeavyDialogAgent"`
- The persisted story doc has `mode=character` AND `debug_info.agent_name=HeavyDialogAgent`
- A naive analysis grouping by `mode` would put this scene in the "character mode" bucket, missing that HeavyDialogAgent wrote it

For ANY cross-campaign analysis, group by `debug_info.agent_name`, not `mode`.

## `game_state` subcollection reference (for per-campaign PC/NPC resolution)

Path: `users/{uid}/campaigns/{cid}/game_states/current_state`

| Field | Type | Notes |
|---|---|---|
| `player_character_data.name` | string | PC name. Required for NAME_COLON/VERB_DIALOG attribution. **Some campaigns have None here (character creation not finalized).** |
| `player_character_data` | dict | PC stats/features/equipment/relationships. **No personality fields (motivation, fear, speech patterns).** |
| `npc_data` | dict | Keyed by NPC name. Each entry: `level`, `role`, `relationships`, sometimes `mbti` / `alignment` (labels only, no deep profile). |
| `custom_campaign_state.core_memories` | list[string] | Narrative milestone strings |
| `custom_campaign_state.active_missions` | list[dict] | `{mission_id, objective, status, title}` |
| `custom_campaign_state.active_constraints` | list | In-world constraints |
| `custom_campaign_state.faction_minigame` | dict | Faction minigame state |
| `custom_campaign_state.god_mode_directives` | list | Player-issued directives (newest first) |
| `npc_agendas` | dict | Often empty dict even in long campaigns |
| `combat_state` | dict | Current encounter |

## Field drift across schema versions

Older campaigns may use these legacy field names. **Always use the fallback chain pattern**:

```python
text = (d.get("scene_text") or d.get("narrative_text") or d.get("text") or
        d.get("content") or d.get("narrative") or d.get("response") or "")
ts = (d.get("timestamp") or d.get("created_at") or d.get("ts") or d.get("time"))
```

The campaign `WlfgzI0ReBrFkmagW3wU` (Nocturne bg3 v5 succubus copy, 554 entries on disk) is known to have older schema drift. If `firestore_service.get_campaign_by_id` returns 0 entries for it, fall back to direct `db.collection(...).story.stream()` — see `download-campaign` Pitfall #8.