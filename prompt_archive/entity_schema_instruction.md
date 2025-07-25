# Entity Schema Protocol - D&D 5E SRD

This protocol defines the standardized entity structure for all characters, NPCs, locations, and other game entities using **D&D 5E System Reference Document (SRD) rules**. Adherence to this schema ensures consistent entity tracking and state management.

## D&D 5E Core System Rules

### Character Attributes (The Big Six)
- **STR** (Strength) - Physical power, melee attacks, carrying capacity
- **DEX** (Dexterity) - Agility, ranged attacks, AC, initiative
- **CON** (Constitution) - Health, hit points, concentration
- **INT** (Intelligence) - Reasoning, investigation, knowledge
- **WIS** (Wisdom) - Perception, insight, awareness
- **CHA** (Charisma) - Social skills, persuasion, deception

### Core Mechanics
- **Ability Checks**: 1d20 + ability modifier + proficiency (if applicable)
- **Saving Throws**: 1d20 + ability modifier + proficiency (if proficient)
- **Attack Rolls**: 1d20 + ability modifier + proficiency bonus
- **Damage**: Weapon die + ability modifier
- **Armor Class**: 10 + DEX modifier + armor bonus
- **Hit Points**: Hit Die + CON modifier per level
- **Proficiency Bonus**: +2 (levels 1-4), +3 (levels 5-8), +4 (levels 9-12), etc.

### Combat Mechanics
- **Initiative**: 1d20 + DEX modifier
- **Attack Roll**: 1d20 + STR/DEX + proficiency
- **Damage Roll**: Weapon damage + STR/DEX modifier
- **Critical Hit**: Natural 20, roll damage dice twice

### Death and Dying
- **0 HP**: Unconscious and making death saving throws
- **Death Saves**: 1d20, 10+ is success, need 3 successes to stabilize
- **Massive Damage**: If damage ≥ max HP, instant death

### Social Interaction Rules
- **Persuasion**: CHA + proficiency (if proficient)
- **Deception**: CHA + proficiency (if proficient)
- **Intimidation**: CHA + proficiency (if proficient)
- **Insight**: WIS + proficiency (if proficient)

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
  "level": 3,
  "class": "Fighter",
  "background": "Soldier",
  "alignment": "Lawful Good",
  "mbti": "INFJ",

  "hp_current": 28,
  "hp_max": 28,
  "temp_hp": 0,
  "armor_class": 16,

  "attributes": {
    "strength": 16,
    "dexterity": 14,
    "constitution": 15,
    "intelligence": 12,
    "wisdom": 13,
    "charisma": 10
  },

  "proficiency_bonus": 2,
  "skills": ["Athletics", "Perception", "Insight"],
  "saving_throw_proficiencies": ["Strength", "Constitution"],

  "resources": {
    "gold": 150,
    "inspiration": false,
    "hit_dice": {"used": 1, "total": 3},
    "spell_slots": {
      "level_1": {"used": 0, "total": 2},
      "level_2": {"used": 1, "total": 1}
    }
  },

  "equipment": {
    "weapons": ["Longsword", "Shield"],
    "armor": "Chain Mail",
    "backpack": ["Rope (50 feet)", "Rations (5 days)"],
    "money": "150 gp"
  },

  "combat_stats": {
    "initiative": 2,
    "speed": 30,
    "passive_perception": 13
  },

  "status_conditions": [],
  "death_saves": { "successes": 0, "failures": 0 },

  "features": ["Fighting Style: Defense", "Second Wind", "Action Surge"],
  "spells_known": []
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
    "class": "Noble",
    "hp_current": 65,
    "hp_max": 65,
    "armor_class": 15,

    "attributes": {
      "strength": 13,
      "dexterity": 12,
      "constitution": 14,
      "intelligence": 16,
      "wisdom": 15,
      "charisma": 18
    },

    "combat_stats": {
      "initiative": 1,
      "speed": 30,
      "passive_perception": 15
    },

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
7. **D&D 5E SRD Authority** - All attributes, mechanics, and stats follow standard D&D 5E rules
8. **Use standard D&D attributes** - Always use strength, dexterity, constitution, intelligence, wisdom, charisma
9. **Calculate modifiers correctly** - Ability modifier = (attribute - 10) / 2 (rounded down)

## Entity Manifest Integration

The system will automatically generate a Scene Manifest from your state updates, tracking:
- Which entities are present in the current location
- Which entities should be mentioned in the narrative (visible & conscious only)
- Combat participants and turn order
- Environmental conditions

Your narrative should acknowledge all expected entities unless they are hidden or invisible.

## World Time Schema

Track in-game time progression with this structure:

```json
"world_time": {
  "year": 1492,
  "month": "Ches",
  "day": 20,
  "hour": 9,
  "minute": 51,
  "second": 10
}
```

## Custom Campaign State Schema

The `custom_campaign_state` object tracks narrative progress and campaign configuration:

```json
"custom_campaign_state": {
  "premise": "Campaign premise/description",
  "attribute_system": "dnd",
  "session_number": 1,
  "active_missions": [
    {
      "mission_id": "main_quest_1",
      "title": "Defeat the Dark Lord",
      "status": "in_progress",
      "objective": "Find the ancient sword",
      "description": "The Dark Lord threatens the realm..."
    }
  ],
  "completed_missions": [
    {
      "mission_id": "tutorial_1",
      "title": "Learn Combat",
      "status": "completed",
      "completion_date": "Day 15"
    }
  ],
  "core_memories": [
    "Met King Theron in the throne room",
    "Learned about the dragon threat",
    "Accepted the quest to save the kingdom"
  ]
}
```

### Mission Object Schema
- **`mission_id`**: Unique string identifier
- **`title`**: Human-readable mission title
- **`status`**: "accepted", "in_progress", "completed", "failed"
- **`objective`**: Current next step description
- **`description`**: Detailed mission background (optional)

## Game State Management Fields

### Required Top-Level Fields
```json
{
  "game_state_version": 1,
  "player_character_data": { /* per schema above */ },
  "npc_data": { /* per schema above */ },
  "world_data": {
    "current_location_name": "Royal Throne Room",
    "kingdom": "Eldoria",
    "political_situation": "The kingdom faces threats...",
    "locations": { /* location data per schema above */ }
  },
  "world_time": { /* per schema above */ },
  "custom_campaign_state": { /* per schema above */ },
  "migration_status": "FRESH_INSTALL"
}
```

### Data Integrity Requirements
- **`string_id`**: Every entity must have unique identifier
- **`mbti`**: All characters (PC and major NPCs) must have MBTI personality type
- **`attribute_system`**: Must be set in custom_campaign_state (default: "dnd")
- **`game_state_version`**: Track for data migration purposes
