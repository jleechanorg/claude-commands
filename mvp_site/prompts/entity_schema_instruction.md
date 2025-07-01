# Entity Schema Protocol

This protocol defines the standardized entity structure for all characters, NPCs, locations, and other game entities. Adherence to this schema ensures consistent entity tracking and state management.

## Entity ID Format

All entities MUST have a unique `string_id` following this format:
- **Player Characters**: `pc_{name}_{sequence}` (e.g., `pc_kaelan_001`)
- **NPCs**: `npc_{name}_{sequence}` (e.g., `npc_theron_001`)
- **Locations**: `loc_{name}_{sequence}` (e.g., `loc_throneroom_001`)
- **Items**: `item_{name}_{sequence}` (e.g., `item_excalibur_001`)
- **Factions**: `faction_{name}_{sequence}` (e.g., `faction_rebels_001`)

The sequence number should be zero-padded to 3 digits (001, 002, etc.).

## Core Entity Structure

### Player Character Data Schema

Every player character MUST include these fields in `player_character_data`:

```json
{
  "string_id": "pc_name_001",
  "name": "Character Name",
  "archetype": "Character concept/archetype",
  "level": 1,
  "xp_current": 0,
  "xp_next_level": 300,
  "alignment": "Lawful Good",
  "mbti": "INFJ",
  "class_concept": "Fighter (Vanguard)",
  
  "hp_current": 10,
  "hp_max": 10,
  "temp_hp": 0,
  
  "aptitudes": {
    "Physique": { "score": 10, "modifier": 0, "potential": 3 },
    "Coordination": { "score": 10, "modifier": 0, "potential": 3 },
    "Health": { "score": 10, "modifier": 0, "potential": 3 },
    "Intelligence": { "score": 10, "modifier": 0, "potential": 3 },
    "Wisdom": { "score": 10, "modifier": 0, "potential": 3 },
    "Charisma": { "score": 10, "modifier": 0, "potential": 3 }
  },
  
  "resources": {
    "gold": 0,
    "inspiration": false,
    "hero_points": 0
  },
  
  "inventory": {
    "equipped": {},
    "backpack": {},
    "stored": {}
  },
  
  "knowledge": [],
  "core_memories": [],
  "recent_decisions": [],
  
  "status_conditions": [],
  "death_saves": { "successes": 0, "failures": 0 }
}
```

### NPC Data Schema

NPCs in `npc_data` should be stored by their display name as the key, with this structure:

```json
{
  "King Theron": {
    "string_id": "npc_theron_001",
    "role": "King of Eldoria",
    "faction": "faction_royalty_001",
    "mbti": "ISFP",
    "attitude_to_party": "neutral",
    
    "level": 10,
    "hp_current": 50,
    "hp_max": 50,
    
    "present": true,
    "conscious": true,
    "hidden": false,
    "status": "Concerned about kingdom",
    
    "relationships": {
      "pc_kaelan_001": "cautious respect"
    },
    
    "knowledge": ["kingdom politics", "dragon threat"],
    "recent_actions": ["summoned heroes", "offered quest"]
  }
}
```

### Location Data Schema

Locations should be tracked with connections and present entities:

```json
{
  "current_location": "loc_throneroom_001",
  "locations": {
    "loc_throneroom_001": {
      "display_name": "Royal Throne Room",
      "description": "A grand hall with marble columns",
      "connected_to": ["loc_hallway_001", "loc_chambers_001"],
      "entities_present": ["npc_theron_001", "npc_guard_001"],
      "environmental_effects": ["dim lighting", "echo"]
    }
  }
}
```

## Entity Status and Visibility

### Status Conditions
Entities can have multiple status conditions from this list:
- `conscious` - Normal, active state
- `unconscious` - Knocked out but alive
- `dead` - Deceased
- `hidden` - Actively concealing
- `invisible` - Magically unseen
- `paralyzed` - Unable to move
- `stunned` - Temporarily incapacitated

### Visibility States
- `visible` - Can be seen normally
- `hidden` - Concealed but can be detected
- `invisible` - Cannot be seen without special means
- `obscured` - Partially visible
- `darkness` - In area of darkness

## State Update Examples

When creating new NPCs:
```json
[STATE_UPDATES_PROPOSED]
{
  "npc_data": {
    "Guard Captain": {
      "string_id": "npc_guardcaptain_001",
      "role": "Captain of the Royal Guard",
      "mbti": "ESTJ",
      "level": 7,
      "hp_current": 45,
      "hp_max": 45,
      "present": true,
      "attitude_to_party": "suspicious"
    }
  }
}
[END_STATE_UPDATES_PROPOSED]
```

When updating entity relationships:
```json
[STATE_UPDATES_PROPOSED]
{
  "npc_data": {
    "King Theron": {
      "attitude_to_party": "friendly",
      "relationships": {
        "pc_kaelan_001": "trusted ally"
      }
    }
  }
}
[END_STATE_UPDATES_PROPOSED]
```

## Critical Rules

1. **Always include string_id** when creating new entities
2. **Maintain consistency** - once an entity has a string_id, never change it
3. **Use present/hidden/conscious flags** to track entity availability
4. **Track relationships** between entities using their string_ids
5. **Delete defeated enemies** using `"__DELETE__"` to remove them completely
6. **Update hp_current** for damage, never modify hp_max unless level changes

## Entity Manifest Integration

The system will automatically generate a Scene Manifest from your state updates, tracking:
- Which entities are present in the current location
- Which entities should be mentioned in the narrative (visible & conscious only)
- Combat participants and turn order
- Environmental conditions

Your narrative should acknowledge all expected entities unless they are hidden or invisible.