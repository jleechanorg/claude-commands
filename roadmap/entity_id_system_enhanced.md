# Enhanced Entity ID System Design

## Comprehensive Entity Schema

Building on the original design to include all requested attributes and entity types.

### Core Entity Types

```python
class EntityType(Enum):
    # Characters
    PLAYER_CHARACTER = "pc"
    NPC = "npc"
    CREATURE = "creature"

    # Resources & Items
    RESOURCE = "resource"      # Gold, materials, etc.
    ITEM = "item"              # Equipment, consumables
    CONTAINER = "container"    # Chests, bags

    # Locations & Environment
    LOCATION = "loc"
    SCENE = "scene"
    ENVIRONMENT = "env"        # Weather, time of day

    # Social Structures
    FACTION = "faction"
    ORGANIZATION = "org"

    # Objects
    OBJECT = "obj"             # Main objects
    SUB_OBJECT = "sub_obj"     # Parts of objects

    # Meta
    KNOWLEDGE = "knowledge"    # Facts, secrets, lore
    MEMORY = "memory"         # Character memories
    DECISION = "decision"     # Recent decisions
```

### Enhanced Character Schema

```python
{
    "entity_id": "pc_sariel_001",  # UUID alternative: "550e8400-e29b-41d4-a716-446655440000"
    "entity_type": "pc",
    "display_name": "Sariel Arcanus",
    "aliases": ["Sariel", "Princess Sariel", "Lady Arcanus"],

    # Core Stats
    "level": 5,
    "experience": {
        "current": 6500,
        "to_next_level": 7500
    },

    # Attributes/Stats
    "stats": {
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "intelligence": 16,
        "wisdom": 13,
        "charisma": 18
    },

    # Combat/Health
    "status": {
        "hp": 8,
        "hp_max": 8,
        "ac": 12,
        "conditions": ["mourning", "injured_ear"],
        "visibility": "visible"
    },

    # Resources
    "resources": {
        "gold": 1500,
        "spell_slots": {
            "level_1": {"current": 2, "max": 4},
            "level_2": {"current": 1, "max": 3},
            "level_3": {"current": 0, "max": 2}
        },
        "inspiration": false,
        "hero_points": 1
    },

    # Inventory
    "inventory": {
        "equipped": {
            "weapon": "item_staff_001",
            "armor": "item_robes_001",
            "accessories": ["item_ring_001", "item_amulet_001"]
        },
        "carried": ["item_potion_001", "item_scroll_001"],
        "capacity": {
            "current": 45,
            "max": 80
        }
    },

    # Location & Movement
    "location": {
        "current": "loc_chamber_001",
        "previous": "loc_throne_room_001",
        "home_base": "loc_arcanus_castle_001"
    },

    # Knowledge & Memories
    "knowledge": {
        "facts": ["knowledge_titus_betrayal_001", "knowledge_valerius_sacrifice_001"],
        "secrets": ["knowledge_ancient_ritual_001"],
        "lore": ["knowledge_arcanus_history_001"]
    },

    "core_memories": [
        {
            "memory_id": "memory_valerius_death_001",
            "description": "Watching Valerius sacrifice himself",
            "emotional_weight": "traumatic",
            "session": "session_12"
        }
    ],

    # Recent Decisions (avoid planning block repetitions)
    "recent_decisions": [
        {
            "decision_id": "decision_spare_titus_001",
            "description": "Chose to spare Titus despite betrayal",
            "timestamp": "session_13_turn_45",
            "consequences": ["faction_nobles_reputation_increase"]
        }
    ],

    # Relationships
    "relationships": {
        "npc_cassian_001": {
            "type": "family",
            "subtype": "twin_brother",
            "standing": "strained"
        },
        "npc_cressida_001": {
            "type": "friend",
            "subtype": "confidant",
            "standing": "trusted"
        }
    }
}
```

### Resource Entity Schema

```python
{
    "entity_id": "resource_gold_pile_001",
    "entity_type": "resource",
    "display_name": "Chest of Gold",
    "amount": 5000,
    "resource_type": "currency",
    "location": "loc_treasury_001",
    "owner": "faction_arcanus_001",
    "accessible_by": ["pc_sariel_001", "npc_cassian_001"]
}
```

### Faction Schema

