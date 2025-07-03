# Attribute System Conversion Guide

This guide provides conversion rules between D&D 6-attribute and Destiny 5-aptitude systems.

## Quick Reference Table

| D&D Attribute | Destiny Aptitude | Conversion Notes |
|---------------|------------------|------------------|
| Strength (STR) | Physique | Direct 1:1 mapping |
| Dexterity (DEX) | Coordination | Direct 1:1 mapping |
| Constitution (CON) | Health | Direct 1:1 mapping |
| Intelligence (INT) | Intelligence | Direct 1:1 mapping |
| Wisdom (WIS) | Wisdom | Direct 1:1 mapping |
| Charisma (CHA) | Personality Traits | See conversion formulas below |

## Detailed Conversion Rules

### Physical & Mental Attributes (1:1 Mappings)
These convert directly with no modification needed:
- **STR ↔ Physique**: Raw physical power
- **DEX ↔ Coordination**: Agility and precision
- **CON ↔ Health**: Endurance and vitality
- **INT ↔ Intelligence**: Reasoning and knowledge
- **WIS ↔ Wisdom**: Awareness and willpower

### Charisma ↔ Personality Traits Conversion

#### D&D to Destiny (CHA → Traits)
When converting a D&D character to Destiny system:

```
If CHA 18-20: Extraversion 5, Agreeableness 5
If CHA 16-17: Extraversion 4, Agreeableness 4
If CHA 14-15: Extraversion 4, Agreeableness 3
If CHA 12-13: Extraversion 3, Agreeableness 3
If CHA 10-11: Extraversion 3, Agreeableness 3
If CHA 8-9:   Extraversion 2, Agreeableness 2
If CHA 6-7:   Extraversion 2, Agreeableness 1
If CHA 3-5:   Extraversion 1, Agreeableness 1
```

Other traits set based on character concept:
- **Openness**: Based on background (Scholar=4-5, Soldier=2-3)
- **Conscientiousness**: Based on class (Paladin=4-5, Rogue=2-3)
- **Neuroticism**: Inversely related to WIS (High WIS = Low Neuroticism)

#### Destiny to D&D (Traits → CHA)
When converting a Destiny character to D&D system:

```
Effective CHA = 10 + Social Modifier

Where Social Modifier = Average of:
- (Extraversion - 3)
- (Agreeableness - 3)
```

Examples:
- Extraversion 5, Agreeableness 4 = CHA 16
- Extraversion 3, Agreeableness 3 = CHA 10
- Extraversion 1, Agreeableness 2 = CHA 6

## Mechanical Conversions

### Attack Rolls
| D&D Version | Destiny Version |
|-------------|-----------------|
| STR + Prof + d20 | Physique + Combat Prowess + d20 |
| DEX + Prof + d20 | Coordination + Combat Prowess + d20 |

### Damage Calculations
| D&D Version | Destiny Version |
|-------------|-----------------|
| Weapon + STR mod | Weapon + Physique mod + (Coord mod / 2) |
| Weapon + DEX mod | Weapon + Coordination mod + (Phys mod / 2) |

### Social Checks
| Check Type | D&D Version | Destiny Version |
|------------|-------------|-----------------|
| Persuasion | CHA + Prof | Agreeableness mod + Skill |
| Deception | CHA + Prof | (5 - Agreeableness) mod + Skill |
| Intimidation | CHA + Prof | (5 - Agreeableness) OR Physique + Skill |
| Performance | CHA + Prof | Extraversion mod + Skill |

### Saving Throws
| D&D Save | Destiny Save | Calculation |
|----------|--------------|-------------|
| STR Save | Physical Save | Physique + Combat Prowess |
| DEX Save | Reflex Save | Coordination + Combat Prowess |
| CON Save | Physical Save | Health + Combat Prowess |
| INT Save | Mental Save | Intelligence + Combat Prowess |
| WIS Save | Mental Save | Wisdom + Combat Prowess |
| CHA Save | Social Save | Highest applicable trait mod + Combat Prowess |

## Spell Conversions

### Spellcasting Ability
| D&D Caster | Primary Attribute | Destiny Equivalent |
|------------|-------------------|-------------------|
| Wizard | INT | Intelligence |
| Cleric | WIS | Wisdom |
| Sorcerer | CHA | Intelligence + High Openness |
| Warlock | CHA | Wisdom + Pact narrative |
| Bard | CHA | High Extraversion + Openness |

### Spell Save DC
- **D&D**: 8 + Prof + Ability Mod
- **Destiny**: 10 + Combat Prowess + Ability Mod

## Campaign Conversion Guidelines

### When to Convert
- Importing character from different system
- Player strongly prefers one system
- Special one-shot with mixed systems

### When NOT to Convert
- Mid-campaign (causes confusion)
- For NPCs in established campaign
- When it would disrupt game flow

## Quick Conversion Checklist

1. ☐ Identify source system
2. ☐ Map physical/mental attributes 1:1
3. ☐ Convert CHA ↔ Personality Traits
4. ☐ Adjust spell DCs if applicable
5. ☐ Update character sheet format
6. ☐ Verify all modifiers recalculated
7. ☐ Test with a few skill checks

## Examples

### D&D Fighter → Destiny Warrior
```
STR 16 → Physique 16
DEX 14 → Coordination 14
CON 15 → Health 15
INT 10 → Intelligence 10
WIS 12 → Wisdom 12
CHA 8  → Extraversion 2, Agreeableness 2
```

### Destiny Diplomat → D&D Bard
```
Physique 10 → STR 10
Coordination 14 → DEX 14
Health 12 → CON 12
Intelligence 16 → INT 16
Wisdom 13 → WIS 13
Extraversion 5, Agreeableness 4 → CHA 16
```