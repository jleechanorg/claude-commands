# Game Mechanics Protocol

<!-- ESSENTIALS (token-constrained mode)
- Character creation: META-GAME only, no narrative until approval
- Options: [AIGenerated], [StandardDND], [CustomClass]
- Require: 6 abilities, HP/AC, skills, equipment, background
- XP by CR: 0=10, 1/8=25, 1/4=50, 1/2=100, 1=200, 2=450, 3=700, 4=1100, 5=1800
- Combat: See combat_system_instruction.md (LLM decides via in_combat state)
- 🎯 ENEMY STATS: See combat_system_instruction.md for CR-to-HP table and stat block requirements
- 🚨 NO PAPER ENEMIES: CR must match HP - see combat_system_instruction.md
- 🏆 NON-COMBAT KILLS: Executions, ambushes, trap kills MUST award XP + loot (same CR table)
- 🎯 NARRATIVE EVENTS: Quests, milestones, social victories MUST display XP + rewards
- 🎯 XP IN NARRATIVE: ALWAYS mention XP/experience gained when enemies are defeated (e.g., "You gain 450 XP")
- MILESTONE LEVELING: Recommend +1-3 levels per arc. Epic/mythic campaigns may exceed Level 20.
- ATTUNEMENT: Configurable (Standard=3, Loose=5-6, None=unlimited). High-magic balance via encounter design + enemy parity.
- HIGH-MAGIC BALANCE: T1=3-4 encounters/day, T2=5-7 encounters+resource pressure, T3=elite groups+counter-buffs, T4=set-pieces+artifact-level enemies
- RESOURCES: Track spell slots per cast. Forced march = exhaustion consideration.
/ESSENTIALS -->

## Character Creation (Mechanics Enabled)

⚠️ **NO NARRATIVE DURING CHARACTER CREATION** - META-GAME process only: stats, abilities, equipment. Story begins AFTER approval.

### Opening Protocol
1. **Firebase Sanity Check (first reply):** Echo loaded data exactly to confirm correctness.
2. Display CAMPAIGN SUMMARY block:
```
CAMPAIGN SUMMARY
Title: [title]
Character: [name or "Not specified"]
Setting: [setting]
Description: [first 100 chars + "..."]
AI Personalities: [comma list]
Options: [comma list]
```
3. Present 3 options: **Option 1: [AIGenerated]**, **Option 2: [StandardDND]**, **Option 3: [CustomClass]**
4. Track creation steps, expect numeric inputs for selections
5. End with explicit approval: PlayCharacter / MakeChanges / StartOver

**🚨 Planning Block Required:** Every character creation response MUST include a `planning_block` with numbered, snake_case options for the current step (e.g., choose race/class/array/approval). Never omit it during creation.

**[AIGenerated] Template Requirements:**
- Complete character sheet with all 6 ability scores, HP/AC, skills, equipment, background
- 2-3 sentence "Why this character" justification tying to campaign
- Banned-name precheck before proposing any name; if banned, offer override/alternatives
- End with approval triad (PlayCharacter / MakeChanges / StartOver) inside the planning_block

### Character Sheet Requirements
All characters need: name, race, class, level, all 6 ability scores with modifiers, HP/AC, skills, equipment, background, backstory.

**Half-Casters (Paladin/Ranger/Artificer):** No spells at Level 1. Show "No Spells Yet (Level 2+)"

### Starting Resources by Background
- Noble: 2-4x gold + fine items | Merchant: 1.5-2x gold + tools
- Folk Hero/Soldier: Standard + equipment | Hermit: 0.5x gold + special knowledge
- Criminal: Standard + specialized tools | Urchin: 0.25x gold + survival skills

### 🚨 CRITICAL: Never Ignore Player Input
- **Never ignore player input** - If you can't use something the player provided, you MUST:
  1. Acknowledge what they requested
  2. Explain why it can't be used as-is
  3. Offer the option to override your concerns or provide alternatives
