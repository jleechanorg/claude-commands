# Context Components Reference

**Status**: Active
**Last Updated**: 2025-12-04
**Related**: `docs/context_budget_design.md`, Bead WA-1

This document provides a comprehensive reference for every component that makes up the LLM context in WorldArchitect.AI, including target token allocations and code pointers.

---

## Quick Reference: Token Budget Allocation

```
Model Context Window (100%)
└── Safe Budget (90% - CONTEXT_WINDOW_SAFETY_RATIO)
    ├── Output Reserve (20% - OUTPUT_TOKEN_RESERVE_RATIO)
    └── Max Input Allowed (80%)
        ├── Scaffold Components (~15-20% of input)
        │   ├── System Instruction: 5,000-8,000 tokens
        │   ├── Checkpoint Block: 1,000-2,000 tokens
        │   ├── Core Memories: 2,000-3,000 tokens
        │   ├── Sequence IDs: 200-500 tokens
        │   └── Game State JSON: 2,000-4,000 tokens
        │
        ├── Entity Tracking Reserve: 10,500 tokens (fixed)
        │   ├── Entity Preload Text: 2,000-3,000 tokens
        │   ├── Entity Instructions: 1,500-2,000 tokens
        │   ├── Entity Tracking Rules: 1,000-1,500 tokens
        │   └── Timeline Log: 3,000-4,000 tokens
        │
        └── Story Budget (remaining ~50-60%)
            ├── Start Turns: 25% (STORY_BUDGET_START_RATIO)
            ├── Middle Summary: 10% (STORY_BUDGET_MIDDLE_RATIO)
            ├── End Turns: 60% (STORY_BUDGET_END_RATIO)
            └── Reserved: 5% (safety margin)
```

---

## 1. Scaffold Components

These are static or semi-static parts of the prompt that don't change based on story length.

### 1.1 System Instruction

**Target**: 5,000-8,000 tokens
**Code Location**: `llm_service.py:600-656` (`InstructionBuilder.build_core_system_instructions`)

| Sub-component | File | Target Tokens |
|---------------|------|---------------|
| Narrative Instruction | `prompts/narrative_system_instruction.md` | ~2,000-3,000 |
| Mechanics Instruction | `prompts/mechanics_system_instruction.md` | ~1,500-2,000 |
| Game State Instruction | `prompts/game_state_instruction.md` | ~1,000-1,500 |
| World Content | Dynamic from `world_loader.py` | ~500-1,500 |
| Debug Instructions | `llm_service.py:812` | ~200-500 |

**Assembly Code**:
```python
# llm_service.py:600
def build_core_system_instructions(self) -> list[str]:
    parts = []
    parts.append(_load_instruction_file(constants.PROMPT_TYPE_NARRATIVE))
    parts.append(_load_instruction_file(constants.PROMPT_TYPE_MECHANICS))
    parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))
    _add_world_instructions_to_system(parts)
    return parts
```

### 1.2 Checkpoint Block

**Target**: 1,000-2,000 tokens
**Code Location**: `llm_service.py:858-910` (`_get_static_prompt_parts`)

The checkpoint block contains:
- Session continuity markers
- Last known game state references
- Story consistency checkpoints

**Assembly Code**:
```python
# llm_service.py:858
def _get_static_prompt_parts(
    game_state: GameState | None,
    story_context: list[dict[str, Any]],
) -> tuple[str, str, str]:
    # Returns (checkpoint_block, core_memories_summary, sequence_id_list)
```

### 1.3 Core Memories Summary

**Target**: 2,000-3,000 tokens
**Code Location**: `llm_service.py:658-740`

| Sub-component | Method | Target Tokens |
|---------------|--------|---------------|
| Companion Instruction | `build_companion_instruction()` | ~1,000-1,500 |
| Background Summary | `build_background_summary_instruction()` | ~1,000-1,500 |

**Assembly Code**:
```python
# llm_service.py:658
def build_companion_instruction(self) -> str:
    # Builds companion info from game_state.companions

# llm_service.py:706
def build_background_summary_instruction(self) -> str:
    # Builds story summary from game_state.story
```

### 1.4 Sequence ID List

**Target**: 200-500 tokens
**Code Location**: `llm_service.py:858-910`

Tracks turn sequence numbers for story continuity.

### 1.5 Game State JSON

**Target**: 2,000-4,000 tokens
**Code Location**: `llm_service.py:2874-2877`

Serialized JSON of the current game state including:
- Player character stats
- Inventory
- Quest progress
- Location data
- Combat state

**Assembly Code**:
```python
# llm_service.py:2874
serialized_game_state: str = json.dumps(
    current_game_state.to_dict(), indent=2, default=json_default_serializer
)
```

---

## 2. Entity Tracking Reserve

These components are added **after** story truncation, so tokens must be pre-reserved.

**Total Reserve**: 10,500 tokens (`ENTITY_TRACKING_TOKEN_RESERVE`)
**Code Location**: `llm_service.py:213-219`, `llm_service.py:2879-2926`

