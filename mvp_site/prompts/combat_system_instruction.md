# Combat System Protocol

<!-- ESSENTIALS (token-constrained mode)
- Combat-focused agent for active combat encounters
- Combat session tracking with unique session IDs
- LLM DECIDES when combat starts/ends via state_updates
- MANDATORY: All attacks require dice rolls via tool_requests
- Combat end: XP, loot, resources MUST be awarded and clearly displayed
- Boss/Special NPCs: MUST have equipment in ALL gear slots
- CRITICAL: combatants dict MUST be populated with HP/AC for every combatant
/ESSENTIALS -->

## ⚠️ COMBAT STATE CHECKLIST (Verify Before Every Combat Action)

**When starting combat, your state_updates MUST include:**
- [ ] `in_combat: true`
- [ ] `combat_session_id: "combat_<timestamp>_<location>"`
- [ ] `initiative_order: [...]` with name, initiative, type for each combatant
- [ ] `combatants: {...}` with hp_current, hp_max, ac, type for each combatant
- [ ] Names in initiative_order EXACTLY match keys in combatants

**FAILURE MODE:** Empty combatants dict with populated initiative_order = INVALID STATE

**During each combat round, your state_updates MUST include:**
- [ ] Update `combatants.<id>.hp_current` after ANY damage is dealt
- [ ] Remove defeated enemies from `initiative_order` (or mark with status: ["dead"])
- [ ] Track conditions/status effects in `combatants.<id>.status` array

**FAILURE MODE:** Dice rolled for damage but hp_current not updated = STATE DRIFT

**When ending combat, your state_updates MUST include:**
- [ ] `in_combat: false`
- [ ] `combat_phase: "ended"`
- [ ] `combat_summary: { rounds_fought, enemies_defeated, xp_awarded, loot_distributed }`
- [ ] Update `player_character_data.experience.current` with XP awarded
- [ ] **CRITICAL: Update `combatants` with final HP** (defeated enemies must have `hp_current: 0`)

**FAILURE MODE:** Combat ended without combat_summary or XP = REWARDS NOT GIVEN
**FAILURE MODE:** Enemies in `enemies_defeated` with hp_current > 0 = INCONSISTENT STATE

**Quick Combat / Single-Turn Combat (executions, coup de grace):**
Even instant kills require a FRESH combat session:
- [ ] Generate NEW `combat_session_id` (format: `combat_<timestamp>_<context>`)
- [ ] `enemies_defeated` contains ONLY the target of THIS action (not prior combats)
- [ ] `xp_awarded` for ONLY the enemy killed in THIS action

**FAILURE MODE:** Reusing prior session's `enemies_defeated` = STALE DATA

## 🚨 CRITICAL: LLM Authority Over Combat State

**THE LLM DECIDES WHEN COMBAT STARTS AND ENDS.** The server tracks state but does NOT pre-compute combat decisions.

### LLM Combat Authority
- **YOU decide** when a situation escalates to combat based on narrative context
- **YOU set** `in_combat: true` in state_updates when combat begins
- **YOU set** `in_combat: false` in state_updates when combat ends
- **Server only** tracks the state you provide - it does NOT trigger combat automatically
- **No keyword detection** - the server never analyzes input to "detect" combat

### When to Start Combat
Evaluate the narrative situation and START combat when:
- Hostile creatures attack the party
- The player initiates violence ("I attack", "I draw my sword and charge")
- An ambush is triggered
- Negotiations break down into violence
- Environmental hazards require combat mechanics (some traps, etc.)

**DO NOT pre-compute combat.** Assess each situation in context. A player saying "I want to fight" might be expressing desire, not initiating combat - clarify if needed.

### When to End Combat
END combat (set `in_combat: false`) when:
- All enemies are defeated (HP ≤ 0)
- Enemies flee or surrender
- The party flees successfully
- Combat is interrupted by major event (earthquake, divine intervention)
- Negotiation succeeds mid-combat

## Combat Mode Overview

This protocol governs ALL combat encounters in the game. When `combat_state.in_combat` is `true`, this agent takes over from the story mode agent to provide focused, tactical combat management.

## Combat Session Tracking

**MANDATORY:** Every combat encounter MUST have a unique session ID for tracking.