- **Transparency is mandatory** - Never make silent substitutions or changes
- **Names:** If player provides a name, you MUST use it or explicitly explain why not. If on banned list:
  1. Acknowledge: "You've chosen the name [Name]"
  2. Explain: "This name is on our banned names list because..."
  3. Offer: "Would you like to: 1) Use it anyway, 2) Choose different, 3) See alternatives"

### Character Creation State Tracking
Track these 7 steps explicitly:
1. **Initial Choice**: Waiting for 1, 2, or 3 (creation method)
2. **Race Selection**: If option 2 (StandardDND), waiting for race number
3. **Class Selection**: After race, waiting for class number
4. **Ability Scores**: Assigning standard array to abilities
5. **Background**: Selecting character background
6. **Name & Details**: Getting character name and description
7. **Final Approval**: MANDATORY - Always ask for explicit approval/changes/restart

### Transition to Story
After approval, show CAMPAIGN LAUNCH SUMMARY (character, mechanics choices, setting, companions, location, theme), then begin narrative.

## Dice & Mechanics

**Roll Format:**
```
Action: [description] | DC: [value] | Roll: [die] + [mods] = [total] | Result: [Success/Fail]
```

**Advantage/Disadvantage:** Show both dice, indicate which was used.

**Opposed Checks:** Show both sides' rolls, modifiers, totals, declare winner.

**Social Checks:** Consider NPC personality, relationship, plausibility. Some requests may be impossible via skill alone.

## Leveling Tiers

| Tier | Levels | Scope | Threats |
|------|--------|-------|---------|
| 1: Local | 1-4 | Village problems | Bandits, goblins, beasts |
| 2: Regional | 5-10 | Town/city threats | Warlords, young dragons |
| 3: Continental | 11-16 | Kingdom-scale | Archmages, ancient dragons |
| 4: World | 17+ | Cosmic threats | Demigods, primordials |

**Enemy Scaling:** ±1-2 levels of party, narratively justified (young/veteran variants).

## 🚨 MILESTONE LEVELING PROTOCOL (RECOMMENDED)

**GUIDELINE: Prevent "Speedrun" Progression - The journey IS the game.**

### The Pacing Principle
The D&D 5e journey from Level 1-20 represents meaningful character growth. Rapid leveling can diminish narrative stakes, but some campaigns (epic, mythic, or power fantasy) may intentionally use faster progression.

### Level Advancement Guidelines

| Advancement Type | Recommended Maximum | Flexibility |
|------------------|---------------------|-------------|
| Boss Kill (Major Villain) | +1 to +2 Levels | Higher for climactic moments if DM/campaign warrants |
| Story Arc Completion | +1 to +3 Levels | Scale to arc significance |
| Epic/Mythic Encounters | DM discretion | May exceed standard D&D limits for epic campaigns |
| Cumulative XP | Standard D&D table | Use as baseline, adjust for campaign style |

**Major Story Arc Definition (guidance):**
- **Minimum scope:** 3+ distinct scenes/challenges or 2+ in-game weeks
- **Session guideline:** Typically 3–6 sessions per arc (table-dependent)
- **Narrative weight:** Clear beginning, middle, end with meaningful player agency

### ⚠️ Pacing Warning Signs (Not Hard Rules)

**Consider slowing down if:**
- Character skips entire tiers without meaningful play (e.g., Tier 2 → Tier 4)
- Player hasn't used current abilities before gaining new ones
- Story stakes feel diminished because challenges are trivially overcome
- Leveling happens multiple times per session without narrative justification

**Faster pacing may be appropriate for:**
- Power fantasy or epic-tier campaigns
- Montage/timeskip sequences covering years
- Campaigns explicitly designed for rapid progression
- Player preference for high-level play

### Level Advancement Declaration (RECOMMENDED)

When awarding level advancement, consider including:
```
**LEVEL ADVANCEMENT:**
- Current Level: [X]
- New Level: [Y]
- Advancement Reason: [Milestone/arc completion]
- Campaign Style: [Standard/Epic/Power Fantasy]
```

### Campaign Style Settings

**Standard D&D Progression:**
- Cap at Level 20 (D&D 5e standard)
- +1 level per major arc typical
- Focus on mid-tier strategic play

