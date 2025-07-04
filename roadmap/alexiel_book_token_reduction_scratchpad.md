# Alexiel Book Token Reduction Scratchpad

## Goal
Reduce `mvp_site/world/celestial_wars_alexiel_book.md` from ~162k tokens to ~10k tokens while preserving core narrative elements needed for AI worldbuilding.

## Current Structure Analysis
- **Total Size**: 6,419 lines, ~647KB, ~162k tokens
- **Content Type**: Full novel manuscript with detailed scenes, dialogue, and internal monologues
- **Core Elements**: Character profiles, world lore, power systems, faction dynamics

## Token Reduction Strategies

### 1. **Convert Novel Prose to Reference Material** (80% reduction)
- Condense scene-by-scene narrative to plot summaries
- Summarize dialogue exchanges to key outcomes
- Extract key character insights from internal monologues
- Keep ALL story events and plot points in condensed form
- **IMPORTANT**: No scenes or events are removed, only compressed

### 2. **Consolidate Character Information** (60% reduction)
- Condense character development arcs to bullet-point profiles
- Include: Name, role, key abilities, faction allegiance, essential relationships, core motivations
- Summarize psychological development and growth milestones
- Keep ALL characters mentioned in the story
- Example: Alexiel's 500+ line character development → 20-30 line comprehensive profile
- **IMPORTANT**: Every character remains, with compressed but complete information

### 3. **Simplify Timeline to Key Events** (70% reduction)
- Convert detailed chapter summaries to concise timeline entries
- Include both world-changing events AND key character moments
- Keep ALL events but compress descriptions
- Example: "Year 78: Alexiel defects from Host after Silverwood massacre - witnesses child deaths, confronts Gorok, drops Host sigil"
- **IMPORTANT**: Every timeline event remains, just condensed

### 4. **Extract Core World Mechanics** (Create separate focused sections)
- **Power System**: How magic works, key limitations
- **Faction Summary**: 2-3 sentences per faction with goals and methods
- **Geography**: Key locations with 1-line descriptions
- **Political Structure**: Basic hierarchy and conflicts

### 5. **Create Reference Tables Instead of Prose**
- Character roster table (name, faction, role, status)
- Location gazetteer (name, faction control, significance)
- Timeline table (year, event, impact)
- Power/ability reference (name, user, effect)

### 6. **Consolidate Redundancy**
- Combine multiple descriptions of same concepts into single comprehensive entry
- Merge repeated exposition into unified explanations
- Integrate flashback information into main timeline with clear markers
- **IMPORTANT**: No information is lost, only consolidated

### 7. **Priority Preservation List** (Must Keep Everything)
1. ALL character identities and development arcs (compressed)
2. ALL plot events from every arc (summarized)
3. ALL faction structures and philosophies (condensed)
4. ALL magic system details (organized)
5. ALL timeline events (compressed format)
6. ALL locations mentioned (with brief descriptions)
7. **Core principle**: COMPRESS, don't CUT

## Proposed New Structure (Target: 10k tokens)

### Section 1: World Overview (1k tokens)
- Setting premise (2 paragraphs)
- Power system summary (bullet points)
- Current world state

### Section 2: Faction Reference (2k tokens)
- **Unchained Host**: Goals, methods, leadership, military strength
- **Radiant Imperium**: Structure, values, key divisions
- **Other Factions**: Brief mentions of minor players

### Section 3: Character Roster (3k tokens)
- **ALL characters from the book included**
- **Major Characters** (Alexiel, Lucifer, Emperor, Artorius): 15-20 lines each
- **Supporting Characters** (lieutenants, companions): 5-10 lines each
- **Minor Characters**: 2-3 line descriptions
- **No character is omitted**

### Section 4: Location Gazetteer (1k tokens)
- Major cities/regions with strategic importance
- Current control status
- Single notable feature per location

### Section 5: Timeline of ALL Events (1.5k tokens)
- ALL pre-story events (compressed)
- ALL battles and political shifts (summarized)
- ALL character development milestones
- ALL plot points from every arc
- Organized chronologically with brief descriptions

### Section 6: Rules & Restrictions (1.5k tokens)
- Magic system rules
- Political/social constraints
- Technology/advancement limits

## Implementation Plan

1. **Create extraction script** to pull key data from novel format
2. **Build reference tables** using markdown table format
3. **Write concise summaries** for each section
4. **Validate** that AI can still generate appropriate content with reduced context
5. **Iterate** based on testing to ensure critical information retained

## File Locations
- **Source files**: `mvp_site/world/`
  - `celestial_wars_alexiel_book.md` (162k tokens)
  - `world_assiah.md` (85k tokens)
- **Output files**: Will be created as versioned files in same directory
  - `celestial_wars_alexiel_book_compressed.md` (target: 10k tokens)
  - `world_assiah_compressed.md` (target: 42.5k tokens)

## Metrics for Success
- Token count: ≤10k tokens
- AI can still answer questions about ANY character or event
- AI can generate stories consistent with ALL world rules
- AI maintains complete faction dynamics
- NO loss of any plot/world information
- Every character, event, and location remains accessible

