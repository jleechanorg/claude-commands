# TASK-111: LLM Narrative Improvements - Requirements & Implementation

## Task Overview
Fix direct alignment mentions in narrative, improve subtlety in character descriptions, and update prompts to avoid meta-game references.

## Current Issues Identified
1. **Direct Alignment Mentions**: AI occasionally references D&D alignment terms explicitly in narrative
2. **Character Description Subtlety**: Character descriptions may be too obvious or heavy-handed
3. **Meta-Game References**: Prompts may contain references that break immersion

## Requirements Definition

### 1. Direct Alignment Fix
- **Problem**: AI mentions "Lawful Good", "Chaotic Neutral", etc. in narrative text
- **Solution**: Update prompts to use "moral compass" terminology that was already implemented
- **Implementation**: 
  - Review all narrative generation prompts
  - Replace any remaining alignment references with descriptive moral compass language
  - Test with sample generations to ensure compliance

### 2. Character Description Subtlety
- **Problem**: Character descriptions may be too direct or obvious
- **Solution**: Implement "show don't tell" principles
- **Implementation**:
  - Review character description prompts
  - Add examples of subtle character revelation through actions/dialogue
  - Update system instructions to emphasize subtlety

### 3. Meta-Game Reference Elimination
- **Problem**: Prompts may contain game mechanics or meta-references that break immersion
- **Solution**: Audit all prompts for immersion-breaking content
- **Implementation**:
  - Comprehensive prompt review
  - Replace meta-game language with in-world equivalents
  - Add explicit instructions against meta-game references

## Files to Review/Update
- `mvp_site/prompts/narrative_system_instruction.md`
- `mvp_site/prompts/character_template.md`
- `mvp_site/prompts/game_state_instruction.md`
- Any other system instruction files

## Success Criteria
- [ ] No direct alignment mentions in generated narrative
- [ ] Character descriptions use subtle, indirect methods
- [ ] All prompts free of meta-game references
- [ ] Integration test shows improved narrative quality

## Estimated Time: 1 hour
- Prompt audit: 30 minutes
- Updates and testing: 30 minutes

## Dependencies
- None (can be completed independently)

## Testing Plan
- Generate sample narratives before/after changes
- Run integration test to verify no regressions
- Manual review of character descriptions