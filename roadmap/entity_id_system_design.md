# Entity ID System Design for Narrative Synchronization

## Problem Statement

Current entity tracking relies on string matching of names, which causes several issues:

1. **Name Ambiguity**:
   - Multiple "Guard" NPCs
   - Common names like "Marcus" appearing in different contexts
   - Titles vs names ("The King" vs "King Aldric")

2. **Name Variations**:
   - "Sariel" vs "Sariel Arcanus" vs "Princess Sariel"
   - "Cressida" vs "Lady Cressida" vs "Lady Valeriana"
   - Nicknames and shortened forms

3. **State Tracking**:
   - Same entity in different states (invisible, polymorphed, wounded)
   - Location changes over time
   - Relationship changes

4. **Performance**:
   - Fuzzy string matching is slow
   - False positives from partial matches

## Proposed Solution: Universal Entity ID System

### Entity Types to Track

```python
class EntityType(Enum):
    PLAYER_CHARACTER = "pc"
    NPC = "npc"
    LOCATION = "loc"
    ITEM = "item"
    FACTION = "faction"
    CREATURE = "creature"
    VEHICLE = "vehicle"  # Ships, wagons, etc.
    EFFECT = "effect"    # Ongoing spells, environmental effects
```

### ID Format Options

#### Option 1: UUID-Based
```json
{
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_type": "pc",
  "display_name": "Sariel Arcanus",
  "aliases": ["Sariel", "Princess Sariel", "Lady Arcanus"]
}
```

**Pros**: Globally unique, no collisions
**Cons**: Not human-readable, harder to debug

#### Option 2: Structured IDs (Recommended)
```json
{
  "entity_id": "pc_sariel_001",
  "entity_type": "pc",
  "display_name": "Sariel Arcanus",
  "aliases": ["Sariel", "Princess Sariel", "Lady Arcanus"]
}
```

**Format**: `{type}_{name}_{sequence}`
**Pros**: Human-readable, debuggable, still unique
**Cons**: Need to manage sequences

#### Option 3: Hierarchical IDs
```json
{
  "entity_id": "campaign.sariel_v2.pc.sariel",
  "entity_type": "pc",
  "display_name": "Sariel Arcanus",
  "campaign_id": "sariel_v2",
  "aliases": ["Sariel", "Princess Sariel", "Lady Arcanus"]
}
```

**Format**: `{campaign}.{type}.{name}`
**Pros**: Shows relationships, campaign-scoped
**Cons**: Longer IDs, potential issues with cross-campaign entities

### Enhanced Game State Structure

```python
game_state = {
    "entities": {
        "pc_sariel_001": {
            "entity_id": "pc_sariel_001",
            "entity_type": "pc",
            "display_name": "Sariel Arcanus",
            "aliases": ["Sariel", "Princess Sariel", "Lady Arcanus"],
            "current_location": "loc_chamber_001",
            "status": {
                "hp": 8,
                "hp_max": 8,
                "conditions": ["mourning", "injured_ear"],
                "visibility": "visible"
            },
            "relationships": {
                "npc_cassian_001": "brother",
                "npc_valerius_001": "brother",
                "npc_cressida_001": "friend"
            }
        },
        "npc_cassian_001": {
            "entity_id": "npc_cassian_001",
            "entity_type": "npc",
            "display_name": "Prince Cassian Arcanus",
            "aliases": ["Cassian", "Prince Cassian"],
            "current_location": "loc_chamber_001",
            "status": {
                "emotional_state": "angry",
                "visibility": "visible"
            }
        },
        "loc_chamber_001": {
            "entity_id": "loc_chamber_001",
            "entity_type": "location",
            "display_name": "Sariel's Chambers",
            "aliases": ["the chambers", "your chambers"],
            "connected_to": ["loc_corridor_001", "loc_balcony_001"],
            "entities_present": ["pc_sariel_001", "npc_cassian_001"]
        }
    },
    "active_scene": {
        "location_id": "loc_chamber_001",
        "present_entities": ["pc_sariel_001", "npc_cassian_001"],
        "mentioned_entities": ["npc_titus_001"],  # Referenced but not present
        "focus_entity": "pc_sariel_001"
    }
}
```

### Benefits for Validation

1. **Precise Tracking**: Know exactly which entity should be mentioned
2. **State Awareness**: Track visibility, conditions, locations
3. **Relationship Context**: Understand entity connections
4. **Performance**: Direct ID lookup instead of fuzzy matching

### Validation Enhancement

```python
def validate_narrative_with_ids(narrative: str, game_state: dict) -> ValidationResult:
    """Enhanced validation using entity IDs"""

    active_scene = game_state["active_scene"]
    entities = game_state["entities"]

    # Get entities that MUST be mentioned
    required_entities = []
    for entity_id in active_scene["present_entities"]:
        entity = entities[entity_id]
        # Check visibility
        if entity["status"].get("visibility") != "invisible":
            required_entities.append({
                "id": entity_id,
                "name": entity["display_name"],
                "aliases": entity.get("aliases", [])
            })

    # Validate each entity appears in narrative
    missing = []
    for entity in required_entities:
        # Check main name and all aliases
        found = False
        search_terms = [entity["name"]] + entity.get("aliases", [])

        for term in search_terms:
            if term.lower() in narrative.lower():
                found = True
                break

        if not found:
            missing.append(entity["id"])

    return ValidationResult(
        missing_entities=missing,
        detection_confidence=1.0  # No fuzzy matching needed!
    )
```

### Migration Path

1. **Phase 1**: Add IDs to new campaigns
   - Generate IDs for all entities on campaign creation
   - Store mapping of name -> ID

2. **Phase 2**: Retrofit existing campaigns
   - Analyze existing campaigns to extract entities
   - Generate IDs based on first appearance
   - Create migration script

3. **Phase 3**: Update validators
   - Enhance validators to use IDs when available
   - Fall back to name matching for legacy data

### Implementation Priority

1. **Start with Milestone 0.4**:
   - Add entity IDs to test campaigns
   - Validate improvement in detection accuracy

2. **Extend to combat tracking**:
   - Combat participants get temporary IDs
   - Track "guard_001", "guard_002" separately

3. **Location tracking**:
   - Every location gets an ID
   - Track connected locations for movement

## Example: Sariel Campaign with IDs

### Before (Current State)
```json
{
  "npc_data": {
    "Cassian Arcanus": {
      "name": "Prince Cassian Arcanus",
      "age": 20
    }
  }
}
```

### After (With IDs)
```json
{
  "entities": {
    "npc_cassian_001": {
      "entity_id": "npc_cassian_001",
      "entity_type": "npc",
      "display_name": "Prince Cassian Arcanus",
      "aliases": ["Cassian", "Prince Cassian", "Brother"],
      "first_appearance": "session_1_turn_3",
      "metadata": {
        "age": 20,
        "mbti": "ESTJ",
        "role": "Twin Prince"
      }
    }
  }
}
```

## Next Steps

1. Choose ID format (recommend Option 2: Structured IDs)
2. Update game_state schema to include entities dictionary
3. Create entity registry service
4. Update validators to use IDs
5. Test on Milestone 0.4 campaigns

This system would dramatically improve entity tracking accuracy and enable more sophisticated narrative validation.
