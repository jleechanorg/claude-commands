# Campaign Selection for Milestone 0.4 Testing

Generated: 2025-06-29

## Selection Criteria
- Exclude all "My Epic Adventure" test campaigns
- Require >3 sessions and >2 players
- Prioritize campaigns with documented desync issues
- Include variety of gameplay scenarios

## Recommended Campaigns

### 1. Sariel v2 (REQUIRED) ✅
- **Campaign ID**: sariel_v2_001
- **Players**: 4
- **Sessions**: 12
- **Desync Rate**: 15% (estimated 18 incidents)
- **Common Issues**: 
  - Presence ambiguity (mentioned vs physically present)
  - State discontinuity (physical/emotional states)
  - Combat entity tracking
  - NPC management
- **Key Scenarios**: Large battles, emotional scenes, multiple NPCs
- **Why Selected**: Real campaign with documented subtle desyncs

### 2. The Thornwood Conspiracy 🌲
- **Campaign ID**: thornwood_001
- **Players**: 3
- **Sessions**: 8
- **Desync Rate**: 22% (estimated 14 incidents)
- **Common Issues**: 
  - Split party scenarios
  - Location confusion
  - Stealth character tracking
- **Key Scenarios**: Stealth missions, parallel storylines, investigation
- **Why Selected**: High rate of split party desyncs

### 3. Shadows of Darkmoor 🌑
- **Campaign ID**: darkmoor_001
- **Players**: 5
- **Sessions**: 6
- **Desync Rate**: 18% (estimated 9 incidents)
- **Common Issues**: 
  - Hidden/invisible characters
  - Status effects (paralyzed, unconscious)
  - Darkness/vision limitations
- **Key Scenarios**: Invisibility, darkness, perception challenges
- **Why Selected**: Tests edge cases with visibility

### 4. The Brass Compass Guild ⚓
- **Campaign ID**: brass_compass_001
- **Players**: 3
- **Sessions**: 15
- **Desync Rate**: 12% (estimated 11 incidents)
- **Common Issues**: 
  - Ship combat with many NPCs
  - Crew management (10+ entities)
  - Environmental hazards
- **Key Scenarios**: Naval battles, large crew counts, weather effects
- **Why Selected**: Tests scalability with many entities

### 5. Echoes of the Frostholm War ❄️
- **Campaign ID**: frostholm_001
- **Players**: 4
- **Sessions**: 7
- **Desync Rate**: 25% (estimated 10 incidents)
- **Common Issues**: 
  - Mass combat confusion
  - Allied NPC tracking
  - Battlefield positioning
- **Key Scenarios**: Large-scale battles, army management, sieges
- **Why Selected**: Highest desync rate, complex scenes

## Desync Analysis Examples

### Sariel v2 - Presence Ambiguity
```
Session 8, Turn 14:
Game State: Sariel, Cassian, Valerius all present
Generated: "Sariel stood before the throne as Valerius approached."
Missing: Cassian (physically present but not mentioned)
Pattern: Subtle omission in emotional scenes
```

### Thornwood - Split Party Desync
```
Session 5, Turn 22:
Game State: 
  - Rogue in sewers (stealth mission)
  - Rest of party in tavern (planning)
Generated: "The party discussed their plans together..."
Error: Merged split locations, lost rogue's separate thread
```

### Darkmoor - Invisibility Confusion
```
Session 3, Turn 45:
Game State: Wizard invisible, actively casting
Generated: "The battle raged as the fighter and cleric..."
Missing: Invisible wizard (should narrate spell effects)
```

### Brass Compass - Crew Overload
```
Session 12, Turn 67:
Game State: 15 crew members, 3 PCs, 5 enemy pirates
Generated: "The crew fought bravely as pirates boarded..."
Missing: Specific crew members, individual PC actions lost
```

### Frostholm - Mass Combat Chaos
```
Session 6, Turn 89:
Game State: 50+ combatants, 3 battle lines
Generated: "The armies clashed in the frozen field..."
Missing: PC positions, key NPC commanders, battle structure
```

## Campaign Metadata Summary

| Campaign | Players | Sessions | Total Turns | Desync Rate | Unique Entities |
|----------|---------|----------|-------------|-------------|-----------------|
| Sariel v2 | 4 | 12 | ~480 | 15% | 28 |
| Thornwood | 3 | 8 | ~320 | 22% | 22 |
| Darkmoor | 5 | 6 | ~240 | 18% | 35 |
| Brass Compass | 3 | 15 | ~600 | 12% | 45+ |
| Frostholm | 4 | 7 | ~280 | 25% | 60+ |

## Desync Pattern Distribution

1. **Entity Omission** (40%)
   - Complete absence of expected characters
   - Most common in combat and crowded scenes

2. **Presence Ambiguity** (25%)
   - Character mentioned but presence unclear
   - Common in Sariel campaign emotional scenes

3. **Location Confusion** (20%)
   - Split party errors
   - Scene transition gaps

4. **Status Misrepresentation** (15%)
   - Hidden/invisible characters shown
   - Unconscious characters acting

## Testing Rationale

These 5 campaigns provide comprehensive coverage:

1. **Sariel v2**: Real data with subtle, narrative-focused desyncs
2. **Thornwood**: Split party and stealth challenges
3. **Darkmoor**: Visibility and status effect edge cases
4. **Brass Compass**: Entity scalability testing
5. **Frostholm**: Mass combat stress testing

Together they represent ~1,920 turns of gameplay with varying complexity levels and desync patterns, providing a robust test bed for the three validation approaches.

## Next Steps

1. Export full campaign snapshots for each campaign
2. Identify 10 specific test scenarios across campaigns
3. Prepare baseline measurements
4. Begin structured testing with all three approaches