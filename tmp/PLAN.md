# Dynamic Time Pressure System Implementation Plan

## Overview
Implement a living world system where time advances realistically, NPCs act autonomously, and player inaction has meaningful consequences.

## Task Breakdown

### Task 1: Create Failing Tests for Time Pressure Features
**File**: `mvp_site/test_time_pressure.py`
**Requirements**:
- Test that time-sensitive events are tracked in game state
- Test that NPC agendas progress over time
- Test that missed deadlines trigger consequences
- Test that warnings are generated at appropriate urgency levels
- Test that world resources deplete over time
- Test that rest periods advance time appropriately

**Success Criteria**: All tests fail initially (red state)

### Task 2: Implement Time Pressure Protocol in Narrative System
**File**: `mvp_site/prompts/narrative_system_instruction.md`
**Requirements**:
- Add "Time Pressure Protocol" section after "Immersive Narration" section
- Include rules for:
  - Tracking time passage for all actions
  - Generating time-based warnings
  - Describing background NPC activities
  - Showing world changes from time passage
  - Calculating rest consequences

**Key Elements**:
```markdown
## Time Pressure Protocol

When time advances in the game world:

1. **Action Time Costs**:
   - Combat: 6 seconds per round
   - Short rest: 1 hour
   - Long rest: 8 hours
   - Travel: Based on distance and terrain
   - Investigation/social: 10-30 minutes

2. **Background Updates**:
   - NPCs progress their agendas
   - World events unfold
   - Resources deplete
   - Threats escalate

3. **Warning System**:
   - 3+ days before deadline: Subtle hints
   - 1-2 days: Clear warnings
   - <1 day: Urgent alerts
   - Missed: Immediate consequences
```

### Task 3: Implement Time Tracking in Game State
**File**: `mvp_site/prompts/game_state_instruction.md`
**Requirements**:
- Add new state structures after "Mission System" section:
  - `time_sensitive_events`: Track events with deadlines
  - `npc_agendas`: Track NPC goals and progress
  - `world_resources`: Track depleting resources
  - `time_pressure_warnings`: Track warnings given

**Schema**:
```json
{
  "time_sensitive_events": {
    "event_id": {
      "description": "Rescue kidnapped merchant",
      "deadline": {
        "year": 1492,
        "month": "Ches",
        "day": 25,
        "hour": 18
      },
      "consequences": "Merchant will be sold to slavers",
      "urgency_level": "high",
      "warnings_given": 0,
      "related_npcs": ["Merchant Elara", "Bandit Leader"]
    }
  },
  "npc_agendas": {
    "Bandit Leader": {
      "current_goal": "Sell captured merchant to slavers",
      "progress_percentage": 60,
      "next_milestone": {
        "day": 23,
        "description": "Contact slaver network"
      },
      "blocking_factors": ["PC interference", "guard patrols"]
    }
  },
  "world_resources": {
    "village_food_supply": {
      "current_amount": 75,
      "depletion_rate": 5,
      "depletion_unit": "per_day",
      "critical_level": 20,
      "consequence": "Villagers start leaving"
    }
  }
}
```

### Task 4: Integration Requirements
**Success Criteria**:
- Time advances appropriately for all actions
- NPCs act autonomously in background
- Players receive clear warnings about time-sensitive events
- Consequences trigger when deadlines are missed
- World feels alive and dynamic

## Testing Scenarios

1. **Kidnapped Merchant**: 3-day deadline to rescue before sold
2. **Plague Outbreak**: Village needs cure within 5 days
3. **Siege Preparation**: Defend town in 7 days
4. **Resource Depletion**: Food runs out in 10 days

## Implementation Order
1. Write failing tests first (TDD)
2. Update narrative system instruction
3. Update game state instruction
4. Run tests to verify green state
5. Integration testing with full scenarios