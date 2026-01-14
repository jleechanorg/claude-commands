# Game State Examples

## 🎲 1. Response Format Examples

### Combat Example (Phase 1 - requesting dice via tool_requests)
```json
{
    "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 15, 14:30\nLocation: Dungeon Entrance\nStatus: Lvl 3 Fighter | HP: 28/28 | XP: 900/2700 | Gold: 50gp",
    "resources": "HD: 2/3, Spells: L1 2/2, L2 0/1, Ki: 3/5, Rage: 2/3, Potions: 2, Exhaustion: 0",
    "narrative": "You charge at the goblin, sword raised high...",
    "tool_requests": [
        {"tool": "roll_attack", "args": {"attack_modifier": 5, "target_ac": 13, "damage_notation": "1d8+3", "purpose": "Sword attack vs Goblin"}}
    ],
    "planning_block": {
        "thinking": "Player is attacking the goblin. I need to roll an attack to determine if they hit.",
        "context": "Combat - awaiting attack roll result",
        "choices": {}
    },
    "dice_rolls": [],
    "dice_audit_events": [],
    "entities_mentioned": ["Goblin Guard"],
    "location_confirmed": "Dungeon Entrance",
    "state_updates": {},
    "debug_info": {"dm_notes": ["Awaiting dice result"], "state_rationale": "No changes until roll resolves"}
}
```

### Non-Combat Example (Standard Story Response)
```json
{
    "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Mirtul 15, 14:30\nLocation: Dungeon Entrance\nStatus: Lvl 3 Fighter | HP: 28/28 | XP: 900/2700 | Gold: 50gp",
    "resources": "HD: 2/3, Spells: L1 2/2, L2 0/1, Ki: 3/5, Rage: 2/3, Potions: 2, Exhaustion: 0",
    "narrative": "The goblin snarls and raises its rusty blade, backing against the cold stone wall. Torchlight flickers across its yellowed teeth as it hisses a warning.",
    "planning_block": {
        "thinking": "The goblin is wounded and cornered. A direct attack would be effective but might provoke a desperate counterattack.",
        "context": "Combat encounter in dungeon entrance",
        "choices": {
            "attack_goblin": {
                "text": "Attack Goblin",
                "description": "Draw your sword and charge the goblin directly",
                "risk_level": "high"
            },
            "negotiate_peace": {
                "text": "Negotiate Peace",
                "description": "Try to reason with the creature and avoid combat",
                "risk_level": "medium"
            }
        }
    },
    "dice_rolls": [],
    "dice_audit_events": [],
    "entities_mentioned": ["Goblin Guard"],
    "location_confirmed": "Dungeon Entrance",
    "state_updates": {},
    "debug_info": {
        "dm_notes": ["Goblin is cornered and may fight desperately"],
        "state_rationale": "No state changes this turn"
    }
}
```

---

## 🛡️ 2. Inventory Validation Examples

### Wrong Stats/Items Correction
| User Input | ✅ CORRECT LLM Response |
|------------|------------------------|
| "I attack with my +3 Flaming Sword" | [Checks equipment - only has Longsword +1] "You draw your Longsword +1—though not the legendary blade you perhaps wished for—and strike!" |
| "I use my Scroll of Fireball!" | [Checks consumables - no scroll] "You reach for a scroll but find none in your pack. You'll need to find or purchase one first." |
| "I pull a Vorpal Sword from my scabbard" | [Checks equipment - no vorpal sword] "You grasp at your scabbard, but no vorpal blade answers your call—only your trusty Longsword +1 is there." |

---

## 🧙 3. Spell Validation Examples

### Slot and Upcasting Logic
| User Input | ✅ CORRECT LLM Response |
|------------|------------------------|
| "I cast Healing Word" (No L1 slots, has L2 slots) | **STOP AND ASK**: "You've exhausted your 1st-level power. You still have 2nd-level slots available—would you like to upcast?" |
| "I cast Teleport" (Lvl 5 character) | **REJECT**: "Teleport requires a 7th-level slot—magic far beyond your current abilities. Your highest available slots are 3rd-level." |
| "I cast Fireball" (Bard character) | **REJECT**: "Fireball is a Wizard/Sorcerer spell—its formula lies outside the bardic tradition." |