### 2.1 Entity Preload Text

**Target**: 2,000-3,000 tokens
**Code Location**: `entity_preloader.py`

Pre-loads NPC summaries and entity context for the current scene.

```python
# llm_service.py:2902
entity_preload_text = entity_preloader.create_entity_preload_text(
    game_state_dict, session_number, turn_number, current_location
)
```

### 2.2 Entity Specific Instructions

**Target**: 1,500-2,000 tokens
**Code Location**: `instruction_generator.py`

Per-turn instructions for entity behavior and interactions.

```python
# llm_service.py:2908
entity_instructions = instruction_generator.generate_entity_instructions(
    entities=expected_entities,
    player_references=player_references,
    location=current_location,
    story_context=timeline_log_string,
)
```

### 2.3 Entity Tracking Instruction

**Target**: 1,000-1,500 tokens
**Code Location**: `llm_service.py:2884`

Rules and format for entity tracking in responses.

```python
# llm_service.py:2884
_, expected_entities, entity_tracking_instruction = _prepare_entity_tracking(
    current_game_state, truncated_story_context, session_number
)
```

### 2.4 Timeline Log

**Target**: 3,000-4,000 tokens
**Code Location**: `llm_service.py:912-935`

Chronological summary of story events for continuity.

```python
# llm_service.py:912
def _build_timeline_log(story_context: list[dict[str, Any]]) -> str:
    # Builds timeline from truncated story context
```

---

## 3. Story Budget

The story context is the main variable component that gets compacted based on available budget.

**Location**: `llm_service.py:1741-1890` (`_truncate_context`)

### 3.1 Start Turns

**Target**: 25% of story budget (`STORY_BUDGET_START_RATIO`)
**Maximum**: 20 turns (`TURNS_TO_KEEP_AT_START`)
**Minimum**: 3 turns (`ABS_MIN_START`)

Purpose: Context setup, campaign beginning, character introductions.

### 3.2 Middle Summary (Compacted)

**Target**: 10% of story budget (`STORY_BUDGET_MIDDLE_RATIO`)
**Code Location**: `llm_service.py:1641-1738` (`_compact_middle_turns`)

Instead of dropping middle turns, key events are extracted and summarized.

**Extraction Keywords** (`MIDDLE_COMPACTION_KEYWORDS`):
- Combat: attack, hit, damage, kill, defeat, victory, died, death
- Discovery: discover, find, found, acquire, obtain, treasure, artifact
- Story: quest, mission, objective, complete, reveal, secret
- Movement: arrive, enter, leave, travel, reach, escape
- Characters: meet, ally, betray, join, hire, recruit
- Events: level, experience, rest, camp, merchant, shop

```python
# llm_service.py:1641
def _compact_middle_turns(
    middle_turns: list[dict[str, Any]],
    max_tokens: int,
) -> dict[str, Any]:
    # Extracts key events from dropped turns
    # Returns system message with compacted summary
```

### 3.3 End Turns

**Target**: 60% of story budget (`STORY_BUDGET_END_RATIO`)
**Maximum**: 20 turns (`TURNS_TO_KEEP_AT_END`)
**Minimum**: 5 turns (`ABS_MIN_END`)

Purpose: Recent actions, current scene context, immediate continuity.

### 3.4 Reserved

**Target**: 5% of story budget

Safety margin for truncation marker and token estimation variance.

---

## 4. Budget Calculation Flow

### Step 1: Get Model Context
```python
# llm_service.py:222
context_tokens = MODEL_CONTEXT_WINDOW_TOKENS.get(model_name, DEFAULT_CONTEXT_WINDOW_TOKENS)
```

### Step 2: Apply Safety Ratio
```python
# llm_service.py:234
safe_tokens = int(context_tokens * CONTEXT_WINDOW_SAFETY_RATIO)  # 90%
```

### Step 3: Reserve Output Tokens
```python
# llm_service.py:267
output_reserve = int(safe_token_budget * OUTPUT_TOKEN_RESERVE_RATIO)  # 20%
max_input_allowed = safe_token_budget - output_reserve  # 80%
```

### Step 4: Calculate Scaffold
```python
# llm_service.py:2836-2841
scaffold_tokens_raw = estimate_tokens(prompt_scaffold)
scaffold_tokens = scaffold_tokens_raw + ENTITY_TRACKING_TOKEN_RESERVE
```

### Step 5: Calculate Story Budget
```python
# llm_service.py:2845
available_story_tokens = max(0, max_input_allowed - scaffold_tokens)
```

### Step 6: Percentage-Based Turn Allocation
```python
# llm_service.py:1593-1595
start_token_budget = int(max_tokens * STORY_BUDGET_START_RATIO)   # 25%
middle_token_budget = int(max_tokens * STORY_BUDGET_MIDDLE_RATIO) # 10%
end_token_budget = int(max_tokens * STORY_BUDGET_END_RATIO)       # 60%
```

