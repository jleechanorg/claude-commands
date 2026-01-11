# Character Creation Flow Paths

**Source**: `mvp_site/prompts/character_creation_instruction.md`

This document extracts all possible paths through character creation for comprehensive lifecycle testing.

## Core Principle: TIME FREEZE

**CRITICAL**: World time is FROZEN during character creation/level-up. No story progression, no world changes, no narrative advancement until character mechanics are complete.

## Flow 1: Full Character Creation (New Campaign)

### Trigger Conditions
- `character_creation_in_progress: True` in custom_campaign_state
- Turn 1 of campaign OR user requests character creation
- No complete character exists

### Phase 1: Concept
**Questions**:
- What kind of character do you want to play?
- Any race/class preferences?
- Character concept/backstory ideas?

**Next**: → Phase 2 (Mechanics)

### Phase 2: Mechanics (D&D 5e Rules)

#### Step 2.1: Race Selection
**Options**: PHB races with mechanical benefits
- Dwarf, Elf, Halfling, Human, Dragonborn, Gnome, Half-Elf, Half-Orc, Tiefling
- Each provides: Ability Score Increase, size, speed, languages, racial traits

**Next**: → Step 2.2

#### Step 2.2: Class Selection
**Options**: All 12 D&D 5e classes
- Barbarian (martial, tank, rage)
- Bard (support, versatile, spellcaster)
- Cleric (healer, divine magic)
- Druid (nature magic, wildshape)
- Fighter (martial, versatile)
- Monk (martial arts, mobility)
- Paladin (divine warrior, oaths)
- Ranger (wilderness, ranged combat)
- Rogue (stealth, skills, sneak attack)
- Sorcerer (innate magic, metamagic)
- Warlock (pact magic, patron)
- Wizard (arcane master, spellbook)

**Class-Specific**: Hit die, proficiencies, starting features, spellcasting (if applicable)

**Next**: → Step 2.3

#### Step 2.3: Background Selection
**Options**:
- Standard backgrounds (Acolyte, Criminal, Folk Hero, Noble, Sage, Soldier, etc.)
- Custom background with user approval

**Provides**: Skills, tools, languages, equipment, background feature

**Next**: → Step 2.4

#### Step 2.4: Ability Score Assignment
**PATH A: Standard Array** (Default)
- Values: 15, 14, 13, 12, 10, 8
- Player assigns to: STR, DEX, CON, INT, WIS, CHA
- Apply racial modifiers

**PATH B: Point Buy**
- Start with all scores at 8
- 27 points to spend
- Cost table: 8=0, 9=1, 10=2, 11=3, 12=4, 13=5, 14=7, 15=9
- Max 15 before racial modifiers
- Apply racial modifiers

**PATH C: Custom/Rolled**
- User provides rolled values
- Verify reasonableness (no stat >18 pre-racial, no all 16+)
- Apply racial modifiers

**Next**: → Step 2.5

#### Step 2.5: Starting Equipment
**Options**:
- Class starting package (recommended for speed)
- Individual item selection from class options
- Background equipment added automatically

**Next**: → Phase 3

### Phase 3: Personality & Story

#### Step 3.1: Personality Traits
**Requirement**: 2 personality traits
- Can use background suggestions or custom

**Next**: → Step 3.2

#### Step 3.2: Ideals
**Requirement**: 1 ideal
- Alignment-related: Good, Evil, Lawful, Chaotic, Neutral, Any

**Next**: → Step 3.3

#### Step 3.3: Bonds
**Requirement**: 1 bond
- Connection to people, places, or events

**Next**: → Step 3.4

#### Step 3.4: Flaws
**Requirement**: 1 flaw
- Character weakness or vulnerability

**Next**: → Step 3.5

#### Step 3.5: Backstory (Optional)
**User Choice**: Detailed backstory OR brief summary

**Next**: → Phase 4

### Phase 4: Review & Confirmation

#### Step 4.1: Display Complete Sheet
**Format**: Organized D&D character sheet
- Race, class, level, background
- Ability scores with modifiers
- Skills with proficiencies
- Equipment list
- Personality traits, ideals, bonds, flaws
- Backstory (if provided)

**Next**: → Step 4.2

#### Step 4.2: Confirmation
**User Options**:
- "Looks good" / "I'm done" / "ready to play" → COMPLETE
- "Change [aspect]" → Return to relevant phase
- "Start over" → Return to Phase 1

**Completion**:
- Set `character_creation_in_progress: False`
- Set `level_up_in_progress: False`
- **UNFREEZE TIME**: Story can now progress

## Flow 2: Level-Up (Existing Character)

### Trigger Conditions
- `level_up_in_progress: True` in custom_campaign_state
- Character gained enough XP for next level
- User says "level up" or DM announces level-up

### Step 1: Announce Level-Up
**Display**:
- Congratulations on reaching level X!
- New features available
- **TIME FROZEN** until complete

