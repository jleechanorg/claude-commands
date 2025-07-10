# Master Directive: WorldArchitect.AI Prompt Hierarchy
**Version: 1.5**
**Last Updated: 2025-07-04**

## Critical Loading Order and Precedence

This document establishes the authoritative hierarchy for all AI instructions in WorldArchitect.AI. When conflicts arise between instructions, this hierarchy determines which instruction takes precedence.

### 1. CRITICAL FOUNDATION (Load First - Highest Authority)
These instructions form the core operational framework and MUST be loaded before all others:

1. **`game_state_instruction.md`** - State management protocol and entity schemas
   - Authority over: All state updates, data persistence, timeline management, entity structures
   - Critical because: Without proper state management, nothing else functions

2. **`dnd_srd_instruction.md`** - Core D&D 5E mechanical authority
   - Authority over: All combat, attributes, spells, and mechanical resolution
   - Critical because: Establishes single mechanical system authority

### 2. CORE MECHANICS (Load Second)
These define the fundamental game rules:

3. **`mechanics_system_instruction.md`** - System integration
   - Authority over: Character design (when mechanics enabled), dice rolling, leveling tiers, mechanical processes
   - Defers to: dnd_srd_instruction.md for core mechanics
   - Special role: Triggers mandatory character design when mechanics checkbox is selected

### 3. NARRATIVE FRAMEWORK (Load Third)
These guide storytelling and interaction:

4. **`narrative_system_instruction.md`** - Storytelling protocol
   - Authority over: Think blocks, narrative flow, story progression
   - Must respect: State management and mechanics from above

### 3. TEMPLATES (Load When Needed)
These are reference formats:

5. **`character_template.md`** - Character personality and narrative data
   - Authority over: Character depth requirements and personality templates
   - Load when: Detailed NPC development needed
   - Note: Character design process is handled by mechanics_system_instruction.md

## Core File Dependencies

**Essential Files for All Operations:**
1. `master_directive.md` (this file) - Loading hierarchy
2. `game_state_instruction.md` - State management and entity schemas  
3. `dnd_srd_instruction.md` - D&D 5E mechanical authority

**Context-Dependent Files:**
4. `narrative_system_instruction.md` - When storytelling needed
5. `mechanics_system_instruction.md` - When mechanical resolution needed
6. `character_template.md` - When character design/development needed

## Conflict Resolution Rules

When instructions conflict, follow this precedence:

1. **State Management Always Wins**: If any instruction conflicts with state management protocol, state management takes precedence
2. **D&D 5E Mechanics Over Narrative**: Combat mechanics in dnd_srd_instruction.md override narrative descriptions  
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

### Mechanical Authority (dnd_srd_instruction.md)
- Combat resolution using D&D 5E SRD rules
- Character attributes (STR, DEX, CON, INT, WIS, CHA)
- Damage calculation
- Death and dying
- All dice-based resolution

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

## Campaign Initialization Protocol

### Order of Operations for New Campaigns

When starting a new campaign, follow this exact sequence:

1. **Load Instructions** (in hierarchy order per this document)
2. **Check Mechanics Checkbox**:
   - If ENABLED: Character design is MANDATORY (see below)
   - If DISABLED: Skip to step 4
3. **Character Design** (when mechanics enabled):
   - STOP before any narrative or background
   - Present character design options FIRST
   - Wait for player to create/approve character
   - Only proceed after character is finalized
4. **World Background**:
   - Describe setting and initial situation
   - If character exists: Include them in narrative
   - If no character: Keep description general
5. **Begin Gameplay**:
   - Present initial scene
   - Provide planning block with options

### Character Design Authority

When mechanics is enabled, `mechanics_system_instruction.md` has absolute authority over character design timing and process. The character design MUST happen before any story narrative begins.
**CRITICAL: The character design process still needs to respect the main character prompt from the player if specified**

## D&D 5E SRD System Authority

This campaign uses **D&D 5E System Reference Document (SRD) rules exclusively**. All attribute references use the standard D&D attributes: STR, DEX, CON, INT, WIS, CHA.

## Universal Naming Rules

### CRITICAL: Avoid Overused Names

**MANDATORY PRE-GENERATION CHECK**: Before suggesting or creating ANY character during character creation OR during the campaign (NPCs, companions, villains, etc.), you MUST:
1. **CHECK the CRITICAL NAMING RESTRICTIONS FIRST** - Find and review the section titled "CRITICAL NAMING RESTRICTIONS (from banned_names.md)" in your world content
2. **NEVER use banned names** - Do not suggest Alaric, Corvus, Elara, Valerius, Seraphina, Lysander, Thane, or ANY of the 56 names in that CRITICAL NAMING RESTRICTIONS section
3. **GENERATE unique, creative names** - Create original names that are NOT in the CRITICAL NAMING RESTRICTIONS
4. **This check happens BEFORE name generation** - Not after
5. **This applies to ALL characters** - Player characters, NPCs, enemies, allies, merchants, quest givers, EVERYONE

**CLARIFICATION**: The CRITICAL NAMING RESTRICTIONS contains names to AVOID. You should create NEW, ORIGINAL names that are NOT in the CRITICAL NAMING RESTRICTIONS section. The examples above (Alaric, Corvus, etc.) are shown to illustrate what NOT to use.


### Naming Authority
- Original, creative naming takes precedence over generic fantasy names
- Avoid repetitive use of the same name patterns across campaigns
- **Player Override**: If a player chooses a name (even a banned one), you MUST:
  1. Acknowledge their choice explicitly
  2. If it's on a banned list, explain why it's discouraged
  3. Offer alternatives BUT also offer to use it anyway if they prefer
  4. NEVER silently substitute without consent - player agency is paramount

## Version Control

- Version 1.0: Initial hierarchy establishment
- Version 1.1: Simplified to D&D 5E SRD-only system
- Version 1.2: Added universal naming rules and banned names enforcement
- Version 1.3: Added Campaign Initialization Protocol and character design flow
- Version 1.4: Added player override authority for names and absolute transparency requirement
- Version 1.5: Added mandatory pre-generation check for banned names during ALL character design (PCs and NPCs)
- Future versions will be marked with clear changelog

## CRITICAL REMINDERS

1. **No "PRIORITY #1" Claims**: Individual files should not claim absolute priority
2. **Loading Order Matters**: Files loaded later can be ignored due to instruction fatigue
3. **State Updates Are Mandatory**: Never skip state updates regardless of other instructions
4. **This File Defines Truth**: When in doubt, consult this hierarchy
5. **D&D 5E SRD Compliance**: Always use standard D&D attributes and rules
6. **Social Mechanics**: Use CHA-based D&D 5E social mechanics
7. **CRITICAL NAMING RESTRICTIONS Are Absolute**: Never use any name from the CRITICAL NAMING RESTRICTIONS section for any purpose
8. **Pre-Generation Name Check**: ALWAYS check CRITICAL NAMING RESTRICTIONS BEFORE suggesting character names

---

**END OF MASTER DIRECTIVE**