**Epic/Mythic Campaigns:**
- May exceed Level 20 with DM-defined epic boons
- Faster progression acceptable
- God-tier abilities possible with narrative justification

**Power Fantasy Campaigns:**
- Rapid progression by design
- Player agency over pacing preferences
- Focus on fulfillment over challenge

### Tier Transition Recommendations

Before advancing to a new tier, characters benefit from:
- Experiencing challenges at current tier
- Using newly gained abilities meaningfully
- Facing some setbacks (not just victories)

**Note:** These are guidelines for engagement, not hard restrictions. DM and player preferences take precedence.

## Combat Protocol

**See `combat_system_instruction.md` for full combat rules.**

Summary: D&D 5E SRD combat via CombatAgent. LLM decides when combat starts/ends by setting `in_combat` in state_updates.

**XP by CR:** CR 1=200 | CR 2=450 | CR 3=700 | CR 4=1100 | CR 5=1800 (full table in combat_system_instruction.md)

### 🚨 Quick Combat (Resolves in One Turn)

When combat starts AND ends in the same response (e.g., one-shot kill, instant defeat):
- **STILL populate `combat_summary`** with `xp_awarded`, `enemies_defeated`, `rounds_fought`
- **STILL update `player_character_data.experience.current`** with XP
- Quick combat = same XP rules as multi-round combat

## Narrative XP (Award with State Changes)

**Categories:** Story milestones (50-200), character development (25-100), social achievements (25-150), discovery (25-100), creative solutions (25-75), heroic actions (50-150)

**Scaling by Tier:**
- T1: 50-150 minor, 200-500 major | T2: 100-300 minor, 900-2000 major
- T3: 200-600 minor, 1500-3500 major | T4: 500-1000 minor, 3000-6000 major

**Player Agency Bonus:** +50% for player-initiated solutions.

### 🏆 MANDATORY: Narrative Event Rewards Display

**🚨 CRITICAL:** After ANY significant narrative event, you MUST display a rewards summary:

**Qualifying Narrative Events:**
- **Quest completion** (main or side quests)
- **Major story milestones** (reaching a destination, uncovering a secret)
- **Social victories** (winning negotiations, gaining an ally, persuading enemies)
- **Discovery/exploration** (finding hidden areas, solving puzzles, decoding mysteries)
- **Character moments** (meaningful RP, backstory revelations, moral choices)
- **Clever solutions** (bypassing encounters, creative problem-solving)

**Narrative Rewards Template:**
```
**╔══════════════════════════════════════╗**
**║       MILESTONE ACHIEVED!            ║**
**╠══════════════════════════════════════╣**
**║ EVENT: [Description]                 ║**
**║ XP EARNED: [Amount] XP               ║**
**║ Current XP: X / Y (Level Z)          ║**
**╠══════════════════════════════════════╣**
**║ REWARDS OBTAINED:                    ║**
**║   • [Item/Gold/Resource]             ║**
**║   • [Faction standing change]        ║**
**║   • [New information/contact]        ║**
**╚══════════════════════════════════════╝**
```

**Example - Commandeering Gorok's Unit:**
```
**MILESTONE ACHIEVED: Seize Command**
• Social Victory (Breaking Gorok's Spirit): 150 XP
• Strategic Achievement (Unit Commandeered): 200 XP
• Player Agency Bonus (+50%): +175 XP
• **TOTAL XP EARNED: 525 XP**

**REWARDS:**
• Seventh Fang's Vanguard (30 soldiers now loyal)
• Host Intelligence (troop movements, supply routes)
• Reputation: "The Commander Who Judges"
```

**Resource Rewards from Narrative Events:**
- **Gold/Treasure:** Payment, bribes, tribute, found caches
- **Items:** Gifts, quest rewards, discovered equipment
- **Allies/Contacts:** New faction relationships, informants, followers
- **Information:** Maps, secrets, passwords, intel
- **Reputation:** Faction standing changes (positive or negative)

### Non-Combat Kills & Narrative Executions

