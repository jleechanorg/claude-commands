# Sariel Campaign Desync Analysis

## Campaign Overview
- **Campaign Name**: Sariel v2: The Awakening
- **Type**: Real Firebase Campaign
- **Log Length**: ~1500 lines of narrative
- **Key Challenge**: Complex multi-character interactions and emotional states

## Entity Tracking Observations

### 1. Good Entity Tracking Examples

#### Turn 599-603: Emotional Scene with Cressida
```
Location: Lady Cressida Valeriana's Chambers
Entities Present: Sariel, Cressida
Status: GOOD - Both characters consistently referenced
```
The narrative properly tracks both characters throughout the emotional scene, with clear references to "you" (Sariel) and "Cressida" maintaining their presence.

#### Turn 1089-1095: Kantos Revelation Scene
```
Location: Chamber of Whispers, Great Archives
Entities Present: Sariel, Magister Kantos
Status: GOOD - Both characters tracked through dialogue
```
Despite the heavy exposition, both Sariel and Kantos remain consistently present in the narrative.

### 2. Potential Desync Patterns

#### Pattern 1: Multi-Character References
When discussing multiple NPCs (Cassian, Valerius, Titus), the narrative sometimes loses track of who is physically present vs. who is being discussed:
- Line 151-159: Cassian enters, but narrative shifts to discussing other family members without clear transitions
- This could lead to confusion about who is actually in the scene

#### Pattern 2: State Transition Tracking
- Multiple scene transitions (chambers → study → archives) maintain character positions well
- However, emotional states and physical descriptions (trembling hands, bandaged ear) sometimes disappear between scenes

#### Pattern 3: Complex Game State Integration
The narrative includes detailed game state blocks with extensive NPC data, but not all NPCs listed are consistently referenced when they should be contextually relevant.

## Key Desync Risk Areas

### 1. **Split Focus Scenes**
When Sariel thinks about absent characters (her brothers, her mother), the narrative sometimes loses focus on present characters.

### 2. **Exposition-Heavy Sections**
During lore reveals (lines 1000-1150), the focus on abstract concepts can overshadow entity tracking.

### 3. **Emotional State Continuity**
Physical manifestations of emotion (tears, trembling) appear and disappear without clear resolution.

## Comparison to Mock Campaigns

Unlike the mock campaigns which showed clear entity omissions, the Sariel campaign demonstrates more subtle tracking issues:
- **Mock Campaigns**: Complete omission of characters (e.g., Kira missing from party narrative)
- **Sariel Campaign**: All characters mentioned but sometimes with unclear presence/absence status

## Recommendations for Testing

1. **Test Scenarios**:
   - Scenes with 3+ characters where some leave/enter
   - Emotional scenes transitioning to exposition
   - Combat scenarios with multiple participants

2. **Validation Focus**:
   - Physical presence vs. mental reference
   - Emotional state continuity
   - Location-based entity tracking

3. **Success Metrics**:
   - 100% of physically present characters mentioned per scene
   - Clear transitions when characters enter/leave
   - Consistent emotional state tracking across scene breaks