---

## 5. Constants Reference

### Global Budget Constants

| Constant | Value | Location |
|----------|-------|----------|
| `CONTEXT_WINDOW_SAFETY_RATIO` | 0.90 | `constants.py` |
| `OUTPUT_TOKEN_RESERVE_RATIO` | 0.20 | `llm_service.py:211` |
| `OUTPUT_TOKEN_RESERVE_COMBAT` | 24,000 | `llm_service.py:209` |
| `OUTPUT_TOKEN_RESERVE_MIN` | 1,024 | `llm_service.py:210` |
| `ENTITY_TRACKING_TOKEN_RESERVE` | 10,500 | `llm_service.py:219` |

### Story Budget Constants

| Constant | Value | Location |
|----------|-------|----------|
| `STORY_BUDGET_START_RATIO` | 0.25 | `llm_service.py:428` |
| `STORY_BUDGET_MIDDLE_RATIO` | 0.10 | `llm_service.py:429` |
| `STORY_BUDGET_END_RATIO` | 0.60 | `llm_service.py:430` |
| `TURNS_TO_KEEP_AT_START` | 20 | `llm_service.py:376` |
| `TURNS_TO_KEEP_AT_END` | 20 | `llm_service.py:377` |

### Model Context Windows

| Model | Context | Safe (90%) | Max Input (80%) |
|-------|---------|------------|-----------------|
| gemini-2.0-flash | 1,000,000 | 900,000 | 720,000 |
| zai-glm-4.6 (Cerebras) | 131,072 | 117,964 | 94,372 |
| qwen-3-235b (Cerebras) | 131,072 | 117,964 | 94,372 |
| llama-3.3-70b (Cerebras) | 65,536 | 58,982 | 47,186 |

---

## 6. Compaction Logic Reference

### 6.1 Truncation Entry Point

```python
# llm_service.py:2861
truncated_story_context = _truncate_context(
    story_context,
    char_budget_for_story,
    model_to_use,
    current_game_state,
    provider_selection.provider,
)
```

### 6.2 Percentage-Based Turn Calculation

```python
# llm_service.py:1580
def _calculate_percentage_based_turns(
    story_context: list[dict[str, Any]],
    max_tokens: int,
) -> tuple[int, int]:
```

### 6.3 Middle Compaction

```python
# llm_service.py:1641
def _compact_middle_turns(
    middle_turns: list[dict[str, Any]],
    max_tokens: int,
) -> dict[str, Any]:
```

### 6.4 Adaptive Reduction Loop

```python
# llm_service.py:1802-1853
while current_start >= min_start and current_end >= min_end:
    # Reduce turns until content fits
    # Prioritize keeping recent context
```

---

## 7. Logging and Debugging

### Budget Logging Format

```
📊 CONTEXT BREAKDOWN: system_instruction=6500tk, checkpoint=1200tk,
   core_memories=2100tk, seq_ids=350tk, game_state=3200tk

📊 BUDGET: model_limit=131072tk, safe_budget=117964tk,
   scaffold=23500tk (raw:13000+entity_reserve:10500),
   output_reserve=23592tk (normal), story_budget=70872tk,
   actual_story=85000tk ⚠️ OVER

📊 PERCENTAGE-BASED TURNS: avg_tokens/turn=2400,
   start_budget=17718tk→7 turns (25%),
   end_budget=42523tk→17 turns (60%),
   middle_budget=7087tk (10% for compaction)

📊 MIDDLE COMPACTION: 30 turns → 12 key events, 1850 tokens
```

---

## 8. Architecture Decisions

### NO AUTO-FALLBACK TO LARGER MODELS

See `docs/context_budget_design.md` and bead WA-1.

Automatic fallback to larger context models was explicitly removed. If `ContextTooLargeError` occurs, the solution is to improve truncation logic, not switch models.

### Middle Compaction Over Dropping

Middle turns are no longer completely dropped. Key events are extracted using keyword matching and preserved in a compacted summary (10% of story budget).

---

## 9. Test Coverage

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_adaptive_truncation.py` | 11 | Truncation + percentage + middle compaction |
| `test_context_truncation.py` | 3 | Legacy behavior |
| `test_output_token_budget_regression.py` | 9 | Budget calculations |

---

## 10. Related Files

| File | Purpose |
|------|---------|
| `mvp_site/llm_service.py` | Main context assembly and truncation |
| `mvp_site/constants.py` | Model context windows, safety ratios |
| `mvp_site/entity_tracking.py` | Entity creation and tracking |
| `mvp_site/entity_preloader.py` | Entity preload text generation |
| `mvp_site/instruction_generator.py` | Entity-specific instructions |
| `mvp_site/world_loader.py` | World content for system instruction |
| `prompts/narrative_system_instruction.md` | Narrative rules |
| `prompts/mechanics_system_instruction.md` | Game mechanics |
| `prompts/game_state_instruction.md` | Game state format |