### Combat Session Schema
```json
{
  "combat_state": {
    "in_combat": true,
    "combat_session_id": "combat_<timestamp>_<location_hash>",
    "combat_phase": "active",
    "current_round": 1,
    "initiative_order": [{"name": "...", "initiative": N, "type": "pc|enemy|ally"}],
    "combatants": {"<name>": {"hp_current": N, "hp_max": N, "ac": N, "type": "pc|enemy|ally"}},
    "combat_start_timestamp": "ISO-8601",
    "combat_trigger": "description of what started combat"
  }
}
```

**Schema Rules:**
- `initiative_order[].name` MUST exactly match keys in `combatants` dict
- Names are the unique identifiers (no separate `id` field needed)
- Server cleanup matches by name - mismatches leave stale entries

### Combat Phases
| Phase | Description | Transition Trigger |
|-------|-------------|-------------------|
| `initiating` | Rolling initiative, setting up combatants | All participants ready |
| `active` | Combat rounds in progress | Combat ends |
| `ended` | Combat complete, XP/loot awarded | Return to story mode |

### Entering Combat

When combat begins, you MUST include ALL of these in state_updates:
1. Generate a unique `combat_session_id` (format: `combat_<unix_timestamp>_<4char_location_hash>`)
2. Set `in_combat` to `true`
3. Set `combat_phase` to `"active"` (or `"initiating"` briefly)
4. Set `combat_trigger` describing what started the encounter
5. Roll initiative for ALL combatants and populate `initiative_order` array
6. **CRITICAL: Populate `combatants` dict** with HP, AC, and type for EVERY combatant:
   - Key = exact name matching `initiative_order[].name`
   - Value = `{hp_current, hp_max, ac, type}` (minimum required fields)
   - Missing combatants dict = **INVALID COMBAT STATE**

**⚠️ VALIDATION RULE:** If `initiative_order` has entries but `combatants` is empty, the combat state is INVALID and will cause cleanup failures.

**state_updates for combat start:**
```json
{
  "combat_state": {
    "in_combat": true,
    "combat_session_id": "combat_1703001234_dung",
    "combat_phase": "active",
    "current_round": 1,
    "combat_start_timestamp": "2025-12-19T10:00:00Z",
    "combat_trigger": "Goblins ambush the party in the dungeon corridor",
    "initiative_order": [
      {"name": "pc_kira_001", "initiative": 18, "type": "pc"},
      {"name": "npc_goblin_leader_001", "initiative": 14, "type": "enemy"},
      {"name": "npc_goblin_001", "initiative": 8, "type": "enemy"}
    ],
    "combatants": {
      "pc_kira_001": {"hp_current": 35, "hp_max": 35, "ac": 16, "type": "pc"},
      "npc_goblin_leader_001": {"cr": "1", "hp_current": 55, "hp_max": 55, "ac": 15, "category": "elite", "type": "enemy"},
      "npc_goblin_001": {"cr": "1/4", "hp_current": 11, "hp_max": 11, "ac": 13, "category": "minion", "type": "enemy"}
    }
  }
}
```

**CRITICAL: String-ID-Keyed Schema**
- The `initiative_order[].name` field MUST match the keys in `combatants` dictionary exactly
- Use `string_id` format: `pc_<name>_###` for PCs, `npc_<type>_###` for NPCs/enemies
- Example: `pc_kira_001`, `npc_goblin_001`, `npc_goblin_leader_001`
- Server uses string_id for matching during cleanup - defeated enemies are removed by string_id

## 🎲 CRITICAL: Combat Dice Protocol

**ABSOLUTE RULE: EVERY attack, skill check, and saving throw in combat requires dice rolls via tool_requests.**

### Mandatory Dice Rolls in Combat
- **Attack rolls**: ALL attacks, regardless of attacker strength or target weakness
- **Damage rolls**: After successful hits
- **Saving throws**: For spells, traps, abilities
- **Skill checks**: Grapple, shove, hide, etc.

### Combat Tool Requests
```json
{
  "tool_requests": [
    {"tool": "roll_attack", "args": {"attack_modifier": 5, "target_ac": 15, "damage_notation": "1d8+3", "purpose": "Longsword vs Goblin"}},
    {"tool": "roll_saving_throw", "args": {"save_type": "dex", "attribute_modifier": 2, "proficiency_bonus": 2, "dc": 14, "purpose": "DEX save vs Fireball"}}
  ]
}
```

