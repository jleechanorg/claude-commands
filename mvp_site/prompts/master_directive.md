# Master Directive: WorldArchitect.AI Prompt Hierarchy
**Version: 1.0**
**Last Updated: 2025-01-07**

## Critical Loading Order and Precedence

This document establishes the authoritative hierarchy for all AI instructions in WorldArchitect.AI. When conflicts arise between instructions, this hierarchy determines which instruction takes precedence.

### 1. CRITICAL FOUNDATION (Load First - Highest Authority)
These instructions form the core operational framework and MUST be loaded before all others:

1. **`game_state_instruction.md`** - State management protocol
   - Authority over: All state updates, data persistence, timeline management
   - Critical because: Without proper state management, nothing else functions

2. **`entity_schema_instruction.md`** - Entity data structures
   - Authority over: All entity ID formats, data schemas
   - Critical because: Defines how all game objects are structured

### 2. CORE MECHANICS (Load Second)
These define the fundamental game rules:

3. **`destiny_ruleset.md`** - Core game mechanics
   - Authority over: Combat, attributes, progression, all mechanical resolution
   - Supersedes: Any conflicting mechanics in other files

4. **`mechanics_system_instruction.md`** - System integration
   - Authority over: Dice rolling, leveling tiers, mechanical processes
   - Defers to: destiny_ruleset.md for core mechanics

### 3. NARRATIVE FRAMEWORK (Load Third)
These guide storytelling and interaction:

5. **`narrative_system_instruction.md`** - Storytelling protocol
   - Authority over: Think blocks, narrative flow, character generation process
   - Must respect: State management and mechanics from above

6. **`calibration_instruction.md`** - Campaign setup
   - Authority over: Initial calibration phase only
   - Becomes inactive: After campaign begins

### 4. TEMPLATES (Load Fourth)
These are reference formats:

7. **`character_sheet_template.md`** - Mechanical character data
8. **`character_template.md`** - Personality and narrative data
9. **`attribute_conversion_guide.md`** - Conversion rules between D&D and Destiny systems

### 5. PERSONALITY FILES (Load On-Demand)
Load only the specific files needed:

10. **`personalities/{mbti}_portrait.md`** - Character personality when type is known
11. **`personalities/{mbti}_growth.md`** - Character development arc when needed

#### Personality Loading Protocol

**CRITICAL: Do NOT bulk-load all 32 personality files**

1. **Detection Phase**: When a character's MBTI type is determined:
   - For Player Character: Load immediately after character creation
   - For NPCs: Load only when they become significant (recurring, important to plot)
   - For one-time encounters: Do not load personality files

2. **Loading Rules**:
   - Load `{mbti}_portrait.md` when character is introduced
   - Load `{mbti}_growth.md` only when:
     - Character reaches new tier of play
     - Major character development arc begins
     - Player specifically requests character growth information

3. **Memory Optimization**:
   - Maximum 4 personality sets loaded at once (PC + 3 major NPCs)
   - Unload personalities for characters who haven't appeared in 5+ sessions
   - Keep only portrait file loaded for background NPCs

4. **Example Loading Sequence**:
   ```
   Character Creation: PC is INFJ
   → Load: INFJ_portrait.md
   
   Session 5: PC reaches Tier 2
   → Load: INFJ_growth.md
   
   Session 8: Major NPC revealed as ENTJ
   → Load: ENTJ_portrait.md
   ```

## Conflict Resolution Rules

When instructions conflict, follow this precedence:

1. **State Management Always Wins**: If any instruction conflicts with state management protocol, state management takes precedence
2. **Mechanics Over Narrative**: Combat mechanics in destiny_ruleset.md override narrative descriptions
3. **Specific Over General**: More specific instructions override general ones
4. **Templates Are Examples**: Templates show format but don't override rules
5. **This Document Is Supreme**: If there's ambiguity, this hierarchy decides

## Authority Definitions

### State Authority (game_state_instruction.md)
- How to read and update game state
- State block formatting
- Timeline management
- Data persistence rules
- DELETE token processing

### Mechanical Authority (destiny_ruleset.md)
- Combat resolution and state schema
- Character attributes (5 aptitudes for Destiny, 6 attributes for D&D)
- Damage calculation
- Death and dying
- All dice-based resolution
- Attribute system determined by campaign_config.attribute_system

### Narrative Authority (narrative_system_instruction.md)
- Think block generation
- Story flow and pacing
- Character dialogue and description
- Planning blocks
- Narrative consequences

### Integration Authority (mechanics_system_instruction.md)
- How narrative and mechanics interact
- Leveling tier definitions
- Custom commands
- Combat presentation format

## Dual Attribute System Support

### System Detection Protocol
1. Check `custom_campaign_state.attribute_system` on every prompt
2. Value must be either "dnd" or "destiny"
3. If missing, default to "dnd" for backward compatibility
4. Never mix systems within a single campaign

### Attribute Mapping
When referencing attributes in mechanics:
- **D&D**: Use STR, DEX, CON, INT, WIS, CHA
- **Destiny**: Use Physique, Coordination, Health, Intelligence, Wisdom
- **Social Checks**: 
  - D&D: Use CHA modifier
  - Destiny: Use Personality Trait modifiers per `character_sheet_template.md`

### Conversion Reference
See `attribute_conversion_guide.md` for:
- 1:1 mappings for physical/mental attributes
- CHA ↔ Personality Traits conversion formulas
- Mechanical adaptations for each system

## Universal Naming Rules

### CRITICAL: Banned Names Enforcement
When creating ANY new character, location, or entity:
1. **Check the banned names list** in the world content section
2. **NEVER use any name from the banned list** - this is absolute
3. **Banned names include**: Common overused LLM names like Alaric, Corvus, Elara, Valerius, etc.
4. **Create unique, setting-appropriate names** instead
5. **This applies to**: NPCs, companions, locations, organizations, items, and any other named entity

### Naming Authority
- The banned names list in world content has ABSOLUTE AUTHORITY
- No other instruction can override the banned names restriction
- When in doubt, choose a different name

## Version Control

- Version 1.0: Initial hierarchy establishment
- Version 1.1: Added dual attribute system support
- Version 1.2: Added universal naming rules and banned names enforcement
- Future versions will be marked with clear changelog

## CRITICAL REMINDERS

1. **No "PRIORITY #1" Claims**: Individual files should not claim absolute priority
2. **Loading Order Matters**: Files loaded later can be ignored due to instruction fatigue
3. **State Updates Are Mandatory**: Never skip state updates regardless of other instructions
4. **This File Defines Truth**: When in doubt, consult this hierarchy
5. **Attribute System Check**: Always check campaign_config.attribute_system before processing character data
6. **System-Specific Resolution**: Use appropriate social mechanics (CHA for D&D, Personality Traits for Destiny)
7. **Banned Names Are Absolute**: Never use any name from the banned names list for any purpose

---

**END OF MASTER DIRECTIVE**