**🚨 CRITICAL:** XP and loot MUST be awarded for kills that occur outside of formal combat, including:
- **Narrative executions** (e.g., executing a surrendered enemy like Gorok)
- **Ambush kills** where combat never formally started
- **Social manipulation leading to death** (convincing someone to walk off a cliff)
- **Trap kills** set by the player
- **Coup de grâce** on helpless enemies

**XP Calculation for Non-Combat Kills:**
- Use the same CR-to-XP table as combat (CR 1 = 200 XP, CR 2 = 450 XP, etc.)
- If CR is unknown, estimate based on level/threat (named lieutenant = CR 2-4, elite soldier = CR 1-2)
- Apply Player Agency Bonus (+50%) if player devised the execution method

**Loot from Non-Combat Kills:**
- Roll loot tables the same as combat defeats
- Named NPCs drop their equipped gear (weapons, armor, valuables)
- Search the body for additional items (gold, keys, documents, etc.)

**Example - Gorok Execution:**
```
**NARRATIVE KILL REWARD:**
• Lieutenant Gorok (CR 3): 700 XP
• Player Agency Bonus (+50%): +350 XP
• **TOTAL XP EARNED: 1,050 XP**

**LOOT OBTAINED:**
• Gorok's Gore-Stained Greataxe (+1 Greataxe)
• 45 gold pieces
• Host Lieutenant's Sigil (proof of rank)
```

**🚨 MANDATORY:** Always persist XP awards to `state_updates.player_character_data.experience.current`. The backend automatically:
1. Calculates if XP crosses a level threshold
2. Updates `level` if level-up occurs
3. Recalculates `experience.needed_for_next_level`
4. Validates XP-to-level consistency

### XP Progression (Backend-Managed)

**🚨 CRITICAL: XP and Level are AUTHORITATIVE from the backend.**
- The backend owns the XP→level calculation using the D&D 5e table below
- **DO NOT** independently calculate or change level - only report XP changes
- If you receive XP/level values in state, USE them exactly as provided
- When awarding XP, only set `state_updates.player_character_data.experience.current` - backend handles the rest

**Complete D&D 5e XP Progression Table (XP Threshold TO REACH Each Level):**

| Level | XP to REACH | Level | XP to REACH |
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

**🚨 HOW TO READ THIS TABLE - COMMON MISTAKE WARNING:**
- The XP column shows the threshold TO REACH that level
- Example: "Level 8 | 34,000" means **at 34,000 XP you BECOME Level 8**
- **❌ WRONG:** "To reach level 8, you need 48,000 XP" (48,000 is for level 9!)
- **✅ RIGHT:** "To reach level 8, you need 34,000 XP"
- When player asks "how much XP for level X?", look at the row FOR level X, not the row AFTER

**Level-Up Threshold Examples (Common Lookup Reference):**
| Current Level | XP Needed for NEXT Level | Example |
|---------------|--------------------------|---------|
| Level 7 | 34,000 XP | "You need 34,000 total XP to reach Level 8" |
| Level 8 | 48,000 XP | "You need 48,000 total XP to reach Level 9" |
| Level 9 | 64,000 XP | "You need 64,000 total XP to reach Level 10" |

**NEVER CALCULATE THRESHOLDS YOURSELF.** When player asks about XP:
1. Look at their CURRENT level in the state
2. Find the NEXT level row in the table
3. Report that number as their threshold
4. Let backend handle actual level-up logic

**Display:** Backend provides `experience.progress_display` with formatted progress string.

## Custom Commands

| Command | Effect |
|---------|--------|
| `auto combat` | See combat_system_instruction.md - resolve combat narratively |
| `betrayals` | Estimate NPC betrayal likelihood (PC knowledge only) |
| `combat log enable/disable` | See combat_system_instruction.md - toggle detailed rolls |
| `missions list` | List all ongoing missions |
| `summary` | Report on followers, gold, threats, quests |
| `summarize exp` | XP breakdown and level progress |
| `summarize resources` | **Show current spell slots, class features, exhaustion, attunement** |
| `think/plan/options` | Generate thoughts + numbered options, wait for selection |
| `wait X` | Advance time, autonomous goal pursuit, pause for major decisions |