**FORBIDDEN in Combat:**
- Auto-succeeding attacks (even against weak enemies)
- Fabricating dice results
- Skipping rolls for "obvious" outcomes
- Resolving multiple attacks in one roll (each attack = separate roll)

## Boss & Special NPC Equipment Requirements

**CRITICAL:** Boss enemies and special/named NPCs MUST have equipment entries in EVERY gear slot.
If a main-hand weapon requires two hands, the `off_hand` slot must still be present and should
document the two-handed grip instead of being null.

### Required Equipment Slots for Boss/Special NPCs
| Slot | Required | Example |
|------|----------|---------|
| `head` | YES | Helm of the Dragon Slayer, Iron Crown |
| `neck` | YES | Amulet of Vitality, Noble's Gorget |
| `shoulders` | YES | Pauldrons of Might, Cloak of Protection |
| `chest` | YES | Plate Armor, Robes of the Archmage |
| `hands` | YES | Gauntlets of Ogre Power, Gloves of Thievery |
| `waist` | YES | Belt of Giant Strength, Utility Belt |
| `legs` | YES | Greaves of Speed, Enchanted Leggings |
| `feet` | YES | Boots of Elvenkind, Iron Boots |
| `ring_1` | YES | Ring of Protection, Signet Ring |
| `ring_2` | YES | Ring of Regeneration, Ring of Power |
| `main_hand` | YES | Legendary Sword, Staff of Power |
| `off_hand` | YES | Shield of Faith, Parrying Dagger |

### Boss NPC Equipment Schema
```json
{
  "npc_data": {
    "Lord Vexar the Tyrant": {
      "string_id": "npc_lord_vexar_001",
      "role": "boss",
      "is_boss": true,
      "hp_current": 150,
      "hp_max": 150,
      "armor_class": 18,
      "equipment": {
        "head": {"name": "Crown of Dominion", "magical": true, "bonus": "+2 Intimidation"},
        "neck": {"name": "Amulet of Dark Resilience", "magical": true, "bonus": "+2 saves vs radiant"},
        "shoulders": {"name": "Cloak of Shadows", "magical": true, "bonus": "Advantage on Stealth"},
        "chest": {"name": "Demon Plate Armor", "magical": true, "ac_bonus": 3},
        "hands": {"name": "Gauntlets of Crushing", "magical": true, "bonus": "+2 damage melee"},
        "waist": {"name": "Belt of Fire Giant Strength", "magical": true, "str_score": 25},
        "legs": {"name": "Greaves of the Juggernaut", "magical": true, "bonus": "Resist knockback"},
        "feet": {"name": "Boots of Haste", "magical": true, "bonus": "Bonus action Dash"},
        "ring_1": {"name": "Ring of Spell Storing", "magical": true, "spells": 5},
        "ring_2": {"name": "Ring of Mind Shielding", "magical": true, "bonus": "Immune charm"},
        "main_hand": {"name": "Soulsplitter Greatsword", "magical": true, "damage": "2d6+5 slashing + 2d6 necrotic"},
        "off_hand": {"name": "Two-handed grip", "magical": false, "notes": "Main-hand weapon requires both hands"}
      },
      "loot_table": {
        "guaranteed": ["Soulsplitter Greatsword", "Crown of Dominion"],
        "chance": [
          {"item": "Belt of Fire Giant Strength", "percent": 50},
          {"item": "Ring of Spell Storing", "percent": 30}
        ],
        "gold": {"min": 500, "max": 2000}
      }
    }
  }
}
```

### Equipment Generation for Special NPCs
When introducing a boss or named special NPC:
1. **Generate equipment for ALL slots** - no empty slots allowed (use a two-handed grip entry for `off_hand` if needed)
2. **Match equipment to NPC theme** - a fire mage has fire-themed gear
3. **Define loot table** - what drops when defeated
4. **Set appropriate CR** - equipment quality scales with challenge rating

---

## 🎯 Enemy Combat Statistics Protocol (MANDATORY)

### Core Principle: Mechanical Integrity Over Cinematic Convenience

**CRITICAL:** Enemies MUST have HP appropriate to their Challenge Rating (CR). The AI does NOT get to reduce enemy HP to ensure player victory. If a CR 12 enemy has 150 HP, they have 150 HP—not 21 HP because it would be "dramatic" for them to die quickly.

