# Response to PR Comments

## Comment 1: "Use the actual real prompts we send to the LLM"
✅ **ADDRESSED** - Changed to use `TEST_SELECTED_PROMPTS = ['narrative', 'mechanics']` representing all checkboxes checked.

## Comment 2: "Get the dragon knight campaign right first"
✅ **ADDRESSED** - We did exactly this approach:
1. First got Dragon Knight tests working correctly
2. Then refactored to create shared base class
3. Finally added Astarion tests using the shared code

## Comment 3: "Stop these inline imports"
✅ **ADDRESSED** - All imports moved to top of files per project rules:
- No imports inside functions
- No conditional imports
- All at module level

## Comment 4: "Aren't there other entity names? Should we sanitize them all?"
✅ **ALREADY IMPLEMENTED** - Investigation shows we're already sanitizing ALL entity names:

```python
# Player Characters (line 500)
pc_entity_id = f"pc_{sanitize_entity_name_for_id(pc_name)}_001"

# NPCs (line 521)
npc_entity_id = f"npc_{sanitize_entity_name_for_id(npc_key)}_{idx+1:03d}"
```

## How the LLM Knows Original Names

The system uses a dual approach:
- **entity_id**: Sanitized for system use (`"npc_cazadors_spawn_001"`)
- **display_name**: Original name for LLM/narrative (`"Cazador's Spawn"`)

Example from the code:
```python
npc = NPC(
    entity_id=npc_entity_id,  # Sanitized: "npc_cazadors_spawn_001"
    display_name=npc_display_name,  # Original: "Cazador's Spawn"
    # ... other fields
)
```

The LLM sees and uses display names in narratives while the system validates using sanitized IDs.