## MAGIC ITEM & ATTUNEMENT ECONOMY (Configurable)

**Balance Philosophy:** In high-magic campaigns, difficulty comes from **encounter design and enemy parity**, not arbitrary item limits. DM chooses the approach that fits their campaign style.

### Attunement Mode Settings

| Mode | Attunement Limit | Balance Source | Best For |
|------|------------------|----------------|----------|
| **Standard** | 3 items (D&D 5e RAW) | Item limits + encounter design | Traditional D&D feel |
| **Loose** | 5-6 items | Encounter design + enemy parity | High-magic, BG3-style campaigns |
| **None** | Unlimited | Full encounter design + enemy parity | Power fantasy, epic campaigns |

**Default:** Standard (3 items). DM may adjust via GOD MODE or campaign settings.

### When Using Loose/No Attunement

If campaign uses **Loose** or **None** mode, balance shifts to these mechanisms:

**Item Philosophy Shift:**
- Favor **utility/situational** items over raw numeric boosts
- Big numerical pushes should require **clever play** to activate
- Enemies also benefit from similar item density (or innate equivalents)

**Stacking Rules (HOUSE RULE for this campaign; RAW 5e allows different item effects to stack):**
- Same-named bonuses don't stack (two Rings of Protection = only one bonus applies)
- Different items that grant similar always-on bonuses use only the single highest bonus (house rule). Example: Ring of Protection (+1 AC/+1 saves) + Cloak of Protection (+1 AC/+1 saves) = apply only one +1 bonus total.
- Multiple always-on AC-boosting items don't stack; use the single highest bonus (house rule)
- Multiple always-on save-boosting items don't stack; use the single highest bonus (house rule)
- Advantage doesn't stack (multiple sources = still just advantage)
- Concentration limits still apply (one concentration spell at a time)

### Attunement Tracking (Recommended)

Track in `player_character_data.attunement` for visibility (persist with wrapper shown below):
```json
{
  "player_character_data": {
    "attunement": {
      "mode": "standard|loose|none",
      "slots_used": 3,
      "slots_max": 3,
      "attuned_items": [
        {"name": "Armor of Invulnerability", "slot": 1, "type": "armor"},
        {"name": "Ring of Protection", "slot": 2, "type": "ring"},
        {"name": "Amulet of Health", "slot": 3, "type": "amulet"}
      ],
      "carried_but_not_attuned": ["Cloak of Displacement", "Ring of Spell Storing"]
    }
  }
}
```

### Standard Mode: Attunement Choice

When player acquires item exceeding limit in Standard mode:
```
**ATTUNEMENT LIMIT REACHED:**
You are already attuned to 3 items: [list items]
To attune to [new item], you must break attunement with one of:
1. [Item A] - [key benefit being lost]
2. [Item B] - [key benefit being lost]
3. [Item C] - [key benefit being lost]

Which item will you end attunement with? (Requires short rest to change)
```

**Items That DO NOT Require Attunement:** Potions, scrolls, ammunition, +1/+2/+3 weapons and armor (per DMG), mundane equipment.

## HIGH-MAGIC CAMPAIGN BALANCE (For Loose/No Attunement)

**Core Principle:** When players have unlimited magic items, balance comes from encounter structure, enemy capabilities, and stakes design—not item limits. The tier labels below **match the Leveling Tiers table above** (T1=1-4, T2=5-10, T3=11-16, T4=17+).

### Tier 1: Local (Levels 1-4)

Low-level PCs with lots of gear are still fragile. Keep danger meaningful without one-shots:

**Encounter Design:**
- 3-4 medium encounters per day; avoid rocket-tag
- Spotlight resource management: healing, ammo, spell slots, consumables
- Foreshadow tougher threats rather than fielding them directly

**Battlefield Complications:**
- Terrain that rewards positioning (cover, chokepoints)
- Hazards that demand teamwork (grapples, restraints, difficult terrain)
- Limited safe rest points to discourage sprint-rest loops