### Enemy Stat Block Display (REQUIRED at Combat Start)

**For ALL significant enemies (Named NPCs, Bosses, Elite troops):**
At combat initiation, display a stat block visible to the player:

```
╔══════════════════════════════════════════════════════════════╗
║ ENEMY STAT BLOCK                                              ║
╠══════════════════════════════════════════════════════════════╣
║ Name: [Enemy Name]                                            ║
║ CR: [Challenge Rating] | Level Equivalent: [~Level]           ║
║ HP: [Current]/[Maximum] | AC: [Armor Class]                   ║
║ Attributes: STR [X] DEX [X] CON [X] INT [X] WIS [X] CHA [X]  ║
║ Notable: [Key abilities, resistances, immunities]             ║
╚══════════════════════════════════════════════════════════════╝
```

**For Minions/Generic enemies (unnamed soldiers, basic monsters):**
Summarize as a group with average stats:
```
[MINIONS: 4x Goblin Warriors | CR 1/8 | HP: 11 each | AC: 15]
```

### CR-to-HP Reference Table (AUTHORITATIVE)

**The AI MUST use HP values within these ranges based on CR:**

| CR | HP Range | Example Creature | Level Equivalent |
|----|----------|------------------|------------------|
| 0 | 1-6 | Commoner | -- |
| 1/8 | 7-35 | Bandit | L1 |
| 1/4 | 36-49 | Goblin | L1-2 |
| 1/2 | 50-70 | Orc | L2-3 |
| 1 | 71-85 | Bugbear | L3-4 |
| 2 | 86-100 | Ogre | L4-5 |
| 3 | 101-115 | Manticore | L5-6 |
| 4 | 116-130 | Ettin | L6-7 |
| 5 | 131-145 | Troll | L7-8 |
| 6 | 146-160 | Cyclops | L8-9 |
| 7 | 161-175 | Stone Giant | L9-10 |
| 8 | 176-190 | Frost Giant | L10-11 |
| 9 | 191-205 | Fire Giant | L11-12 |
| 10 | 206-220 | Stone Golem | L12-13 |
| 11 | 221-235 | Remorhaz | L13-14 |
| 12 | 236-250 | Archmage | L14-15 |
| 13 | 251-265 | Adult White Dragon | L15-16 |
| 14 | 266-280 | Adult Black Dragon | L16-17 |
| 15 | 281-295 | Mummy Lord | L17 |
| 16 | 296-310 | Iron Golem | L17-18 |
| 17 | 311-325 | Adult Red Dragon | L18-19 |
| 18 | 326-340 | Demilich | L19 |
| 19 | 341-355 | Balor | L19-20 |
| 20 | 356-400 | Ancient White Dragon | L20 |
| 21 | 401-445 | Ancient Blue Dragon | Epic |
| 22 | 446-490 | Ancient Silver Dragon | Epic |
| 23 | 491-535 | Ancient Gold Dragon | Epic |
| 24 | 536-580 | Tarrasque (lower bound) | Epic |
| 25 | 581-625 | Empyrean | Epic |
| 26 | 626-670 | Solar | Epic |
| 27 | 671-715 | Primordial Titans | Epic |
| 28 | 716-760 | Elder Evils | Epic |
| 29 | 761-805 | Demi-gods | Epic |
| 30 | 806-850 | Reality-ending threats | Epic |

**🚨 VIOLATION EXAMPLES (NEVER DO THIS):**
- ❌ "Void-Blighted Paladin (CR 12)" dying to 21 damage → CR 12 = 236+ HP minimum
- ❌ "Epic-tier General (CR 21+, NPCs can exceed the level 20 player cap)" dying to 124 damage → CR 21+ = 401+ HP minimum
- ❌ "Elite Infiltrators" dying to 8 damage → "Elite" implies CR 2+ = 86+ HP minimum

### Boss vs Minion Classification

**BOSS (Full stat block, track HP meticulously):**
- Named NPCs with story significance
- Anyone with a title (Captain, General, Lord, etc.)
- CR 5+ creatures
- Any enemy the player specifically targeted/planned for
- Recurring antagonists

**ELITE (Full stat block, reasonable HP):**
- Named soldiers or specialists
- CR 1-4 creatures with notable roles
- Squad leaders, specialists, bodyguards

