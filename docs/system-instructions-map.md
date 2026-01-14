# System Instructions Map

**Version**: 1.0.0
**Last Updated**: 2025-12-30

This document provides a comprehensive map of all system instructions (prompts) used in WorldArchitect.AI, including their locations, purposes, assembly mechanisms, and invariants that must be preserved.

## Table of Contents

1. [Overview](#overview)
2. [Prompt Files](#prompt-files)
3. [Assembly Mechanisms](#assembly-mechanisms)
4. [Agent Types and Their Prompts](#agent-types-and-their-prompts)
5. [Critical Invariants](#critical-invariants)
6. [Regression Testing Checklist](#regression-testing-checklist)

---

## Overview

WorldArchitect.AI uses a hierarchical system instruction architecture where multiple prompt files are loaded and assembled in a specific order depending on the active agent mode. The `PromptBuilder` class in `mvp_site/agent_prompts.py` is the central orchestrator for this assembly.

### Key Principles

1. **Prompt Hierarchy**: Earlier prompts establish authority over later ones
2. **Agent Specialization**: Different game modes load different prompt combinations
3. **Dynamic Injection**: Game state, directives, and identity blocks are injected at runtime
4. **Living World Triggers**: Background world events are generated every N turns

---

## Prompt Files

### Core Prompts (Always Loaded)

| File | Constant | Purpose |
|------|----------|---------|
| `prompts/master_directive.md` | `PROMPT_TYPE_MASTER_DIRECTIVE` | Loading hierarchy, conflict resolution, naming rules |
| `prompts/game_state_instruction.md` | `PROMPT_TYPE_GAME_STATE` | JSON protocol, state schemas, entity structures |
| `prompts/dnd_srd_instruction.md` | `PROMPT_TYPE_DND_SRD` | D&D 5E rules authority |

### Mode-Specific Prompts

| File | Constant | When Loaded |
|------|----------|-------------|
| `prompts/narrative_system_instruction.md` | `PROMPT_TYPE_NARRATIVE` | Story mode, user selects "narrative" |
| `prompts/mechanics_system_instruction.md` | `PROMPT_TYPE_MECHANICS` | Character creation, leveling, most modes |
| `prompts/character_template.md` | `PROMPT_TYPE_CHARACTER_TEMPLATE` | NPC psychology development |
| `prompts/god_mode_instruction.md` | `PROMPT_TYPE_GOD_MODE` | Administrative commands |
| `prompts/living_world_instruction.md` | `PROMPT_TYPE_LIVING_WORLD` | Every 3 turns (configurable) |
| `prompts/combat_system_instruction.md` | `PROMPT_TYPE_COMBAT` | Active combat encounters |
| `prompts/rewards_system_instruction.md` | `PROMPT_TYPE_REWARDS` | XP/loot distribution |

### Prompt File Locations

All prompt files are stored in `mvp_site/prompts/`:
```
mvp_site/prompts/
├── master_directive.md
├── game_state_instruction.md
├── narrative_system_instruction.md
├── mechanics_system_instruction.md
├── character_template.md
├── dnd_srd_instruction.md
├── god_mode_instruction.md
├── living_world_instruction.md
├── combat_system_instruction.md
└── rewards_system_instruction.md
```

---

## Assembly Mechanisms

### PromptBuilder Class (`mvp_site/agent_prompts.py`)

The `PromptBuilder` class is responsible for assembling system instructions. Key methods:

```python
class PromptBuilder:
    # Core instruction building
    def build_core_system_instructions() -> list[str]  # master_directive, game_state, debug
    def build_god_mode_instructions() -> list[str]     # God mode stack
    def build_info_mode_instructions() -> list[str]    # Trimmed for info queries
    def build_combat_mode_instructions() -> list[str]  # Combat-focused stack
    def build_rewards_mode_instructions() -> list[str] # Rewards processing stack

    # Conditional additions
    def add_character_instructions(parts, selected_prompts)
    def add_selected_prompt_instructions(parts, selected_prompts)
    def add_system_reference_instructions(parts)

    # Dynamic content generation
    def build_companion_instruction() -> str
    def build_background_summary_instruction() -> str
    def build_character_identity_block() -> str        # Name, gender, pronouns
    def build_god_mode_directives_block() -> str       # Player-defined rules
    def build_continuation_reminder() -> str           # Planning blocks, temporal
    def build_living_world_instruction(turn) -> str    # Background events
    def build_arc_completion_reminder() -> str         # Prevents arc revisiting

    # Finalization
    def finalize_instructions(parts, use_default_world) -> str
```

### Loading Order for Story Mode

1. Master Directive (establishes hierarchy)
2. Character Identity Block (if game state exists)
3. God Mode Directives Block (if directives exist)
4. Game State Instruction (JSON protocol)
5. Debug Instructions (dice rolls, state tracking)
6. Character Template (if narrative selected)
7. Narrative Instruction (if selected)
8. Mechanics Instruction (if selected)
9. D&D SRD Instruction
10. Continuation Reminder (temporal enforcement)
11. Living World Instruction (every 3 turns)
12. World Content (if enabled)

### Loading Order for Combat Mode

1. Master Directive
2. Game State Instruction
3. Combat System Instruction
4. Narrative Instruction
5. D&D SRD Instruction
6. Mechanics Instruction
7. Debug Instructions

### Loading Order for God Mode

1. Master Directive
2. God Mode Instruction
3. Game State Instruction
4. D&D SRD Instruction
5. Mechanics Instruction

---

## Agent Types and Their Prompts

### StoryModeAgent (`mvp_site/agents.py`)

**Mode**: `character`

**Required Prompts**:
- `master_directive`
- `game_state`
- `dnd_srd`

**Optional Prompts**:
- `narrative`
- `mechanics`
- `character_template`

### CombatAgent

**Mode**: `combat`

Uses `build_combat_mode_instructions()`:
- master_directive, game_state, combat, narrative, dnd_srd, mechanics, debug

### GodModeAgent

**Mode**: `god`

Uses `build_god_mode_instructions()`:
- master_directive, god_mode, game_state, dnd_srd, mechanics

### InfoAgent

**Mode**: `info`

Uses `build_info_mode_instructions()`:
- master_directive, game_state (trimmed for equipment queries)

### RewardsAgent

**Mode**: `rewards`

Uses `build_rewards_mode_instructions()`:
- master_directive, game_state, rewards, dnd_srd, mechanics, debug

---

## Critical Invariants

These are the behaviors that MUST be preserved and tested for regression:

### 1. State Management

| Invariant | Location | Test Criteria |
|-----------|----------|---------------|
| JSON response structure | `game_state_instruction.md` | Response contains `narrative`, `state_updates`, `planning_block` |
| Player character data | `game_state_instruction.md` | `player_character_data` preserves HP, XP, level, inventory |
| NPC data structure | `game_state_instruction.md` | `npc_data` dict with proper fields (string_id, hp, etc.) |
| Combat state schema | `game_state_instruction.md` | `combat_state` with `combatants`, `initiative_order` |
| God mode directives | `game_state_instruction.md` | `custom_campaign_state.god_mode_directives` persists |

### 2. Living World System

| Invariant | Location | Test Criteria |
|-----------|----------|---------------|
| 3-turn cadence | `living_world_instruction.md` | Living world triggers on turns 3, 6, 9, etc. |
| 4 background events | `living_world_instruction.md` | 3 immediate + 1 long-term per LW turn |
| Event status field | `living_world_instruction.md` | Events have `status`: pending/discovered/resolved |
| Scene events | `living_world_instruction.md` | At least 1 scene_event across 10+ turns |
| Faction updates | `living_world_instruction.md` | Faction movements on LW turns |

### 3. Combat System

| Invariant | Location | Test Criteria |
|-----------|----------|---------------|
| Dice roll requirement | `combat_system_instruction.md` | All attacks require `tool_requests` |
| HP tracking | `combat_system_instruction.md` | `combatants` dict populated with HP/AC |
| Combat end rewards | `combat_system_instruction.md` | XP awarded, loot distributed on combat end |
| Initiative matching | `combat_system_instruction.md` | `initiative_order[].name` matches `combatants` keys |
| Boss equipment | `combat_system_instruction.md` | Boss NPCs have all equipment slots filled |

### 4. Character Identity

| Invariant | Location | Test Criteria |
|-----------|----------|---------------|
| Gender pronouns | `agent_prompts.py` | Character identity block includes gender enforcement |
| Name persistence | `agent_prompts.py` | Character name preserved across requests |
| Relationship tracking | `agent_prompts.py` | Key relationships listed in identity block |

### 5. God Mode Directives

| Invariant | Location | Test Criteria |
|-----------|----------|---------------|
| Directive persistence | `agent_prompts.py` | Directives persist across requests |
| Directive enforcement | `god_mode_instruction.md` | LLM follows directive rules |
| Directive extraction | `world_logic.py` | God mode commands create directives |

### 6. Rewards System

| Invariant | Location | Test Criteria |
|-----------|----------|---------------|
| rewards_processed flag | `rewards_system_instruction.md` | Must be set to prevent duplicate rewards |
| rewards_box field | `rewards_system_instruction.md` | Required when xp_awarded > 0 |
| XP thresholds | `rewards_system_instruction.md` | Correct D&D 5E level thresholds |

---

## Regression Testing Checklist

### Core Functionality Tests

- [ ] **Story continuation produces valid JSON**
  - Response has `narrative` (string)
  - Response has `state_updates` (object)
  - Response has `planning_block` (object with `thinking`, `choices`)

- [ ] **Player character data persists**
  - HP, XP, level unchanged unless modified by action
  - Inventory items preserved
  - Equipment slots maintained

- [ ] **NPC data structure preserved**
  - NPCs have `string_id`, `hp_current`, `hp_max`, `ac`
  - Relationships tracked correctly
  - Location data maintained

### Living World Tests

- [ ] **Living world triggers every 3 turns**
  - Turn 3, 6, 9, etc. include `living_world_instruction.md`
  - Non-LW turns do NOT include living world instruction

- [ ] **Background events generated correctly**
  - 4 events per LW turn (3 immediate + 1 long-term)
  - Events have `event_type` field
  - Events have `status` field (pending/discovered/resolved)

- [ ] **Scene events trigger periodically**
  - At least 1 scene_event across 10+ turns
  - `next_scene_event_turn` tracked in custom_campaign_state

### Combat Tests

- [ ] **Combat state valid on combat start**
  - `in_combat: true`
  - `combat_session_id` present
  - `combatants` dict populated
  - `initiative_order` matches combatants

- [ ] **Combat rewards distributed on end**
  - `in_combat: false`
  - `combat_summary` present
  - XP added to player
  - `rewards_processed: true`

### God Mode Tests

- [ ] **God mode directives persist**
  - Directive added via god mode command
  - Directive appears in subsequent requests
  - Directive influences LLM behavior

- [ ] **God mode commands recognized**
  - `/god` or `[GOD MODE]` triggers god mode agent
  - State corrections applied correctly

### Schema Stability Tests

- [ ] **world_events structure unchanged**
  - `background_events` array present
  - Events have required fields

- [ ] **combat_state structure unchanged**
  - `combatants` dict format stable
  - `initiative_order` array format stable

- [ ] **player_character_data structure unchanged**
  - Level tracking with masked_level and real_level
  - Experience tracking with current XP
  - Equipment with slot keys

---

## Usage in Regression Testing

### Automatic Validation (Zero Code Changes Required)

The `testing_mcp/lib/campaign_utils.py` module automatically validates every response
from `process_action()` without requiring any test code changes. Results are attached
to the response dict.

**Environment Variables:**
- `MCP_INVARIANT_CHECK`: Set to `0` or `false` to disable (default: enabled)
- `MCP_INVARIANT_STRICT`: Set to `1` or `true` to raise AssertionError on breaking changes

**Attached to every response:**
```python
response["_turn_number"]          # Current turn count for this campaign
response["_invariant_validation"] # Validation summary dict
response["_invariant_violations"] # List of violation strings (if any)
```

**Example - No code changes needed:**
```python
from testing_mcp.lib import process_action

# Validation happens automatically!
response = process_action(client, user_id=uid, campaign_id=cid, user_input="Attack goblin")

# Results are attached to the response
print(response["_invariant_validation"]["status"])  # 'pass', 'warn', or 'fail'
print(response["_invariant_violations"])  # ['invariant: violation', ...]
```

**Aggregate results at end of test:**
```python
from testing_mcp.lib import aggregate_validation_summary

responses = [r1, r2, r3, ...]  # Responses from process_action calls
summary = aggregate_validation_summary(responses)
print(summary["overall_status"])  # 'pass', 'warn', or 'fail'
print(summary["all_violations"])  # All violations across all turns
```

### Manual Validation (For Advanced Use)

The `testing_mcp/lib/regression_oracle.py` module provides utilities for:

1. **Compare prior vs current test snapshots**
2. **Classify differences as SAFE, SUSPICIOUS, or BREAKING**
3. **Validate structural invariants**
4. **Generate machine-readable regression reports**

Example usage:
```python
from testing_mcp.lib.regression_oracle import RegressionOracle

oracle = RegressionOracle()
result = oracle.compare_snapshots(prior_snapshot, current_snapshot)
print(result['overall_status'])  # 'pass', 'warn', or 'fail'
```

---

## Related Documentation

- `CLAUDE.md` - Primary rules and operating protocol
- `mvp_site/agent_prompts.py` - PromptBuilder implementation
- `mvp_site/agents.py` - Agent class definitions
- `mvp_site/constants.py` - Prompt type constants