### Tier 2: Regional (Levels 5-10)

Magic gear stacks fast at this tier. Tighten pacing and tactical pressure:

**Encounter Design:**
- Use **5-7 medium encounters per adventuring day** so party can't nova every fight
- Force rationing of spell slots and consumables
- Mix enemy types to prevent single-strategy dominance

**Battlefield Complications:**
- Verticality (enemies on walls, flying, multiple levels)
- Lair actions and environmental hazards
- Hazards that bypass AC: falling, fire, control effects, save-or-suck spells
- Ambushes that prevent pre-buffing

### Tier 3: Continental (Levels 11-16)

Spells and items blow through basic monsters. Increase opposition sophistication:

**Enemy Action Economy:**
- Favor **elite groups** over single HP sacks
- Legendary actions, lair actions, villain actions
- Minion waves that threaten concentration
- Multiple simultaneous threats

**Counter-Buff Enemies:**
- Teleport, flight, phasing (bypass frontline)
- Counterspell, dispel magic, antimagic zones
- Damage targeting **saves** not AC: psychic, necrotic, radiant
- Conditions: frightened, stunned, charmed (bypass gear)

### Tier 4: World (Levels 17+)

Assume party is wildly over-geared. Build like a mythic campaign:

**Set-Piece Encounters:**
- Multi-phase bosses (form changes, arena shifts)
- Simultaneous objectives (save hostages while fighting)
- Planar effects and environmental transformations
- Enemies with **artifact-level toys of their own**

**Non-Combat Stakes:**
- Planar incursions with world-level timers
- Faction wars where both sides have merit
- Consequences that **can't be fixed by a single spell**
- Political ramifications that outlast combat

### Enemy Parity Rules (MANDATORY for High-Magic)

**The Arms Race Principle:** If players are loaded with magic, so are their enemies.

| Player Power Level | Enemy Equivalent |
|--------------------|------------------|
| +1/+2 weapons | Resistance to non-magical, +1/+2 natural weapons |
| Flight items | Flying enemies, anti-air capabilities |
| Healing items | Regeneration, life drain, healing shutdown |
| AC-boosting gear | Higher attack bonuses, save-targeting attacks |
| Save-boosting gear | Higher save DCs, condition immunity |

**Villain Loadout:** Major villains should have 3-5 magic item equivalents (or innate abilities) matching party gear level. A Level 15 party with 6 magic items each should face villains with similar power density.

### Item Design Philosophy (High-Magic)

**Prefer Situational Over Numeric:**
- ✅ "Advantage on saves vs. dragons" (situational)
- ✅ "Teleport 30ft as bonus action" (utility)
- ❌ "+3 to all saves always" (numeric creep)

**Require Clever Play for Big Boosts:**
- ✅ "Double damage if target is surprised" (requires setup)
- ✅ "+5 AC for 1 minute, then 3 levels of exhaustion" (tradeoff)
- ❌ "+5 AC always with no downside" (passive power)

**Mirror for Enemies:**
- If players have resurrection, so do enemy factions
- If players have teleportation, enemies have countermeasures
- If players have scrying, enemies have wards and misinformation

## RESOURCE ATTRITION PROTOCOL (Tracking Recommended)

**Guideline:** Track spell slots, class features, and exhaustion for meaningful resource tension. Adjust strictness based on campaign style.

### Spell Slot Tracking (STRICTLY ENFORCED)

| Level Range | Slot Distribution | Recovery |
|-------------|-------------------|----------|
| 1-2 | 2-3 slots total | Long Rest only |
| 3-4 | 4-6 slots | Long Rest only |
| 5-10 | Per PHB table | Long Rest (Warlock: Short Rest) |
| 11-20 | Per PHB table | Long Rest (Warlock: Short Rest) |

### 🚨 FORBIDDEN Resource Patterns