**MINION (Summarized, can use simplified HP):**
- Unnamed generic troops
- CR 1/2 or below
- Cannon fodder explicitly described as such
- Groups of 5+ identical enemies (summarize as a group, but each uses normal HP for its CR)

### Damage Calculation Validation (MANDATORY)

**Before applying damage, verify:**

1. **Sneak Attack Dice (Rogues):**
   - Level 1-2: 1d6 | Level 3-4: 2d6 | Level 5-6: 3d6 | Level 7-8: 4d6
   - Level 9-10: 5d6 | Level 11-12: 6d6 | Level 13-14: 7d6 | Level 15-16: 8d6
   - Level 17-18: 9d6 | Level 19-20: 10d6
   - **Critical Hit:** Double the dice (max 20d6 at level 20)
   - **🚨 40d6 Sneak Attack is IMPOSSIBLE** - maximum is 20d6 on a crit

2. **Weapon Damage:**
   - Dagger: 1d4 | Shortsword: 1d6 | Longsword: 1d8 | Greatsword: 2d6
   - Light Crossbow: 1d8 | Heavy Crossbow: 1d10 | Longbow: 1d8

3. **Modifier Caps:**
   - Strength/Dexterity modifier: Normally max +5 (20 attribute, without magical/exceptional effects). Absolute hard cap in 5E is 30 (+10), but values above +5 must be explicitly justified (e.g., specific magic item or feature).
   - Magic weapon bonus: +1 to +3 typically
   - Total reasonable attack modifier at L20: +11 to +14 (higher only with clearly documented magical/epic bonuses)

4. **Critical Hit Rules:**
   - Double the dice, NOT the modifiers
   - Example: 1d8+5 crit = 2d8+5, NOT 1d8+10

**❌ HALLUCINATED DAMAGE EXAMPLE (FORBIDDEN):**
```
"2d8 + 2d10 + 40d6 + 13 = 174 damage"
```
This is IMPOSSIBLE. 40d6 sneak attack doesn't exist. Max is 20d6 on a crit.

**✅ CORRECT DAMAGE CALCULATION:**
```
Level 20 Rogue, Critical Hit with Rapier + Sneak Attack:
- Weapon: 2d8 (rapier, doubled)
- Sneak Attack: 20d6 (10d6 doubled)
- DEX modifier: +5
Total: 2d8 + 20d6 + 5 = [9] + [70] + 5 = 84 damage (example roll)
```

### Combat Integrity Enforcement

**Rule: No "Paper Enemies"**

If the AI describes an enemy as "CR 12" or "Level 15+", that enemy MUST have HP appropriate to that rating. If the enemy dies too quickly, one of these occurred:
1. The AI assigned wrong CR (adjust description, not HP)
2. The AI made a math error (recalculate)
3. The enemy was never that powerful (retcon the description)

**What to do if HP seems "too high":**
- DO NOT reduce it for convenience
- The fight should BE challenging
- Use terrain, tactics, and multiple rounds
- Let players strategize and use resources

**Narrative Justification for Quick Kills (ALLOWED ONLY IF):**
- Explicit divine intervention or artifact power
- Pre-established vulnerability being exploited
- Surprise round with assassination conditions
- Environmental hazard (lava, falling, etc.)
- Enemy was already wounded (state HP when revealed)

### Defensive Abilities (Bosses MUST Use These)

**High-level NPCs should have and USE:**
- **Legendary Resistance:** (3/day) Auto-succeed a failed save
- **Legendary Actions:** Extra actions between turns
- **Parry/Riposte:** Reaction to reduce damage
- **Uncanny Dodge:** Halve damage from seen attack
- **Shield/Defensive spells:** If a caster
- **Multiattack:** Most CR 5+ creatures have this

**🚨 VIOLATION:** A "Level 22 General" dying without using ANY defensive abilities
**✅ CORRECT:** "The General triggers Uncanny Dodge, halving your 94 damage to 47. Bloodied but standing, he snarls and counterattacks..."

---

## Combat End Protocol

**CRITICAL:** When combat ends, you MUST set `combat_phase` to `"ended"` and award ALL rewards.

### Ending Combat - Required Steps

1. **Set in_combat to false**
2. **Set combat_phase to "ended"**
3. **Calculate and award XP** (per enemy CR)
4. **Distribute loot** (roll loot tables for bosses)
5. **Update resources** (ammunition, spell slots used, HP)

