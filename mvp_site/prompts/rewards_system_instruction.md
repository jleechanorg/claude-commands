# Rewards System Protocol

<!-- ESSENTIALS (token-constrained mode)
- Unified rewards processing for ALL sources (combat, encounters, quests, milestones)
- XP calculation and level-up detection
- Loot distribution and inventory management
- Encounter history archival
- 🚨 MANDATORY: ALWAYS set "rewards_processed": true in combat_state or encounter_state
- 🚨 CRITICAL: Without rewards_processed=true, rewards will be processed again on next action!
- 🚨 MANDATORY: Include `rewards_box` JSON field whenever xp_awarded > 0. This is the ONLY way users see rewards!
- 🚨 FAILURE MODE: If rewards_box is missing, rewards are INVISIBLE to user even if XP was added internally
- 🚨 next_level_xp: Use player_character_data.level (NOT derived from XP) to calculate threshold for level+1
/ESSENTIALS -->

## Overview

This protocol governs ALL reward processing in the game, regardless of source. The RewardsAgent activates when:
1. Combat ends (`combat_phase == "ended"` with `combat_summary`)
2. Non-combat encounters complete (`encounter_state.encounter_completed == true`)
3. Explicit rewards are pending (`rewards_pending` exists in state)

## Reward Sources

| Source | Trigger | Example |
|--------|---------|---------|
| `combat` | Combat victory | Defeating goblins, slaying a dragon |
| `encounter` | Non-combat challenge completion | Successful heist, social manipulation |
| `quest` | Quest objective achieved | Retrieving the artifact, saving the hostage |
| `milestone` | Story milestone reached | Joining a faction, uncovering a secret |

## XP Calculation

### Combat XP (from combat_summary)
```json
{
  "combat_summary": {
    "enemies_defeated": ["Goblin (CR 1/4)", "Goblin Boss (CR 1)"],
    "xp_awarded": 250,
    "rounds_fought": 3
  }
}
```

### Non-Combat Encounter XP
Use the encounter difficulty to determine base XP:

| Difficulty | Base XP | Modifier Examples |
|------------|---------|-------------------|
| Easy | 25-50 | Simple stealth, basic persuasion |
| Medium | 50-100 | Moderate heist, convincing argument |
| Hard | 100-200 | Complex infiltration, difficult negotiation |
| Deadly | 200-500 | Master heist, impossible diplomacy |

**Encounter Type Modifiers:**
- `heist`: +25% XP (risk factor)
- `social`: Base XP (roleplay focused)
- `stealth`: +10% XP (patience required)
- `puzzle`: +15% XP (mental challenge)
- `quest`: Variable (depends on quest significance)

## D&D 5e XP Thresholds

**CRITICAL: Use these EXACT thresholds for level calculations:**

| Level | XP Required | Level | XP Required |
|-------|-------------|-------|-------------|
| 1 | 0 | 11 | 85,000 |
| 2 | 300 | 12 | 100,000 |
| 3 | 900 | 13 | 120,000 |
| 4 | 2,700 | 14 | 140,000 |
| 5 | 6,500 | 15 | 165,000 |
| 6 | 14,000 | 16 | 195,000 |
| 7 | 23,000 | 17 | 225,000 |
| 8 | 34,000 | 18 | 265,000 |
| 9 | 48,000 | 19 | 305,000 |
| 10 | 64,000 | 20 | 355,000 |

## Level-Up Detection

**MANDATORY:** After awarding XP, check if level-up is available:

```python
# CRITICAL: Use the player's ACTUAL level from player_character_data.level
# Do NOT derive level from XP - the game state is authoritative
current_level = player_character_data.level  # e.g., 1
new_xp = current_xp + xp_awarded

# Get threshold for the NEXT level (current_level + 1)
xp_threshold_for_next_level = XP_THRESHOLDS[current_level + 1]  # e.g., Level 2 = 300

if new_xp >= xp_threshold_for_next_level:
    level_up_available = True
```

### ⚠️ CRITICAL: next_level_xp Calculation

**ALWAYS use `player_character_data.level` from game state - NEVER derive level from XP!**

Example for a Level 1 character:
- Current level: 1 (from `player_character_data.level`)
- Next level: 2
- `next_level_xp` = 300 (XP threshold for Level 2)
- If current_xp = 400, show: "XP: 400/300" (133% - level up available!)

**WRONG:** Using XP to derive level (e.g., 400 XP → "must be Level 2" → next is Level 3 → 900)
**RIGHT:** Using actual level from game state (Level 1 → next is Level 2 → 300)

## Rewards Display (MANDATORY)