**Next**: → Step 2

### Step 2: Hit Points
**Calculation**:
- Roll hit die OR take average (class hit die / 2 + 1)
- Add CON modifier
- Add to max HP

**Next**: → Step 3

### Step 3: Class Features
**Display**: New features gained at this level
- Automatic features (proficiency bonus increase, etc.)
- Choice-based features (Fighting Style, Spells Known, etc.)

**Next**: → Step 4

### Step 4: Ability Score Improvement (ASI)
**Trigger**: Levels 4, 8, 12, 16, 19

**PATH A: +2 to one ability OR +1 to two abilities**
- Apply increases (max 20 per ability)

**PATH B: Feat**
- Select from PHB feat list
- Apply feat benefits

**Next**: → Step 5 (if spellcaster) OR Step 7

### Step 5: Spell Selection (Spellcasters Only)
**Varies by class**:
- **Wizards**: Add 2 spells to spellbook
- **Sorcerers/Bards/Rangers**: Swap 1 spell known (if desired)
- **Clerics/Druids**: Full spell list available
- **Warlocks**: Invocations + spell changes

**Next**: → Step 6

### Step 6: Other Caster-Specific
- New spell slots
- Metamagic (Sorcerer)
- Invocations (Warlock)
- Channel Divinity (Cleric/Paladin)

**Next**: → Step 7

### Step 7: Review & Confirmation
**Display**: Updated character sheet with level changes

**User Options**:
- "Done" / "Looks good" → COMPLETE
- "Change [choice]" → Return to relevant step

**Completion**:
- Set `level_up_in_progress: False`
- Set `character_creation_in_progress: False`
- **UNFREEZE TIME**: Story can now progress

## Flow 3: Pre-Defined Character (God Mode Templates)

### Trigger Conditions
- Campaign created with God Mode template
- Template includes complete character data
- `character_creation_in_progress: True` still set

### Step 1: Review Pre-Defined Character
**Display**: Character from template
- All mechanics already defined
- May need personality/backstory

**Next**: → Step 2

### Step 2: Confirm or Customize
**User Options**:
- "Looks perfect" → COMPLETE (skip to Phase 4)
- "I want to change [aspect]" → Jump to relevant phase
- "Tell me more about [class/race]" → Provide info, return to Step 2

**Completion**:
- Set `character_creation_in_progress: False`
- **UNFREEZE TIME**

## Completion Detection

### Explicit Completion Phrases
- "I'm done creating my character"
- "ready to play"
- "let's start the adventure"
- "looks good" / "perfect"
- "done" / "finished"
- "yes, let's go"

### Implicit Completion
- User asks about starting adventure
- User asks "what happens next"
- User makes in-character statement

### Incomplete Indicators
- Questions about mechanics
- "I want to change..."
- "Can I pick a different..."
- "What about [feature]?"

## State Management

### character_creation_in_progress Flag
**Set to True**:
- Campaign creation (if no character exists)
- User requests character creation
- Level-up triggered

**Set to False**:
- Character creation confirmed complete
- Level-up confirmed complete
- User explicitly exits creation mode

### level_up_in_progress Flag
**Set to True**:
- Character reaches level-up XP threshold
- User explicitly requests level-up

**Set to False**:
- Level-up process confirmed complete

## Lifecycle Test Coverage Matrix

| Path | Ability Scores | Class | Special Conditions |
|------|----------------|-------|-------------------|
| 1A   | Standard Array | Fighter | Full creation, equipment package |
| 1B   | Point Buy | Wizard | Full creation, spell selection |
| 1C   | Custom Rolled | Rogue | Full creation, custom background |
| 2A   | (existing) | Barbarian | Level 4 ASI (+2 STR) |
| 2B   | (existing) | Sorcerer | Level 4 Feat (War Caster) |
| 2C   | (existing) | Cleric | Level 5 with new spell slots |
| 3A   | Pre-defined | Paladin | God Mode template, accept as-is |
| 3B   | Pre-defined | Bard | God Mode template, customize class |
| 3C   | Pre-defined | Ranger | God Mode template, change backstory |

## Critical Rules for Tests

1. **TIME FREEZE VERIFICATION**: Assert no story/world changes during character creation
2. **FLAG PERSISTENCE**: `character_creation_in_progress` must stay True until explicit completion
3. **PHASE SEQUENCE**: Tests must hit steps in order (can't skip Phase 2 to jump to Phase 3)
4. **COMPLETION DETECTION**: Tests must verify all completion phrases trigger state transition
5. **CLASS COVERAGE**: All 12 classes must be tested at least once
6. **ABILITY SCORE PATHS**: All 3 paths (Standard/Point Buy/Custom) must be tested
7. **LEVEL-UP PATHS**: ASI and Feat paths must both be tested
8. **SPELLCASTER SPECIAL**: Spellcasters must test spell selection/swapping
