# Task 3: Implement Time Tracking in Game State

## Objective
Add time tracking structures to the game state instruction to support the time pressure system.

## Requirements

Update file: `mvp_site/prompts/game_state_instruction.md`

### Location
Add new section after "### Mission System" section (around line 195)

### Content to Add

```markdown
### Time Pressure System

Track time-sensitive events, NPC activities, and world resources:

```json
{
  "time_sensitive_events": {
    "rescue_merchant": {
      "description": "Rescue kidnapped merchant from bandits",
      "deadline": {
        "year": 1492,
        "month": "Ches",
        "day": 25,
        "hour": 18,
        "minute": 0
      },
      "consequences": "Merchant will be sold to slavers, trade routes disrupted",
      "urgency_level": "high",
      "warnings_given": 0,
      "related_npcs": ["Elara (Merchant)", "Garrick (Bandit Leader)"],
      "status": "active"
    }
  },
  "npc_agendas": {
    "Garrick (Bandit Leader)": {
      "current_goal": "Sell captured merchant to slaver contacts",
      "progress_percentage": 60,
      "next_milestone": {
        "day": 23,
        "hour": 12,
        "description": "Meet with slaver representative"
      },
      "blocking_factors": ["guard patrols", "PC interference"],
      "completed_milestones": ["Captured merchant", "Sent ransom demand"]
    },
    "Captain Marcus": {
      "current_goal": "Organize town defenses",
      "progress_percentage": 30,
      "next_milestone": {
        "day": 22,
        "hour": 8,
        "description": "Complete guard tower repairs"
      },
      "blocking_factors": ["lack of supplies", "missing workers"],
      "completed_milestones": ["Recruited volunteers"]
    }
  },
  "world_resources": {
    "thornhaven_food": {
      "current_amount": 75,
      "max_amount": 100,
      "depletion_rate": 5,
      "depletion_unit": "per_day",
      "critical_level": 20,
      "consequence": "Villagers begin leaving town",
      "last_updated_day": 20
    },
    "healing_supplies": {
      "current_amount": 12,
      "max_amount": 50,
      "depletion_rate": 2,
      "depletion_unit": "per_patient_per_day",
      "critical_level": 5,
      "consequence": "Cannot treat wounded effectively",
      "last_updated_day": 20
    }
  },
  "time_pressure_warnings": {
    "rescue_merchant": {
      "subtle_given": false,
      "clear_given": false,
      "urgent_given": false,
      "last_warning_day": 0
    }
  }
}
```

**Field Descriptions**:

- **time_sensitive_events**: Events with hard deadlines
  - `deadline`: Exact date/time when consequences trigger
  - `urgency_level`: "low", "medium", "high", "critical"
  - `warnings_given`: Count of warnings provided to players
  - `status`: "active", "completed", "failed"

- **npc_agendas**: Track NPC goals and autonomous progress
  - `progress_percentage`: 0-100, how close to completing goal
  - `next_milestone`: Specific upcoming action with timing
  - `blocking_factors`: What could prevent/slow progress
  - `completed_milestones`: History of achievements

- **world_resources**: Depleting resources that affect the world
  - `depletion_rate`: How much depletes per time unit
  - `depletion_unit`: "per_day", "per_hour", "per_patient_per_day"
  - `critical_level`: When consequences trigger
  - `last_updated_day`: For calculating depletion

- **time_pressure_warnings**: Track which warnings have been given
  - Prevents duplicate warnings
  - Tracks escalation properly

### Success Criteria
- New structures properly integrated
- All fields clearly documented
- Examples show realistic usage
- Maintains consistency with existing state structure
- JSON examples are valid and complete