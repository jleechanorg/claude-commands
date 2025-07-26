# Character Sheet Template

This document defines the mechanical attributes of a character in the game. It must be filled out completely for the Player Character (PC) and all significant NPCs who might engage in combat or skill-based challenges.

<!--
SYSTEM CONSTANTS: This template references attribute systems defined in constants.py:
- ATTRIBUTE_SYSTEM_DND = "D&D"
- ATTRIBUTE_SYSTEM_DESTINY = "Destiny"
- DEFAULT_ATTRIBUTE_SYSTEM = "Destiny"
See constants.py for complete attribute lists and helper functions.
-->

## Campaign Configuration
- **Active Attribute System:** [D&D / Destiny]
  - *Set at campaign creation and locked thereafter*
  - *All characters in this campaign use the same system*

---

## I. Core Attributes
*Only ONE of the following sections should be populated based on Active Attribute System*

### Option A: D&D System (If Active System = D&D)
- **Strength (STR):** [Score] (Modifier: [+/-X])
- **Dexterity (DEX):** [Score] (Modifier: [+/-X])
- **Constitution (CON):** [Score] (Modifier: [+/-X])
- **Intelligence (INT):** [Score] (Modifier: [+/-X])
- **Wisdom (WIS):** [Score] (Modifier: [+/-X])
- **Charisma (CHA):** [Score] (Modifier: [+/-X])

### Option B: Destiny System (If Active System = Destiny)
- **Physique:** [Score] (Modifier: [+/-X])
- **Coordination:** [Score] (Modifier: [+/-X])
- **Health:** [Score] (Modifier: [+/-X])
- **Intelligence:** [Score] (Modifier: [+/-X])
- **Wisdom:** [Score] (Modifier: [+/-X])
*Note: Social mechanics use Personality Traits (Section II) instead of Charisma*

---

## II. Personality Traits (Big Five)
*Used by BOTH systems. Critical for social mechanics in Destiny System.*

- **Openness:** [1-5] (Modifier: [Rating - 3])
  - *Creativity, imagination, intellectual curiosity*
- **Conscientiousness:** [1-5] (Modifier: [Rating - 3])
  - *Organization, dependability, self-discipline*
- **Extraversion:** [1-5] (Modifier: [Rating - 3])
  - *Sociability, assertiveness, energy*
- **Agreeableness:** [1-5] (Modifier: [Rating - 3])
  - *Cooperation, trust, empathy*
- **Neuroticism:** [1-5] (No modifier - affects behavior/thresholds)
  - *Emotional stability, stress response*

### Social Check Quick Reference (Destiny System):
- **Persuasion/Diplomacy:** Agreeableness modifier (+ Extraversion for groups)
- **Deception:** (5 - Agreeableness) modifier (+ Conscientiousness for schemes)
- **Intimidation:** (5 - Agreeableness) modifier OR Physique modifier
- **Performance:** Extraversion modifier (+ Openness for creative acts)
- **Leadership:** Conscientiousness modifier (+ low Neuroticism bonus)

---

## III. Combat Statistics
*Same mechanics for both systems*

- **Hit Points:** [Current]/[Maximum]
- **Defense:** [Base 10 + Armor + Shield + Dex/Coord Mod + Other]
- **Initiative:** [Dex/Coord Modifier + Other Bonuses]
- **Speed:** [Value] ft
- **Combat Prowess Bonus:** +[Level/Tier-based value]

### Saving Throws
#### D&D System:
- **Fortitude (CON):** [CON Mod + Proficiency if applicable]
- **Reflex (DEX):** [DEX Mod + Proficiency if applicable]
- **Will (WIS):** [WIS Mod + Proficiency if applicable]

#### Destiny System:
- **Physical (Health):** [Health Mod + Combat Prowess]
- **Reflex (Coordination):** [Coord Mod + Combat Prowess]
- **Mental (Wisdom):** [Wisdom Mod + Combat Prowess]

---

## IV. Skills & Proficiencies
- **Expertise Tags:** [List narrative expertise areas]
- **Trained Skills:** [List mechanical skill proficiencies]
- **Languages:** [Known languages]
- **Tool Proficiencies:** [Specific tools/kits]

---

## V. Abilities & Features
- **Class/Archetype Features:** [List key mechanical abilities]
- **Feats/Techniques:** [Special abilities gained]
- **Racial/Heritage Traits:** [Innate abilities]
- **Energy Points (EP):** [Current]/[Maximum] (if applicable)

---

## VI. Equipment
- **Primary Weapon:** [Name, damage, properties]
- **Secondary Weapon:** [If applicable]
- **Armor:** [Type, Defense bonus, properties]
- **Shield:** [If applicable]
- **Magical Items:** [List with properties]
- **Other Gear:** [Important adventuring equipment]
- **Wealth:** [GP, SP, CP]

---

## VII. Character Development

### Attribute/Aptitude Potentials (Growth Coefficients)
*Use names matching your Active System*

#### D&D System:
- **STR Potential:** [1-5]
- **DEX Potential:** [1-5]
- **CON Potential:** [1-5]
- **INT Potential:** [1-5]
- **WIS Potential:** [1-5]
- **CHA Potential:** [1-5]

#### Destiny System:
- **Physique Potential:** [1-5]
- **Coordination Potential:** [1-5]
- **Health Potential:** [1-5]
- **Intelligence Potential:** [1-5]
- **Wisdom Potential:** [1-5]

### Experience & Level
- **Character Level:** [Value]
- **Experience Points:** [Current]/[Needed for next level]
- **Tier of Play:** [1-4]

---

## VIII. Notes
- **Background Summary:** [Brief character history]
- **Core Ambitions:** [Major character goals]
- **Bonds & Flaws:** [Key relationships and weaknesses]
- **Campaign-Specific:** [Any unique campaign mechanics]
