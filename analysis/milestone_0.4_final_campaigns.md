# Milestone 0.4 Final Campaign Selection

Generated: 2025-06-30

## Overview
- **Mock Campaigns**: 5 (with synthetic desync patterns)
- **Real Campaigns**: 1 (Sariel v2 from production Firebase)
- **Total Test Campaigns**: 6

## Campaign Details

### 1. Sariel v2: The Awakening (REAL)
- **Campaign ID**: sariel_v2_real
- **Type**: Real Firebase Campaign
- **Source**: Production Database
- **Desync Rate**: ~15% (estimated from log analysis)
- **Priority**: **REQUIRED** (User specified)

**Key Patterns Observed:**
- Complex multi-NPC scenes (6+ named NPCs)
- Emotional state tracking across characters
- Location transitions within the Zenith Spire
- State updates with detailed character sheets

**Test Scenarios:**
1. Multi-NPC conversation scenes (Cassian, Valerius, Cressida present)
2. Emotional state transitions (grief, anger, comfort)
3. Location-based entity visibility

**Example Entities to Track:**
- Player: Sariel Arcanus
- NPCs: Cassian Arcanus, Valerius Arcanus, Lady Cressida Valeriana, High Commander Titus val Raziel, Ser Gideon Vance, Rowan Thorne
- Locations: Sariel's Chambers, Valerius's Study, Cressida's Chambers

---

### 2. The Thornwood Conspiracy (MOCK)
- **Campaign ID**: thornwood_conspiracy_42
- **Type**: Mock
- **Desync Rate**: 22%
- **Priority**: High

**Key Issues:**
- Split party scenarios
- Stealth/visibility mechanics
- Location confusion

**Test Scenarios:**
1. Party split across sewers/tavern
2. Hidden characters in same location
3. Regrouping after split

---

### 3. Shadows of Darkmoor (MOCK)
- **Campaign ID**: darkmoor_shadows_99
- **Type**: Mock
- **Desync Rate**: 18%
- **Priority**: High

**Key Issues:**
- Invisible character handling
- Hidden status tracking
- Perception mechanics

**Test Scenarios:**
1. Invisible wizard + hidden rogue
2. Partial party visibility
3. Stealth breaking scenarios

---

### 4. The Brass Compass Guild (MOCK)
- **Campaign ID**: brass_compass_17
- **Type**: Mock
- **Desync Rate**: 12%
- **Priority**: Medium

**Key Issues:**
- Large NPC groups (20+ crew)
- Naval combat tracking
- Background NPC management

**Test Scenarios:**
1. Ship battle with full crew
2. Port scenes with crowds
3. Allied NPC coordination

---

### 5. Echoes of the Astral War (MOCK)
- **Campaign ID**: astral_war_55
- **Type**: Mock
- **Desync Rate**: 25%
- **Priority**: High

**Key Issues:**
- Planar travel effects
- Polymorph tracking
- Reality distortion

**Test Scenarios:**
1. Character polymorphed into dragon
2. Party split across planes
3. Reality shift effects

---

### 6. The Siege of Frostholm (MOCK)
- **Campaign ID**: frostholm_siege_88
- **Type**: Mock
- **Desync Rate**: 20%
- **Priority**: Medium

**Key Issues:**
- Mass combat (100+ participants)
- Siege equipment tracking
- Army coordination

**Test Scenarios:**
1. Large-scale battle scenes
2. Siege weapon operations
3. Command hierarchy tracking

## Testing Approach

### Phase 1: Validation-Only Approach
- Implement entity validation after narrative generation
- Flag missing entities without modifying output
- Measure detection accuracy

### Phase 2: Pydantic-Only Approach
- Structure narrative generation with Pydantic schemas
- Force entity inclusion through structured data
- Measure generation quality

### Phase 3: Combined Approach
- Use both validation and structured generation
- Compare effectiveness vs individual approaches
- Optimize for best results

## Success Metrics
- **Primary**: 50% reduction in desync rate
- **Secondary**: 95% entity mention rate in narratives
- **Constraint**: <100ms additional latency

## Next Steps
1. Extract full narrative samples from each campaign
2. Create test harness for all three approaches
3. Run benchmarks and measure improvements
4. Document results and recommendations
