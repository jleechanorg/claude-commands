# Milestone 0.4: Alternative Approach Evaluation - Structured Generation

## Overview

Building on the success of Milestone 0.3 (validation prototype), this milestone evaluates whether we can **prevent** narrative desynchronization through structured generation rather than **detecting** it post-generation.

## Key Insight from DungeonLM

DungeonLM uses Pydantic schemas to enforce strict data structures:
- Character: id, name, race, class, level, hp, stats, inventory, etc.
- Location: id, name, description, connected_locations, npcs, items

We can adopt a similar approach for WorldArchitect.AI.

## Approach 1: Explicit Schema Injection

### 1.1 Create Pydantic Models for Game Entities

```python
# mvp_site/schemas/entities.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Character(BaseModel):
    """Structured character representation."""
    id: str
    name: str
    race: str
    character_class: str
    level: int = Field(ge=1, le=20)
    hp: int = Field(ge=0)
    max_hp: int = Field(ge=1)
    status: List[str] = []  # ["conscious", "hidden", "injured", etc.]
    location: str
    inventory: List[str] = []
    
class Location(BaseModel):
    """Structured location representation."""
    id: str
    name: str
    description: str
    characters_present: List[str] = []  # Character IDs
    npcs_present: List[str] = []
    items: List[str] = []
    exits: Dict[str, str] = {}  # direction -> location_id

class SceneManifest(BaseModel):
    """Complete scene state for narrative generation."""
    location: Location
    player_characters: List[Character]
    npcs: List[Character]
    timestamp: str
    narrative_constraints: List[str] = []
```

### 1.2 Modify Prompts to Include Schema

```python
# prompts/structured_generation/system_with_schema.md
You are a Game Master for D&D 5e. You MUST generate narratives that accurately reflect the provided scene state.

## SCENE MANIFEST (Required Elements)
The following JSON represents the current scene. ALL characters listed MUST be acknowledged in your narrative:

```json
{
  "location": {
    "name": "Kaelan's Cell",
    "description": "A dank prison cell with stone walls",
    "characters_present": ["gideon_001", "rowan_001"]
  },
  "player_characters": [
    {
      "id": "gideon_001",
      "name": "Gideon",
      "race": "Human",
      "character_class": "Fighter",
      "hp": 45,
      "max_hp": 50,
      "status": ["conscious", "armed"]
    },
    {
      "id": "rowan_001", 
      "name": "Rowan",
      "race": "Elf",
      "character_class": "Cleric",
      "hp": 30,
      "max_hp": 35,
      "status": ["conscious", "preparing_spell"]
    }
  ]
}
```

## VALIDATION REQUIREMENTS
Your narrative MUST:
1. Mention ALL characters by name at least once
2. Reflect their current HP status (injured if <50%)
3. Take place in the specified location
4. Account for character statuses (hidden, unconscious, etc.)
```

## Approach 2: Structured Output Format

### 2.1 Force Structured Narrative Sections

```python
# prompts/structured_generation/structured_output.md
Generate your response in the following format:

## Character Acknowledgment
[List each character and their current action]
- Gideon: [action/state]
- Rowan: [action/state]

## Scene Description
[Narrative describing the scene and character interactions]

## Entity Status Update
[Any changes to character states]
```

### 2.2 XML-Based Structure

```xml
<narrative>
  <scene_setup>
    <location>Kaelan's Cell</location>
    <present_characters>
      <character name="Gideon" status="ready for combat"/>
      <character name="Rowan" status="preparing healing spell"/>
    </present_characters>
  </scene_setup>
  
  <narrative_content>
    The dank cell echoed with...
  </narrative_content>
  
  <validation_check>
    <character_mentioned name="Gideon">true</character_mentioned>
    <character_mentioned name="Rowan">true</character_mentioned>
  </validation_check>
</narrative>
```

## Approach 3: Chain-of-Thought Entity Tracking

### 3.1 Pre-Narrative Planning

```python
# prompts/structured_generation/chain_of_thought.md
Before generating the narrative, complete this checklist:

<think>
1. Who is present? List all characters:
   - Gideon (Fighter, 45/50 HP, armed)
   - Rowan (Cleric, 30/35 HP, preparing spell)

2. Where are we? Kaelan's Cell - prison setting

3. What must be included?
   - Both characters must be mentioned
   - Location must be clear
   - HP status should influence descriptions
</think>

Now generate the narrative ensuring all entities are included...
```

## Testing Framework

### Test Scenarios
1. **Basic Presence**: 2 characters in simple scene
2. **Combat Chaos**: 5+ characters in active combat  
3. **Hidden Characters**: Mix of visible/hidden entities
4. **Location Transitions**: Characters entering/leaving
5. **Status Effects**: Unconscious, invisible, polymorphed

### Metrics to Measure
- **Desync Rate**: % of narratives missing entities
- **Generation Time**: Impact on response latency
- **Token Usage**: Cost implications
- **Narrative Quality**: Subjective assessment
- **Flexibility**: Ability to handle edge cases

### Comparison Matrix

| Approach | Desync Rate | Performance | Quality | Complexity |
|----------|-------------|-------------|---------|------------|
| Validation (0.3) | <5% | +0.27ms | High | Medium |
| Schema Injection | TBD | TBD | TBD | Low |
| Structured Output | TBD | TBD | TBD | Medium |
| Chain-of-Thought | TBD | TBD | TBD | Low |

## Implementation Steps

### Week 1: Schema Development & Integration
1. Create Pydantic models for all game entities
2. Build schema generation from current game_state
3. Integrate schema into prompt templates
4. Create 20 test scenarios with ground truth

### Week 2: Testing & Analysis
5. Test each approach on all scenarios
6. Measure desync rates and performance
7. Conduct quality assessments
8. Generate comparison report
9. Make recommendation for production

## Success Criteria
- At least one approach achieves <5% desync rate
- Performance impact <10ms per generation
- Narrative quality remains high
- Implementation complexity is manageable

## Deliverables
1. `schemas/entities.py` - Pydantic models
2. `prompts/structured_generation/` - Modified prompts
3. `analysis/structured_generation_results.md` - Test results
4. `analysis/approach_comparison.md` - Final recommendation

## Key Questions to Answer
1. Can structured generation match validation's <5% desync rate?
2. Is the performance/quality trade-off acceptable?
3. Which approach is most maintainable?
4. Should we use prevention, detection, or both?