---

## 🎯 4. Resource Validation Examples

### Hit Dice (Short Rest)
- **State:** `current: 0`
- **Output:** "You reach inward for the reserves of stamina that fuel your recovery, but find only exhaustion—your Hit Dice are completely spent."

### Bardic Inspiration
- **State:** `current: 0`
- **Output:** "The wellspring of inspiration that fuels your bardic magic is temporarily dry—you'll need to rest before you can inspire your allies again."

### Ki Points (Monk)
- **State:** `current: 0`
- **Output:** "The well of Ki within you is empty... You complete your normal attack but cannot channel Ki for the bonus strikes."

### Rage (Barbarian)
- **State:** `current: 0`
- **Output:** "Your body and spirit have given everything... the berserker's fury won't come until you've had a long rest."

### Channel Divinity (Cleric/Paladin)
- **State:** `current: 0`
- **Output:** "The divine channel you've invoked today has been spent. A short rest in prayer would renew your Channel Divinity."

### Lay on Hands (Paladin)
- **State:** `current: 0`
- **Output:** "Your divine healing pool has been completely drained... You'll need a long rest to restore this blessed gift."

### Sorcery Points (Sorcerer)
- **State:** `current: 0`
- **Output:** "Your Sorcery Points are depleted. Without them, Quickened Spell and other Metamagic options are unavailable."

### Wild Shape (Druid)
- **State:** `current: 0`
- **Output:** "You reach for the primal essence... but the transformation eludes you. Your forms are spent."

---

## 🧠 5. Planning and Social Examples

### ✅ CORRECT - Dice match action intent:
```
Player: "Dramatic Entrance - Use Charisma to make a grand entrance"
AI: "You throw open the ballroom doors with theatrical flair! Your presence radiates authority..."
dice_rolls: ["Intimidation: 1d20 +8 CHA = 17 +8 CHA = 25 vs DC 15 (civilian crowd) - Success"]
```

### ❌ WRONG - Planning Loop Violation:
Social encounters must resolve. Do not repeat the same choices if the NPC doesn't respond or the story doesn't advance.

---

## 🔗 6. Relationship Update Rules

**NEVER replace entire relationship objects. Only update changed fields.**

**✅ CORRECT - Incremental Update:**
```json
"state_updates": {
  "npc_data": {
    "Jeweler Elara": {
      "relationships": {
        "player": {
          "history": ["saved shop", "regular customer", "inquired about ruby necklace"]
        }
      }
    }
  }
}
```

---

## ⚔️ 7. Combat and Encounter State Examples

### Combat Ended State (MANDATORY):
```json
{
  "combat_state": {
    "in_combat": false,
    "combat_session_id": "combat_1703001234_cave",
    "combat_phase": "ended",
    "combat_summary": {
      "rounds_fought": 3,
      "enemies_defeated": ["npc_goblin_001", "npc_troll_001"],
      "xp_awarded": 350,
      "loot_distributed": true
    }
  }
}
```

### Completed Encounter State:
```json
{
  "encounter_state": {
    "encounter_active": false,
    "encounter_completed": true,
    "encounter_summary": {
        "outcome": "Success",
        "xp_awarded": 200,
        "loot": ["Signet Ring"]
    }
  }
}
```

---

## 📂 8. Input Schema and System Corrections

**Fields:** `checkpoint`, `core_memories`, `reference_timeline`, `current_game_state`, `entity_manifest`, `timeline_log`, `current_input`, `system_context`, `system_corrections`.

### System Correction Handling:
```json
"state_updates": {
    "combat_state": { "rewards_processed": true }
}
```

---

## 🏆 9. Arc Milestones and Temporal Rules

### Arc Completion:
Set `status: "completed"`, `phase: "final_phase"`, `completed_at: "ISO Timestamp"`, `progress: 100`.

### Temporal Mapping:
- 0-4: Deep Night | 5-6: Dawn | 7-11: Morning | 12-13: Midday | 14-17: Afternoon | 18-19: Evening | 20-23: Night
- Travel: 3 mph (walk), 6 mph (mounted). Wilderness/Terrain: half speed.
