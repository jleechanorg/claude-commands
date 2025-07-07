# Entity Field Integration Scratchpad

## Project Goal
Create a comprehensive superset of entity fields by integrating the best aspects of entities_simple.py, entities.py (Pydantic), and game_state_instruction.md to provide robust support for both narrative consistency and complete D&D 5e mechanics.

## Implementation Plan

### Phase 1: Analysis and Design ✅
- [x] Compare field definitions across all three sources
- [x] Identify unique fields, overlapping implementations, and missing critical fields  
- [x] Create comprehensive field matrix and integration recommendations
- [x] Prioritize missing fields by importance (High/Medium/Low)

### Phase 2: Core Integration (Next)
- [ ] Enhance entities_simple.py with high-priority missing fields
- [ ] Add D&D fundamentals: class_name, alignment, mbti, armor_class, proficiency_bonus
- [ ] Implement combat stats and active effects tracking
- [ ] Add comprehensive resource tracking from LLM documentation
- [ ] Maintain defensive programming and validation patterns

### Phase 3: Schema Synchronization
- [ ] Update game_state_instruction.md entity examples to match enhanced schema
- [ ] Verify all LLM documentation reflects the integrated field set
- [ ] Test entity creation with new comprehensive fields
- [ ] Validate backward compatibility with existing campaigns

### Phase 4: Testing and Validation
- [ ] Extend test_age_field_validation.py to cover all new fields
- [ ] Create integration tests for D&D mechanics (AC, proficiency, etc.)
- [ ] Test narrative consistency with enhanced fields
- [ ] Validate defensive conversion for new numeric fields

## Current State: Analysis Complete

### Key Findings
**Critical Missing Fields in Current Implementation:**
1. **gender & age** - Present in Simple, missing in Pydantic ⚠️
2. **mbti** - Missing in both, critical for roleplay consistency
3. **alignment** - Fundamental D&D attribute, missing in both
4. **class_name** - Core D&D identity, missing in both  
5. **armor_class** - Essential combat stat, missing in both
6. **proficiency_bonus** - Core D&D mechanic, missing in both

**Unique Strengths by Source:**
- **Simple**: Gender/age validation, defensive programming
- **Pydantic**: Strong validation, JSON schema generation
- **LLM Docs**: Complete D&D 5e resource tracking, consumables

## Next Steps
1. Enhance entities_simple.py with missing high-priority fields
2. Implement D&D fundamental attributes (class, alignment, AC)
3. Add MBTI for consistent character roleplay
4. Integrate detailed resource tracking from LLM documentation
5. Update LLM instructions to reflect enhanced schema

## Key Context
- Using Simple schema system (USE_PYDANTIC=false)
- Must maintain defensive programming patterns
- Gender/age validation already implemented for narrative consistency
- Focus on backward compatibility while adding comprehensive D&D support

## Branch Info
- Branch: luke_campaign_fixes
- Goal: Complete entity field integration for narrative consistency and D&D mechanics
- Integration target: Current simple schema with enhanced field set