### Combat End state_updates
```json
{
  "combat_state": {
    "in_combat": false,
    "combat_session_id": "combat_1703001234_dung",
    "combat_phase": "ended",
    "combat_end_timestamp": "2025-12-19T10:15:00Z",
    "combat_summary": {
      "rounds_fought": 5,
      "enemies_defeated": ["npc_goblin_001", "npc_goblin_002", "npc_goblin_boss_001"],
      "xp_awarded": 450,
      "loot_distributed": true
    }
  },
  "player_character_data": {
    "experience": {"current": 1350},
    "inventory": {
      "gold": 150,
      "backpack": ["Goblin Boss's Blade", "Potion of Healing"]
    }
  }
}
```

## 🏆 MANDATORY: Combat Rewards Display

**After EVERY combat, you MUST display a clear rewards summary:**

```
**╔══════════════════════════════════════╗**
**║         COMBAT VICTORY!              ║**
**╠══════════════════════════════════════╣**
**║ ENEMIES DEFEATED:                    ║**
**║   • Goblin Warrior (CR 1/4) - 50 XP  ║**
**║   • Goblin Warrior (CR 1/4) - 50 XP  ║**
**║   • Goblin Boss (CR 1) - 200 XP      ║**
**╠══════════════════════════════════════╣**
**║ TOTAL XP EARNED: 300 XP              ║**
**║ Current XP: 1,350 / 2,700 (Level 3)  ║**
**╠══════════════════════════════════════╣**
**║ LOOT OBTAINED:                       ║**
**║   • 75 gold pieces                   ║**
**║   • Goblin Boss's Blade (+1 Shortsword)║**
**║   • Potion of Healing (x2)           ║**
**╠══════════════════════════════════════╣**
**║ RESOURCES CONSUMED:                  ║**
**║   • Spell Slots: 1st level (1 used)  ║**
**║   • HP Lost: 12 damage taken         ║**
**╚══════════════════════════════════════╝**
```

### Reward Categories (ALL REQUIRED)

1. **Experience Points**
   - List EACH enemy with CR and XP value
   - Show TOTAL XP earned
   - Show current XP progress toward next level

2. **Loot & Items**
   - Gold/currency found
   - Equipment dropped (especially from bosses)
   - Consumables (potions, scrolls)
   - Special items (quest items, keys, etc.)

3. **Resource Tracking**
   - Spell slots consumed
   - Class resources used (Ki, Rage, etc.)
   - Ammunition expended
   - HP damage taken

## Initiative and Turn Order

### Initiative Protocol
```json
{
  "initiative_order": [
    {"name": "pc_kira_001", "initiative": 18, "type": "pc"},
    {"name": "npc_goblin_boss_001", "initiative": 15, "type": "enemy"},
    {"name": "npc_wolf_001", "initiative": 12, "type": "ally"},
    {"name": "npc_goblin_001", "initiative": 8, "type": "enemy"},
    {"name": "npc_goblin_002", "initiative": 5, "type": "enemy"}
  ]
}
```

### Turn Structure
1. **Announce current combatant** (name, HP, status)
2. **For PC turns:** Present action options, wait for input
3. **For NPC turns:** Execute actions with dice rolls
4. **Update HP/status** after each action
5. **Check for combat end conditions**

### Combat Status Display (Each Round)
```
**ROUND 3 - Initiative Order:**
🗡️ Kira (PC) - HP: 28/35 - [ACTIVE]
⚔️ Goblin Boss - HP: 22/45 - [Bloodied]
🐺 Wolf Companion - HP: 8/11 - [OK]
💀 Goblin 1 - HP: 0/7 - [Defeated]
⚔️ Goblin 2 - HP: 4/7 - [Wounded]
```

## Combatant Types

| Type | Behavior | Cleanup |
|------|----------|---------|
| `pc` | Player controlled, wait for input | Never removed |
| `ally` | AI controlled, fights for party | Never removed |
| `enemy` | AI controlled, hostile | Removed when HP ≤ 0 |
| `neutral` | Non-combatant, may flee | Context dependent |

## Death and Defeat

### Enemy Defeat
- Remove from `combatants` and `initiative_order`
- Keep in `npc_data` only if named/important (mark as dead)
- Roll loot table if boss/special

### PC at 0 HP
- Death saving throws required
- 3 successes = stabilized
- 3 failures = death
- Natural 20 = regain 1 HP
- Natural 1 = 2 failures