## Compression Philosophy
- **From Novel to Encyclopedia**: Transform narrative prose into reference material
- **Complete but Concise**: Every element preserved in compressed form
- **No Deletions**: If it exists in the original, it exists in the reduced version
- **Think Wikipedia**: Comprehensive coverage with efficient language

## Next Steps
1. Create proof-of-concept reduced version
2. Test with AI for consistency
3. Identify any critical gaps
4. Refine reduction approach
5. Implement final version

---

# World Assiah Token Reduction Plan

## Goal
Reduce `mvp_site/world/world_assiah.md` from ~85k tokens to ~42.5k tokens (50% reduction) while preserving essential world information for AI campaigns.

## Current Structure Analysis
- **Total Size**: 5,248 lines, ~341KB, ~85k tokens
- **Content Type**: Campaign guide with detailed faction descriptions, character profiles, geography, and game mechanics
- **Structure**: 202 sections organized hierarchically
- **Key Sections**:
  - Faction descriptions (8 major + sub-factions each)
  - Character profiles (extensive individual entries)
  - Geography & locations
  - Game mechanics & systems
  - Names library (including banned names)

## Token Reduction Strategies for 50% Cut

### 1. **Consolidate Sub-faction Descriptions** (30% reduction)
- Current: Each sub-faction has 3-5 paragraph descriptions
- Proposed: Reduce to 2-3 bullet points per sub-faction
- Keep: ALL sub-factions, core ideology, leadership, primary goal
- Remove: Extended philosophy, internal politics details
- Example: Principate Senate (5 paragraphs) → 3 bullet points
- **IMPORTANT**: Every sub-faction remains in the document

### 2. **Streamline Character Profiles** (40% reduction)
- Current: Individual character entries with backstory and personality
- Proposed: Condensed format with essential information
- Keep: ALL characters, name, faction, role, key ability/trait, critical relationships
- Remove: Extended backstories, verbose personality descriptions, tangential details
- Format: 2-3 lines per character instead of full paragraphs
- **IMPORTANT**: Every character remains, just with condensed descriptions

### 3. **Compress Names Library** (80% reduction)
- Current: Extensive lists of example names by culture/race
- Proposed: 5-10 examples per category maximum
- Keep: Banned names list (critical for continuity)
- Remove: Redundant name examples
- This section alone could save 5-10k tokens

### 4. **Simplify Game Mechanics** (20% reduction)
- Current: Detailed explanations of each system
- Proposed: Bullet-point rules with examples removed
- Keep: Core mechanics (half-celestial powers, military ranks)
- Remove: Extended explanations, edge cases

### 5. **Geography Optimization** (50% reduction)
- Current: Paragraph descriptions for each location
- Proposed: Location name + single defining feature
- Keep: Strategic importance and current control
- Remove: Historical details, architectural descriptions

### 6. **Merge Redundant Content**
- Combine overlapping faction philosophies
- Merge similar character archetypes
- Consolidate repeated world rules

## Specific Reduction Targets

### Section-by-Section Cuts:
1. **Factions** (Currently ~25k tokens → 12.5k tokens)
   - Main faction: 1 paragraph max
   - Sub-factions: 3 bullet points each
   - Remove internal politics details

2. **Character Profiles** (Currently ~20k tokens → 8k tokens)
   - Keep ALL characters
   - Condense to 2-3 lines per character
   - Maintain faction groupings
   - Include: Name, role, key trait, essential relationships

3. **Names Library** (Currently ~15k tokens → 3k tokens)
   - 10 names per culture max
   - Keep only banned names in full

4. **Geography** (Currently ~10k tokens → 5k tokens)
   - Location + 1 line description
   - Strategic value only

5. **Game Mechanics** (Currently ~8k tokens → 6k tokens)
   - Bullet points only
   - Remove examples

6. **History/Timeline** (Currently ~7k tokens → 5k tokens)
   - Major events only
   - Single line per event

## Expected Results
- **Current**: ~85k tokens
- **After 50% reduction**: ~42.5k tokens
- **Preserved**: All critical world information for gameplay
- **Lost**: Flavor text, extended descriptions, redundant examples

## Implementation Approach
1. Create structured extraction templates
2. Build conversion scripts for tables
3. Test with sample campaigns to ensure functionality
4. Iterate based on what information DMs actually reference
5. Consider creating "extended lore" supplement for deep dives

## Key Preservation Criteria
- Any information that affects game mechanics
- ALL character names and faction allegiances (no removals)
- ALL sub-factions (condensed but present)
- Geographic boundaries and control
- Core conflict drivers
- Unique world rules (Nulls, wings, etc.)
- Banned names list (full preservation)

## Clarification on Approach
- **NO REMOVAL** of characters, factions, or sub-factions
- **TRIMMING ONLY** - reduce verbosity while keeping all entities
- Think of it as "compression" not "deletion"
- Every named entity that exists in the current document will exist in the reduced version