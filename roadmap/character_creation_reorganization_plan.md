# Character Design Reorganization Plan

## Current Issues
- Information scattered across sections
- Planning blocks mentioned early but explained later
- Options separated from their explanations
- State tracking mixed with rules
- Examples dispersed throughout

## New Structure

### 1. Character Creation Overview
- When mechanics are enabled, character creation is mandatory
- Purpose: Establish player character with D&D 5e mechanics
- Process flow: Recognition → Options → Creation → Approval → Story

### 2. Core Rules (Apply to ALL paths)
- **Planning Block Requirement**: End EVERY response with planning block
- **Input Handling**: Numeric responses = selections from lists
- **Character Recognition**: Check if character specified in prompt
- **Final Approval**: MANDATORY step before starting story
- **Complete Display**: ALWAYS show full character sheet

### 3. Initial Character Recognition

#### When Character IS Specified:
```
I see you want to play as [CHARACTER NAME]. Let's design [CHARACTER NAME] with D&D 5e mechanics!

How would you like to design [CHARACTER NAME]:
1. **AIGenerated** - I'll create a complete D&D version based on their lore
2. **StandardDND** - You choose from D&D races and classes  
3. **CustomClass** - We'll create custom mechanics for their unique abilities

Which option would you prefer? (1, 2, or 3)
```

#### When Character is NOT Specified:
```
Welcome, adventurer! Let's design your character for this campaign.

How would you like to create your character:
1. **AIGenerated** - I'll design a character perfect for this setting
2. **StandardDND** - Choose from established D&D races and classes
3. **CustomClass** - Design your own unique character concept

Which option would you prefer? (1, 2, or 3)
```

### 4. The Three Creation Paths

#### Path 1: AIGenerated
**Purpose**: Quick character creation with AI designing everything
**Process**:
1. Player selects option 1
2. AI creates complete character based on setting/prompt
3. Present FULL character sheet
4. Explain design choices
5. Ask for approval/changes

**Character Sheet Format**:
```
**CHARACTER SHEET**
Name: [Character Name]
Race: [Race] | Class: [Class] | Level: 1
Background: [Background]

**Ability Scores:**
STR: 15 (+2) | DEX: 14 (+2) | CON: 13 (+1)
INT: 8 (-1) | WIS: 12 (+1) | CHA: 10 (+0)

**Skills:** [List all proficient skills]
**Equipment:** [Detailed equipment list]

**Backstory:**
[2-3 paragraph backstory]

**Why This Character:**
[Explanation of design choices]
```

#### Path 2: StandardDND
**Purpose**: Traditional D&D character creation step-by-step
**Process**:
1. Player selects option 2
2. Present race options (if not obvious from character)
3. Present class options
4. Assign ability scores (standard array)
5. Select background
6. Name and details
7. Final approval

**Step Example**:
```
[CHARACTER CREATION - Step 2 of 7]

You've selected Human as your race. Now let's choose your class:

1. **Fighter** - Master of martial combat
2. **Wizard** - Student of arcane magic
3. **Rogue** - Expert in stealth and skill
[etc...]

--- PLANNING BLOCK ---
What would you like to do?
1. **[Fighter]:** Choose the Fighter class
2. **[Wizard]:** Choose the Wizard class
3. **[Rogue]:** Choose the Rogue class
4. **[Other]:** See more class options
```

#### Path 3: CustomClass
**Purpose**: Create unique character concepts outside standard D&D
**Process**:
1. Player selects option 3
2. Discuss custom concept
3. Design mechanics collaboratively
4. Balance abilities
5. Create full character sheet
6. Final approval

### 5. Universal Requirements

#### Final Approval Step (MANDATORY)
```
[Present complete character sheet]

Would you like to:
1. **Play as this character** - Begin the adventure!
2. **Make changes** - Tell me what you'd like to adjust
3. **Start over** - Design a completely different character

What is your choice? (1, 2, or 3)

--- PLANNING BLOCK ---
What would you like to do?
1. **[Approve]:** Start playing with this character
2. **[Modify]:** Request specific changes
3. **[Restart]:** Begin character creation again
4. **[Other]:** Ask questions about the character
```

#### Planning Block Format
Every response during character creation MUST end with:
```
--- PLANNING BLOCK ---
What would you like to do?
[Numbered options relevant to current step]
```

### 6. Character Resources & Equipment
[Keep existing tables for backgrounds, equipment, etc.]

### 7. Quick Reference Checklist
✅ ALWAYS show complete character sheet for AIGenerated
✅ ALWAYS end with planning block
✅ ALWAYS include final approval step
✅ ALWAYS use numeric input for selections
❌ NEVER skip ability scores or equipment
❌ NEVER start story without approval
❌ NEVER ignore specified characters
❌ NEVER substitute names without consent