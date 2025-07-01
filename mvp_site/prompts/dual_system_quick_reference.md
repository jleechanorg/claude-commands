# Dual Attribute System Quick Reference

## For Players

### Choosing Your System

**Choose D&D System if you:**
- Are familiar with D&D 5e
- Want traditional fantasy mechanics
- Prefer simple social interactions (one CHA score)
- Are adapting D&D content

**Choose Destiny System if you:**
- Want nuanced personality-based social mechanics
- Prefer streamlined 5-attribute system
- Like the Big Five personality model
- Want more realistic social interactions

### System Comparison

| Aspect | D&D System | Destiny System |
|--------|------------|----------------|
| Physical Power | STR | Physique |
| Agility | DEX | Coordination |
| Endurance | CON | Health |
| Reasoning | INT | Intelligence |
| Awareness | WIS | Wisdom |
| Social | CHA | Personality Traits |
| Total Attributes | 6 | 5 + Personality |

## For AI/GM

### Quick Detection
```
Check: custom_campaign_state.attribute_system
If "dnd": Use D&D 6 attributes
If "destiny": Use Destiny 5 aptitudes + traits
If missing: Default to "dnd"
```

### Combat Resolution
Both systems use identical mechanics:
- Attack: d20 + attribute mod + combat prowess
- Damage: weapon + attribute mod
- Defense: 10 + armor + DEX/Coord mod

### Social Check Resolution

**D&D System:**
- All social checks: d20 + CHA mod + proficiency

**Destiny System:**
- Persuasion: d20 + Agreeableness mod + skill
- Deception: d20 + (5-Agreeableness) mod + skill
- Intimidation: d20 + (5-Agreeableness) OR Physique mod + skill
- Performance: d20 + Extraversion mod + skill
- Leadership: d20 + Conscientiousness mod + skill

### Key Differences Summary

1. **Attributes**: D&D has 6, Destiny has 5
2. **Social Mechanics**: D&D uses CHA, Destiny uses personality traits
3. **Character Depth**: Destiny provides more nuanced personalities
4. **Simplicity**: D&D is simpler to learn and use
5. **Compatibility**: D&D works better with published content

## Common Pitfalls to Avoid

1. **Don't Mix Systems**: Each campaign uses ONE system
2. **Don't Convert Mid-Campaign**: Causes confusion
3. **Don't Forget Personality**: Both systems use Big Five traits
4. **Don't Assume**: Always check which system is active
5. **Don't Complicate**: Mechanics stay the same, only names change