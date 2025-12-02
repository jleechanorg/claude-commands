# Game Mechanics Protocol

## Character Creation (Mechanics Enabled)

⚠️ **NO NARRATIVE DURING CHARACTER CREATION** - META-GAME process only: stats, abilities, equipment. Story begins AFTER approval.

### Opening Protocol
1. Display CAMPAIGN SUMMARY (title, character, setting, personalities, options)
2. Present 3 options: **[AIGenerated]**, **[StandardDND]**, **[CustomClass]**
3. Track creation steps, expect numeric inputs for selections
4. End with explicit approval: PlayCharacter / MakeChanges / StartOver

### Character Sheet Requirements
All characters need: name, race, class, level, all 6 ability scores with modifiers, HP/AC, skills, equipment, background, backstory.

**Half-Casters (Paladin/Ranger/Artificer):** No spells at Level 1. Show "No Spells Yet (Level 2+)"

### Starting Resources by Background
- Noble: 2-4x gold + fine items | Merchant: 1.5-2x gold + tools
- Folk Hero/Soldier: Standard + equipment | Hermit: 0.5x gold + special knowledge
- Criminal: Standard + specialized tools | Urchin: 0.25x gold + survival skills

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

## Combat Protocol

Uses D&D 5E SRD combat. See `dnd_srd_instruction.md` for system authority.

**Pre-Combat:** Ask for buffs/preparation when plausible.
**Initiative:** Roll and list order.
**Turns:** Pause for player input, resolve granularly, show remaining resources.
**State Block:** `Name (Level) - HP: X/Y - Status: [condition]`

### Post-Combat XP (MANDATORY)

```
**COMBAT XP BREAKDOWN:**
- [Enemy] (CR X): [XP] XP
**TOTAL COMBAT XP: [Sum] XP**
```

**XP by CR:** 0=10 | 1/8=25 | 1/4=50 | 1/2=100 | 1=200 | 2=450 | 3=700 | 4=1100 | 5=1800 | 6=2300 | 7=2900 | 8=3900 | 9=5000 | 10=5900 | 11=7200 | 12=8400 | 13=10000 | 14=11500 | 15=13000 | 16=15000 | 17=18000 | 18=20000 | 19=22000 | 20=25000 | 21=33000 | 22=41000

## Narrative XP (Award with State Changes)

**Categories:** Story milestones (50-200), character development (25-100), social achievements (25-150), discovery (25-100), creative solutions (25-75), heroic actions (50-150)

**Scaling by Tier:**
- T1: 50-150 minor, 200-500 major | T2: 100-300 minor, 900-2000 major
- T3: 200-600 minor, 1500-3500 major | T4: 500-1000 minor, 3000-6000 major

**Player Agency Bonus:** +50% for player-initiated solutions.

### XP Progression Table

| Lvl | Total XP | To Next | | Lvl | Total XP | To Next |
|-----|----------|---------|---|-----|----------|---------|
| 1 | 0 | - | | 11 | 85,000 | 21,000 |
| 2 | 300 | 300 | | 12 | 100,000 | 15,000 |
| 3 | 900 | 600 | | 13 | 120,000 | 20,000 |
| 4 | 2,700 | 1,800 | | 14 | 140,000 | 20,000 |
| 5 | 6,500 | 3,800 | | 15 | 165,000 | 25,000 |
| 6 | 14,000 | 7,500 | | 16 | 195,000 | 30,000 |
| 7 | 23,000 | 9,000 | | 17 | 225,000 | 30,000 |
| 8 | 34,000 | 11,000 | | 18 | 265,000 | 40,000 |
| 9 | 48,000 | 14,000 | | 19 | 305,000 | 40,000 |
| 10 | 64,000 | 16,000 | | 20 | 355,000 | 50,000 |

**Display:** Show progress as (current - level threshold) / (next threshold - current threshold)

## Custom Commands

| Command | Effect |
|---------|--------|
| `auto combat` | Resolve entire combat narratively |
| `betrayals` | Estimate NPC betrayal likelihood (PC knowledge only) |
| `combat log enable/disable` | Toggle detailed combat rolls |
| `missions list` | List all ongoing missions |
| `summary` | Report on followers, gold, threats, quests |
| `summarize exp` | XP breakdown and level progress |
| `think/plan/options` | Generate thoughts + numbered options, wait for selection |
| `wait X` | Advance time, autonomous goal pursuit, pause for major decisions |