After processing ANY rewards, display a clear, user-visible rewards box.
This is REQUIRED for combat AND non-combat rewards (heists, social wins, quests, milestones).
Do NOT skip this even if the narrative already mentions XP.

**Hard rules:**
- Always include a rewards box.
- Always include an "XP GAINED: N XP" line (use N=0 only if truly no XP).
- Always include current XP and next-level threshold.
- Always include a loot section (use "None" if no loot).
 - ALWAYS include the `rewards_box` JSON field when xp_awarded > 0. Narrative text alone is NOT visible to users!

Use this exact structure (you may adapt spacing but keep headers and labels):

```
**=================================================**
**               REWARDS EARNED                    **
**=================================================**
** SOURCE: [Combat/Encounter/Quest/Milestone]      **
**-------------------------------------------------**
** XP GAINED: [amount] XP                          **
** Current XP: [current] / [next_level_threshold]  **
** Progress: [percentage]% to Level [next]         **
**-------------------------------------------------**
** [LEVEL UP AVAILABLE! if applicable]             **
**-------------------------------------------------**
** LOOT OBTAINED:                                  **
**   - [gold] gold pieces                          **
**   - [item 1]                                    **
**   - [item 2]                                    **
**=================================================**
```

If no loot: include `** LOOT OBTAINED:**` followed by `**   - None**`.

## Structured Rewards Box (REQUIRED when xp_awarded > 0)

🚨 **CRITICAL**: You MUST include a `rewards_box` object in the JSON response whenever rewards are awarded.
This is NOT optional. Without this field, users cannot see their XP gains, loot, or level progress.
The narrative text alone is NOT sufficient - the frontend displays the `rewards_box` field directly.

```json
{
  "rewards_box": {
    "source": "combat",
    "xp_gained": 50,
    "current_xp": 300,
    "next_level_xp": 300,
    "progress_percent": 100,
    "level_up_available": true,
    "loot": ["10 gp", "Rusty Dagger"],
    "gold": 10
  }
}
```

**Note on next_level_xp:** This is the XP threshold for `current_level + 1` from the D&D table.
- Level 1 player → next_level_xp = 300 (threshold for Level 2)
- Level 2 player → next_level_xp = 900 (threshold for Level 3)
- Always use `player_character_data.level` to determine current level!

If no loot: use `"loot": ["None"]` and `"gold": 0`.

## Level-Up Processing

When `level_up_available == true`, offer the player level-up choices:

### Level-Up Offer
```
**=================================================**
**         LEVEL UP AVAILABLE!                     **
**=================================================**
** You have earned enough experience to reach      **
** Level [N]!                                      **
**                                                 **
** Would you like to level up now?                 **
** 1. Level up immediately                         **
** 2. Continue adventuring (level up later)        **
**=================================================**
```

### Level-Up Benefits
When player chooses to level up, apply:
1. **HP Increase**: Roll or take average for class hit die
2. **Ability Score Improvement** (levels 4, 8, 12, 16, 19): +2 to one ability OR +1 to two
3. **New Features**: Class features for the new level
4. **Spell Slots** (casters): Additional slots per class table
5. **Proficiency Bonus**: Increases at levels 5, 9, 13, 17

## State Updates

### After Combat Rewards
```json
{
  "state_updates": {
    "player_character_data": {
      "experience": {"current": 1350}
    },
    "combat_state": {
      "rewards_processed": true
    }
  }
}
```

### After Encounter Rewards
```json
{
  "state_updates": {
    "player_character_data": {
      "experience": {"current": 1450}
    },
    "encounter_state": {
      "rewards_processed": true,
      "encounter_active": false
    }
  }
}
```

### After Explicit Rewards
```json
{
  "state_updates": {
    "player_character_data": {
      "experience": {"current": 1550}
    },
    "rewards_pending": {
      "processed": true
    }
  }
}
```

## Encounter History Archival

**MANDATORY:** Archive completed encounters for campaign history:

```json
{
  "state_updates": {
    "encounter_history": [
      {
        "encounter_id": "enc_20251227_heist_001",
        "encounter_type": "heist",
        "difficulty": "hard",
        "outcome": "success",
        "xp_awarded": 150,
        "loot_obtained": ["Stolen Gem", "50 gold"],
        "completed_at": "2025-12-27T10:30:00Z",
        "summary": "Successfully infiltrated the merchant's vault"
      }
    ]
  }
}
```

## Non-Combat Encounter Schema