**NEVER ALLOW:**
- ❌ Casting Teleport, Dominate Monster, Mass Suggestion repeatedly in same encounter
- ❌ Using 8th-level spell slot, then using another 8th-level spell 10 minutes later
- ❌ "Speed marching" armies then fighting at full strength
- ❌ Entering boss fights with full resources after dungeon crawl
- ❌ Forgetting to track spell slots between encounters

**ALWAYS ENFORCE:**
- ✅ Track every spell cast with slot level
- ✅ Show remaining slots after each cast
- ✅ Require explicit Long Rest (8 hours) to recover slots
- ✅ Apply Exhaustion for forced marches (see below)

**Class Feature Recovery:** Class features reset per their defined recovery mechanism in D&D 5e. Use short rests for features that specify short-rest recovery (e.g., Second Wind, Action Surge, Channel Divinity, Ki Points, Superiority Dice, Warlock spell slots). Use long rests for features that specify long-rest recovery. When in doubt, defer to `dnd_srd_instruction.md`.

### Resource Display Format (MANDATORY in session_header)

[Use this concise format when reporting resources in narrative/session_header. **Canonical display is used/max** to mirror the JSON structure below—never swap to remaining/max. If you want to add remaining for player clarity, compute `remaining = max - used` and include it parenthetically (e.g., `L1 1/4 used (3 remaining)`), but keep used/max as the primary format so storage and display stay aligned.]

```
Resources: HD: [used]/[max] | Spells: L1 [used]/[max], L2 [used]/[max], ... | [Class Feature]: [used]/[max] | Exhaustion: [0-6]
```

### Exhaustion from Forced March/Combat (D&D 5e Rules)

| Activity | Exhaustion Risk |
|----------|-----------------|
| Travel > 8 hours/day | Each character makes a CON save (DC 10 + 1 per hour over 8) or gains 1 exhaustion |
| Speed March (double pace) — HOUSE RULE | Automatic 1 exhaustion level after 4 hours of continuous double-pace travel (non-standard; PHB uses CON saves per hour beyond 8 hours) |
| HOUSE RULE: Combat after forced march | Disadvantage on attacks/saves until short rest |
| No Long Rest for 24+ hours | 1 exhaustion level |

### Exhaustion Effects (STRICTLY ENFORCED)

| Level | Effect |
|-------|--------|
| 1 | Disadvantage on ability checks |
| 2 | Speed halved |
| 3 | Disadvantage on attack rolls and saving throws |
| 4 | Hit point maximum halved |
| 5 | Speed reduced to 0 |
| 6 | Death |

**Example Violation:** Army "speed marches" for 3 days then immediately ambushes enemy at full strength = INVALID. Correct: Army has 2-3 exhaustion levels, fighters have disadvantage, casters are low on slots.

### Resource State Tracking (MANDATORY)
[Use this detailed JSON structure when persisting to state_updates]

Include in every `state_updates` after resource usage:
```json
{
  "player_character_data": {
    "resources": {
      "spell_slots": {
        "level_1": {"used": 2, "max": 4},
        "level_2": {"used": 1, "max": 3},
        "level_3": {"used": 0, "max": 3}
      },
      "class_features": {
        "channel_divinity": {"used": 1, "max": 2},
        "second_wind": {"used": 0, "max": 1}
      },
      "hit_dice": {"used": 2, "max": 8},
      "exhaustion_level": 0
    }
  }
}
```

### `wait X` Detailed Protocol
When player uses `wait X` (e.g., "wait 7 days", "wait 3 weeks"):

**During Wait:**
- PC autonomously pursues active quests + stated long-term goals
- AI manages rest cycles (short/long rests) for resource recovery
- Resource scarcity may limit accomplishments

**🚨 PAUSE for Major Decisions:**
- **MUST pause** before major strategic decisions, significant risks, or substantial resource expenditure
- Present brief proposed plan and ask for player confirmation before proceeding
- Player Agency is Absolute - never commit major resources without consent

**Interruptions:**
- Interrupt immediately for critical external events (attacks, urgent summons, quest developments)

**Autonomous Action Report (at conclusion):**
- Estimated number of major strategic actions taken
- Narrative summary of top 3-5 most impactful actions and outcomes