# String Matching Audit Results

## Overview
Found multiple instances of hardcoded string matching that should be replaced with LLM-based solutions per CLAUDE.md rule: "USE LLM CAPABILITIES: When designing command systems or natural language features: NEVER suggest keyword matching, regex patterns, rule-based parsing - ALWAYS leverage LLM's natural language understanding"

## High Priority Replacements

### 1. Planning Block Validation (`llm_service.py:1390-1450`)
**Current**: Hardcoded keyword matching for character creation detection
```python
is_character_approval: bool = (
    "[character creation" in response_lower
    and "character sheet" in response_lower
    and (
        "would you like to play as this character" in response_lower
        or "what is your choice?" in response_lower
        or "approve this character" in response_lower
    )
)
```
**Should be**: LLM-based detection of campaign creation state

### 2. Mode Switch Detection (`llm_service.py:1346`)
**Current**: Hardcoded phrase matching
```python
phrase in user_input.lower() for phrase in constants.MODE_SWITCH_PHRASES
```
**Should be**: LLM understanding of user intent to switch modes

### 3. Entity Validation (`entity_instructions.py:248-273`)
**Current**: Simple keyword matching for critical situations
```python
# Simple keyword matching - could be enhanced
return any(indicator in story_lower for indicator in critical_indicators)
```
**Should be**: LLM-based analysis of narrative urgency/criticality

### 4. Game State Location Sync (`game_state.py:183-199`)
**Current**: Hardcoded location word matching
```python
if "forest" in narrative_lower and "tavern" in location_lower:
elif "tavern" in narrative_lower and "forest" in location_lower:
```
**Should be**: LLM-based location understanding and conflict resolution

### 5. Entity Tracking (`entity_validator.py:169`)
**Current**: Simple substring matching
```python
if entity_lower in narrative_lower:
```
**Should be**: LLM-based entity mention detection with context

## Medium Priority

### 6. Debug Mode Parser (`debug_mode_parser.py`)
**Current**: "Regex-based pattern matching with extensive coverage"
**Analysis**: This may be appropriate for system commands, but should verify if it's user-facing

### 7. Narrative Movement Detection (`dual_pass_generator.py:272`)
**Current**: Word list matching for movement
```python
word in narrative_lower for word in ["moves", "walks", "turns", "looks"]
```
**Should be**: LLM understanding of player actions

## Recommended Implementation Strategy

### Phase 1: Critical Path Fixes
1. **Planning Block Validation**: Replace string matching with LLM-based campaign state tracking
2. **Character Creation State**: Use LLM to understand when in character creation vs active gameplay

### Phase 2: Game Logic Improvements
1. **Entity Detection**: Use LLM for entity mention analysis
2. **Location Synchronization**: LLM-based location understanding
3. **Mode Switch Detection**: Natural language intent recognition

### Phase 3: Enhancement Opportunities
1. **Movement Detection**: LLM-based action understanding
2. **Critical Situation Detection**: LLM analysis of urgency

## Implementation Notes

### LLM Integration Pattern
Instead of keyword matching, use structured prompts like:
```python
analysis_prompt = f"""
Analyze this user input in the context of a D&D campaign:
User input: "{user_input}"
Current state: {game_state_summary}

Is the user trying to:
1. Switch to GM/God mode? (yes/no)
2. Create a new character? (yes/no)
3. Make a character choice? (yes/no)

Return JSON with your analysis.
"""
```

### Benefits
- **Robust**: Handles natural language variations
- **Extensible**: Easily add new intent categories
- **Context-aware**: Considers full game state
- **Maintainable**: No hardcoded keyword lists to update