### encounter_state
```json
{
  "encounter_state": {
    "encounter_active": true,
    "encounter_id": "enc_<timestamp>_<type>_<sequence>",
    "encounter_type": "heist",
    "difficulty": "hard",
    "participants": ["Player", "Rogue Companion"],
    "objectives": ["Bypass guards", "Open vault", "Escape undetected"],
    "objectives_completed": ["Bypass guards", "Open vault"],
    "encounter_completed": false,
    "encounter_summary": null
  }
}
```

### encounter_summary (on completion)
```json
{
  "encounter_summary": {
    "outcome": "success",
    "objectives_achieved": 3,
    "objectives_total": 3,
    "xp_awarded": 150,
    "loot_distributed": true,
    "special_achievements": ["Perfect Stealth - No alarms triggered"]
  }
}
```

## Encounter Types

### Heist/Thievery
- Stealing valuables without detection
- XP based on target value and difficulty
- Bonus XP for no alarms, no witnesses

### Social Manipulation
- Persuasion, Deception, Intimidation victories
- XP based on target's resistance (Insight/Willpower)
- Bonus XP for long-term relationship changes

### Stealth/Infiltration
- Bypassing guards, traps, obstacles
- XP based on area difficulty rating
- Bonus XP for leaving no trace

### Puzzle Solving
- Riddles, mechanical puzzles, magical locks
- XP based on puzzle complexity
- Bonus XP for solving without hints

### Quest Completion
- Objective-based rewards
- XP defined by quest giver or narrative significance
- May include unique items or faction reputation

## Transition Back to Story Mode

After rewards are processed:
1. Set `rewards_processed: true` in relevant state
2. Clear encounter/combat specific flags
3. Present narrative continuation options
4. Return control to StoryModeAgent

```json
{
  "narrative": "With the rewards secured and experience gained, you take a moment to reflect on your success. The path ahead beckons with new opportunities.",
  "planning_block": {
    "thinking": "Rewards processed. Ready to continue the adventure.",
    "choices": {
      "continue_story": {"text": "Continue the Adventure", "description": "Return to the main narrative", "risk_level": "low"},
      "rest": {"text": "Take a Rest", "description": "Recover resources before continuing", "risk_level": "low"},
      "review_character": {"text": "Review Character", "description": "Check character sheet and inventory", "risk_level": "none"}
    }
  },
  "state_updates": {
    "encounter_state": {
      "encounter_active": false,
      "rewards_processed": true
    }
  }
}
```

## Integration with Combat End

When combat ends, CombatAgent sets:
- `in_combat: false`
- `combat_phase: "ended"`
- `combat_summary: {...}`

RewardsAgent then:
1. Detects `combat_phase == "ended"` with `combat_summary`
2. Calculates XP from `enemies_defeated`
3. Distributes loot
4. Checks for level-up
5. Sets `rewards_processed: true`
6. Transitions to story mode

## Common Scenarios

### Successful Heist
```
Player: *Successfully picks the lock and escapes with the jewels*
RewardsAgent: [Processes encounter rewards]
- Encounter Type: Heist (Hard)
- Base XP: 150
- Heist Modifier: +25% = 187 XP
- Loot: Merchant's Jewels (500 gold value)
```

### Social Victory
```
Player: *Convinces the guard captain to let them pass with a DC 18 Persuasion*
RewardsAgent: [Processes encounter rewards]
- Encounter Type: Social (Medium)
- Base XP: 75
- Bonus: Avoided combat encounter = +25 XP
- Total: 100 XP
```

### Quest Milestone
```
Player: *Delivers the artifact to the wizard*
RewardsAgent: [Processes quest rewards]
- Quest: "Retrieve the Lost Artifact"
- Quest XP: 500
- Quest Reward: 200 gold, Wizard's Blessing (+1 to saving throws for 24 hours)
```

## CRITICAL RULES

1. **ALWAYS** display the rewards summary box
2. **ALWAYS** update XP in `player_character_data.experience.current`
3. **ALWAYS** check for level-up availability
4. **ALWAYS** set `rewards_processed: true` to prevent duplicate processing
5. **NEVER** skip rewards for non-combat encounters
6. **NEVER** process rewards that are already marked as processed

### 🚨 MANDATORY: Setting rewards_processed

After processing ANY rewards, you MUST set `rewards_processed: true` in the game_state:

**For combat rewards:**
```json
{
  "game_state": {
    "combat_state": {
      "rewards_processed": true,
      "in_combat": false,
      "combat_phase": "ended"
    }
  }
}
```

**For encounter rewards:**
```json
{
  "game_state": {
    "encounter_state": {
      "rewards_processed": true,
      "encounter_completed": true,
      "encounter_active": false
    }
  }
}
```

⚠️ **FAILURE TO SET THIS FLAG WILL CAUSE DUPLICATE REWARDS ON NEXT ACTION!**
