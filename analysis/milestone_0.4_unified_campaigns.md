# Milestone 0.4: Unified Campaign Selection

Generated: 2025-06-30

## Overview
This document combines mock campaigns with the real Sariel v2 campaign for comprehensive testing of three approaches to prevent narrative desynchronization.

## Campaign Selection Summary
- **Total Campaigns**: 6 (5 mock + 1 real)
- **Desync Rate Range**: 12% - 25%
- **Testing Priority**: Sariel v2 (required), then by desync rate

## Selected Campaigns

### 1. Sariel v2: The Awakening (REAL)
- **Campaign ID**: sariel_v2_firebase
- **Source**: Firebase Production Database
- **Desync Rate**: ~15% (subtle tracking issues)
- **Priority**: REQUIRED - User specified
- **Key Issues**:
  - Multi-character scene management
  - Emotional state continuity
  - Physical presence vs. mental reference
- **Unique Characteristics**:
  - Complex narrative with heavy exposition
  - Multiple NPCs with detailed backstories
  - Sophisticated emotional scenes
- **Test Scenarios**:
  - Cassian confrontation (multiple emotional states)
  - Chamber of Whispers (Kantos + exposition)
  - Cressida comfort scene (intimate 2-person dialogue)

### 2. The Thornwood Conspiracy (MOCK)
- **Campaign ID**: thornwood_conspiracy_42
- **Desync Rate**: 22% (highest)
- **Priority**: High
- **Key Issues**:
  - Split party scenarios
  - Stealth/visibility mechanics
  - Location confusion
- **Test Scenarios**:
  - Kira in sewers while party in tavern
  - Hidden characters in same location
  - Party regrouping after split

### 3. Echoes of the Astral War (MOCK)
- **Campaign ID**: astral_war_55
- **Desync Rate**: 25% (severe)
- **Priority**: High
- **Key Issues**:
  - Planar travel confusion
  - Polymorph state tracking
  - Reality distortion effects
- **Test Scenarios**:
  - Character transformed into dragon
  - Party split across planes
  - Shifting reality descriptions

### 4. Shadows of Darkmoor (MOCK)
- **Campaign ID**: darkmoor_shadows_99
- **Desync Rate**: 18%
- **Priority**: High
- **Key Issues**:
  - Invisible character omission
  - Hidden vs. visible status
  - Perception mechanics
- **Test Scenarios**:
  - Multiple invisible party members
  - Stealth in combat
  - Partial visibility scenarios

### 5. The Brass Compass Guild (MOCK)
- **Campaign ID**: brass_compass_17
- **Desync Rate**: 12%
- **Priority**: Medium
- **Key Issues**:
  - Large group management
  - Naval combat tracking
  - Crew member omission
- **Test Scenarios**:
  - 20+ NPCs in battle
  - Ship crew during storm
  - Port scenes with crowds

### 6. The Siege of Frostholm (MOCK)
- **Campaign ID**: frostholm_siege_88
- **Desync Rate**: 20%
- **Priority**: Medium
- **Key Issues**:
  - Mass combat confusion
  - Siege equipment tracking
  - Army unit management
- **Test Scenarios**:
  - 100+ combatants
  - Siege tower assault
  - Command tent strategy

## Testing Approach

### Phase 1: Validation-Only (Week 1)
- Implement post-generation validation
- Test on all 6 campaigns
- Measure desync reduction

### Phase 2: Pydantic-Only (Week 2)
- Implement structured generation
- Test on all 6 campaigns
- Compare to validation results

### Phase 3: Combined Approach (Week 3)
- Implement both methods
- Test on all 6 campaigns
- Analyze synergistic effects

## Success Metrics

### Primary Metrics
1. **Desync Rate Reduction**: Target 50% reduction
2. **Entity Mention Rate**: Target 95% of present entities
3. **Performance Impact**: <100ms additional latency

### Secondary Metrics
1. **False Positive Rate**: <5% incorrect entity mentions
2. **Narrative Quality**: No degradation in storytelling
3. **Edge Case Handling**: 90% success on complex scenarios

## Key Differences: Real vs Mock

### Sariel v2 (Real)
- **Subtle Issues**: Characters mentioned but presence unclear
- **Complex State**: Extensive game state integration
- **Emotional Depth**: Sophisticated character interactions

### Mock Campaigns
- **Obvious Omissions**: Complete character disappearance
- **Simple Patterns**: Clear cause-and-effect
- **Mechanical Focus**: Combat and location-based issues

## Next Steps

1. Extract specific test scenarios from each campaign
2. Implement validation-only approach (Step 2)
3. Create test harness for automated evaluation
4. Begin systematic testing across all campaigns