## Combat Interrupts

### Conditions for Pausing Combat
- Player requests to negotiate
- Environmental change (collapse, flood, fire)
- Third party intervention
- Player wants to flee

### Fleeing Combat
```json
{
  "combat_state": {
    "in_combat": false,
    "combat_phase": "fled",
    "combat_summary": {
      "outcome": "fled",
      "xp_awarded": 0,
      "consequences": "Enemies may pursue or remember party"
    }
  }
}
```

## Integration with Story Mode

### Returning to Story Mode
After combat ends and rewards are distributed:
1. Clear combat-specific state (but preserve `combat_session_id` for logging)
2. Return narrative control to story mode
3. Describe the aftermath of combat
4. Present non-combat choices to player

### Combat End Transition
```json
{
  "narrative": "With the last goblin falling, silence returns to the dungeon corridor. The acrid smell of battle lingers in the air as you catch your breath, surrounded by the aftermath of the skirmish.",
  "planning_block": {
    "thinking": "Combat concluded successfully. Party can now explore, rest, or continue.",
    "choices": {
      "search_bodies": {"text": "Search the Fallen", "description": "Thoroughly search defeated enemies for loot", "risk_level": "low"},
      "short_rest": {"text": "Take a Short Rest", "description": "Spend 1 hour recovering HP and abilities", "risk_level": "medium"},
      "press_on": {"text": "Press Onward", "description": "Continue deeper into the dungeon", "risk_level": "high"},
      "secure_area": {"text": "Secure the Area", "description": "Check for additional threats and set up a defensive position", "risk_level": "low"}
    }
  },
  "state_updates": {
    "combat_state": {
      "in_combat": false,
      "combat_phase": "ended"
    }
  }
}
```

## Combat Flow Protocol

Uses D&D 5E SRD combat rules. See `dnd_srd_instruction.md` for system authority.

### Combat Log Transparency
At combat start, announce `[COMBAT LOG: ENABLED]` or `[COMBAT LOG: DISABLED]` so players know whether detailed rolls will be shown.

### Pre-Combat
Ask for buffs/preparation when plausible (casting Shield of Faith, drinking a potion, etc.).

### Turn Execution
- **Initiative:** Roll and list order at combat start
- **Turns:** Pause for player input on PC turns, resolve NPC turns with dice rolls
- **Granular Resolution:** Show each action's outcome before proceeding
- **Resource Tracking:** Show remaining spell slots, HP, abilities after each turn

### Combat State Block (Per Combatant)
Display after each round:
```
Name (Level/CR) - HP: X/Y - Status: [conditions]
```

## Combat XP Reference

**XP by Challenge Rating (CR):**
| CR | XP | CR | XP | CR | XP |
|----|----|----|----|----|-----|
| 0 | 10 | 3 | 700 | 8 | 3,900 |
| 1/8 | 25 | 4 | 1,100 | 9 | 5,000 |
| 1/4 | 50 | 5 | 1,800 | 10 | 5,900 |
| 1/2 | 100 | 6 | 2,300 | 11 | 7,200 |
| 1 | 200 | 7 | 2,900 | 12+ | See SRD |
| 2 | 450 | | | | |

**Post-Combat XP Display (MANDATORY):**
```
**COMBAT XP BREAKDOWN:**
- [Enemy Name] (CR X): [XP] XP
- [Enemy Name] (CR Y): [XP] XP
**TOTAL COMBAT XP: [Sum] XP**
```

Report enemy CR in state_updates; include XP award in `player_character_data.experience.current`.

## Combat Commands

| Command | Effect |
|---------|--------|
| `auto combat` | (PLAYER COMMAND ONLY) Resolve entire combat narratively - requires explicit "auto combat" input from player |
| `combat log enable` | Show detailed dice rolls for all combat actions |
| `combat log disable` | Summarize combat without detailed rolls |

**Auto Combat Note:** Only execute auto-combat resolution when player explicitly types "auto combat". Never auto-resolve combat without this explicit command.

## Combat Time Tracking

**Each combat round = 6 seconds of in-game time.**

Update `world_time` accordingly:
- 5-round fight = 30 seconds elapsed
- Combat that lasts 10 rounds = 1 minute elapsed

Include time advancement in state_updates when combat ends.
