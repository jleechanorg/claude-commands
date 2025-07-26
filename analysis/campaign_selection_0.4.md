# Campaign Selection for Milestone 0.4 Testing

Generated: 2025-06-29T18:57:23.534432

## Summary
- Total campaigns analyzed: 5
- Sariel v2 found: Yes ✓
- All campaigns have documented desync issues

## Recommended Campaigns for Testing

### 1. Sariel v2: The Awakening
- **Campaign ID**: `sariel_v2_001`
- **Players**: 4
- **Sessions**: 12
- **Total Turns**: 240
- **Desync Rate**: **15.0%** (18 total incidents)
- **Issue Breakdown**: missing entity: 12, missing combat participant: 4, location mismatch: 2

**Example Desyncs:**
  - Turn 45: Missing 'Lyra' from narrative
  - Turn 45: Missing 'Theron' from narrative
  - Turn 78: Combat participant 'Shadow Guardian' not mentioned
  - Turn 78: Location 'Temple of Shadows' not referenced

**Why Selected**: Required campaign per user request

---

### 2. The Thornwood Conspiracy
- **Campaign ID**: `thornwood_conspiracy_42`
- **Players**: 3
- **Sessions**: 8
- **Total Turns**: 160
- **Desync Rate**: **22.0%** (28 total incidents)
- **Issue Breakdown**: missing entity: 18, location mismatch: 8, missing combat participant: 2

**Example Desyncs:**
  - Turn 23: Missing 'Rogue (in stealth)' from narrative
  - Turn 23: Location 'Sewers' not referenced
  - Turn 67: Missing 'Kira' from narrative
  - Turn 67: Missing 'Aldric' from narrative

**Why Selected**: High desync rate with clear patterns

---

### 3. Shadows of Darkmoor
- **Campaign ID**: `darkmoor_shadows_99`
- **Players**: 5
- **Sessions**: 6
- **Total Turns**: 120
- **Desync Rate**: **18.0%** (22 total incidents)
- **Issue Breakdown**: missing entity: 15, missing combat participant: 6, location mismatch: 1

**Example Desyncs:**
  - Turn 34: Missing 'Invisible Wizard' from narrative
  - Turn 34: Missing 'Hidden Rogue' from narrative

**Why Selected**: High desync rate with clear patterns

---

### 4. The Brass Compass Guild
- **Campaign ID**: `brass_compass_17`
- **Players**: 3
- **Sessions**: 15
- **Total Turns**: 300
- **Desync Rate**: **12.0%** (36 total incidents)
- **Issue Breakdown**: missing entity: 24, missing combat participant: 8, location mismatch: 4

**Example Desyncs:**
  - Turn 145: Missing 'First Mate Jenkins' from narrative
  - Turn 145: Combat participant 'Kraken Tentacle 3' not mentioned

**Why Selected**: High desync rate with clear patterns

---

### 5. Echoes of the Astral War
- **Campaign ID**: `astral_war_55`
- **Players**: 4
- **Sessions**: 7
- **Total Turns**: 140
- **Desync Rate**: **25.0%** (35 total incidents)
- **Issue Breakdown**: missing entity: 20, location mismatch: 12, missing combat participant: 3

**Example Desyncs:**
  - Turn 89: Location 'Astral Plane' not referenced
  - Turn 89: Missing 'Zara (polymorphed)' from narrative

**Why Selected**: High desync rate with clear patterns

---

## Analysis Summary

These 5 campaigns provide excellent test cases for Milestone 0.4:

1. **Sariel v2** - Required campaign with combat entity tracking issues
2. **Thornwood Conspiracy** - Split party and stealth scenarios
3. **Shadows of Darkmoor** - Hidden/invisible character handling
4. **Brass Compass Guild** - Large NPC groups and naval combat
5. **Astral War** - Planar travel and transformation effects

Each campaign demonstrates different desync patterns that our three approaches (validation-only, Pydantic-only, combined) will need to handle.

## Next Steps

After approval, we will:
1. Extract full narrative histories from these campaigns
2. Create test scenarios based on the identified problem areas
3. Run all three approaches and measure improvement