```python
{
    "entity_id": "faction_arcanus_001",
    "entity_type": "faction",
    "display_name": "House Arcanus",
    "aliases": ["Arcanus Family", "The Royal House"],

    # Resources
    "resources": {
        "gold": 50000,
        "soldiers": 500,
        "influence": 85,
        "territory_count": 12
    },

    # Members
    "members": {
        "leaders": ["pc_sariel_001", "npc_cassian_001"],
        "officers": ["npc_commander_001", "npc_advisor_001"],
        "members": ["npc_guard_001", "npc_guard_002"],
        "total_count": 523
    },

    # Controlled Objects/Locations
    "holdings": {
        "locations": ["loc_arcanus_castle_001", "loc_northern_fort_001"],
        "objects": ["obj_throne_001", "obj_crown_001"]
    },

    # Relationships with other factions
    "faction_relations": {
        "faction_merchants_001": "allied",
        "faction_rebels_001": "hostile",
        "faction_church_001": "neutral"
    }
}
```

### Scene Entity Schema

```python
{
    "entity_id": "scene_throne_confrontation_001",
    "entity_type": "scene",
    "display_name": "Throne Room Confrontation",
    "session": "session_13",
    "turn_range": [42, 58],

    # Scene Composition
    "participants": {
        "people": ["pc_sariel_001", "npc_cassian_001", "npc_titus_001"],
        "environment": ["env_throne_room_dark_001"],
        "objects": ["obj_throne_001", "obj_crown_001", "obj_bloodied_sword_001"]
    },

    # Dynamic Elements
    "environment_state": {
        "lighting": "dim_torchlight",
        "weather": "storm_outside",
        "time": "late_night",
        "mood": "tense"
    },

    # Non-living objects in scene
    "static_objects": {
        "obj_throne_001": {
            "state": "occupied_by_cassian",
            "condition": "pristine"
        },
        "obj_crown_001": {
            "state": "on_floor",
            "condition": "bloodstained"
        }
    }
}
```

### Object Hierarchy Schema

```python
{
    "entity_id": "obj_ship_001",
    "entity_type": "object",
    "display_name": "The Brass Compass",
    "object_type": "vehicle",
    "sub_objects": ["sub_obj_mast_001", "sub_obj_helm_001", "sub_obj_deck_001"],

    "properties": {
        "size": "large",
        "condition": "damaged",
        "capacity": {
            "crew": {"current": 15, "max": 30},
            "cargo": {"current": 2000, "max": 5000}
        }
    }
}

{
    "entity_id": "sub_obj_mast_001",
    "entity_type": "sub_object",
    "display_name": "Main Mast",
    "parent_object": "obj_ship_001",
    "condition": "cracked",
    "can_interact": true
}
```

### Knowledge Entity Schema

```python
{
    "entity_id": "knowledge_titus_betrayal_001",
    "entity_type": "knowledge",
    "display_name": "Titus's Betrayal",
    "knowledge_type": "secret",
    "known_by": ["pc_sariel_001", "npc_cassian_001"],
    "details": {
        "fact": "Titus orchestrated Valerius's death",
        "evidence": ["item_letter_001", "memory_overheard_conversation_001"],
        "implications": ["faction_nobles_trust_broken", "decision_required_justice"]
    },
    "discovered": "session_12_turn_89"
}
```

## ID Format Recommendation

### Primary: Structured IDs
`{type}_{name}_{sequence}`
- Example: `pc_sariel_001`, `faction_arcanus_001`
- Human-readable and debuggable
- Easy to identify entity type at a glance

### Alternative: UUID with Type Prefix
`{type}_{uuid}`
- Example: `pc_550e8400-e29b-41d4-a716-446655440000`
- Guaranteed uniqueness
- Still identifies type

### For Sub-objects: Hierarchical
`{parent_id}_{sub_type}_{name}_{sequence}`
- Example: `obj_ship_001_deck_main_001`
- Shows relationship clearly

## Implementation Benefits

1. **Complete State Tracking**: Every aspect of the game world has an ID
2. **Relationship Mapping**: Complex webs of connections are traceable
3. **Decision History**: Recent decisions tracked to avoid repetition
4. **Resource Management**: Clear ownership and access rights
5. **Memory Persistence**: Core memories shape character behavior
6. **Scene Composition**: Full environmental and object tracking

## Validation Improvements

With this system, validators can:
- Track if specific items are mentioned when relevant
- Ensure faction resources are referenced correctly
- Validate that known facts influence dialogue
- Check that recent decisions aren't contradicted
- Verify object states remain consistent
- Ensure sub-objects are referenced with parent context

## Migration Strategy

1. **Phase 1**: Characters and NPCs (highest impact)
2. **Phase 2**: Locations and core objects
3. **Phase 3**: Resources and factions
4. **Phase 4**: Knowledge, memories, and decisions
5. **Phase 5**: Scenes and sub-objects

This comprehensive system would enable near-perfect narrative synchronization and state tracking.
