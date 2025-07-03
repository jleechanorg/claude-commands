# Master Directive: WorldArchitect.AI Prompt Hierarchy
**Version: 1.0**
**Last Updated: 2025-01-07**

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
   - Authority over: Dice rolling, leveling tiers, mechanical processes
   - Defers to: dnd_srd_instruction.md for core mechanics

### 3. NARRATIVE FRAMEWORK (Load Third)
These guide storytelling and interaction:

4. **`narrative_system_instruction.md`** - Storytelling protocol
   - Authority over: Think blocks, narrative flow, character generation process
   - Must respect: State management and mechanics from above

### 3. TEMPLATES (Load When Needed)
These are reference formats:

5. **`character_template.md`** - Character personality and narrative data
   - Authority over: Character creation process and depth requirements
   - Load when: Character creation or detailed NPC development needed

## Core File Dependencies

**Essential Files for All Operations:**
1. `master_directive.md` (this file) - Loading hierarchy
2. `game_state_instruction.md` - State management and entity schemas  
3. `dnd_srd_instruction.md` - D&D 5E mechanical authority

**Context-Dependent Files:**
4. `narrative_system_instruction.md` - When storytelling needed
5. `mechanics_system_instruction.md` - When mechanical resolution needed
6. `character_template.md` - When character creation/development needed

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

## D&D 5E SRD System Authority

This campaign uses **D&D 5E System Reference Document (SRD) rules exclusively**. All attribute references use the standard D&D attributes: STR, DEX, CON, INT, WIS, CHA.

## Universal Naming Rules

### CRITICAL: Avoid Overused Names
When creating ANY new character, location, or entity:
1. **Avoid common overused LLM names** like Alaric, Corvus, Elara, Valerius, Seraphina, Thane, etc.
2. **Create unique, setting-appropriate names** instead
3. **This applies to**: NPCs, companions, locations, organizations, items, and any other named entity
4. **When in doubt**: Choose more creative, original names that fit the setting

### Naming Authority
- Original, creative naming takes precedence over generic fantasy names
- Avoid repetitive use of the same name patterns across campaigns

## Version Control

- Version 1.0: Initial hierarchy establishment
- Version 1.1: Simplified to D&D 5E SRD-only system
- Version 1.2: Added universal naming rules and banned names enforcement
- Future versions will be marked with clear changelog

## CRITICAL REMINDERS

1. **No "PRIORITY #1" Claims**: Individual files should not claim absolute priority
2. **Loading Order Matters**: Files loaded later can be ignored due to instruction fatigue
3. **State Updates Are Mandatory**: Never skip state updates regardless of other instructions
4. **This File Defines Truth**: When in doubt, consult this hierarchy
5. **D&D 5E SRD Compliance**: Always use standard D&D attributes and rules
6. **Social Mechanics**: Use CHA-based D&D 5E social mechanics
7. **Banned Names Are Absolute**: Never use any name from the banned names list for any purpose

---

**END OF MASTER DIRECTIVE**