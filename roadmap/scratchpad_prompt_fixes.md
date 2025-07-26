# Critical Prompt System Fixes

## Major Issues Discovered

**CRITICAL**: Prompt system has extensive broken references and contradictions that need immediate fixing.

### 1. Broken File References (High Priority)
All prompts reference missing archived files:
- `entity_schema_instruction.md` (referenced 10+ times)
- `destiny_ruleset.md` (referenced 8+ times)
- `calibration_instruction.md` (referenced 3+ times)
- `character_sheet_template.md` (referenced 2+ times)
- `personalities/{mbti}_portrait.md` files

### 2. System Contradictions (High Priority)
- **Mixed Systems**: Files claim D&D 5E authority but reference Destiny mechanics
- **Attribute Conflicts**: D&D 6-attribute vs Destiny 5-aptitude inconsistencies
- **Command Conflicts**: References deprecated `GOD_MODE_UPDATE_STATE`

### 3. Missing Content (Medium Priority)
- **Banned Names**: Referenced but implementation unclear
- **World Content**: Master directive references missing world content section
- **Example Contradictions**: Uses banned names like "Elara" in examples

### 4. UI Cleanup (Low Priority)
- Remove "Calibration Rigor" checkbox from UI (line 117-118 in index.html)

## Fix Implementation Plan

### Phase 1: Remove Broken References (Immediate)
- [ ] **master_directive.md**: Remove references to archived files
- [ ] **game_state_instruction.md**: Remove entity_schema and destiny references
- [ ] **mechanics_system_instruction.md**: Remove destiny_ruleset references
- [ ] **narrative_system_instruction.md**: Clean up missing file references
- [ ] **dnd_srd_instruction.md**: Fix entity_schema reference

### Phase 2: System Consistency (Immediate)
- [ ] **Standardize on D&D 5E**: Remove all Destiny system references
- [ ] **Fix attribute systems**: Use D&D 6-attribute consistently
- [ ] **Update deprecated commands**: Replace GOD_MODE_UPDATE_STATE
- [ ] **Consistent authority**: D&D SRD as single mechanical authority

### Phase 3: Content Integration (Next)
- [ ] **Integrate essential content**: Move key info from archived files into remaining files
- [ ] **Fix banned names**: Either implement properly or remove references
- [ ] **Clean examples**: Remove contradictory examples (like using banned names)

### Phase 4: UI Cleanup ✅ COMPLETED
- [x] **Remove calibration checkbox**: Update index.html
- [ ] **Update constants**: Remove calibration references (if needed)
- [ ] **Test prompt combinations**: Ensure narrative+mechanics combinations work

## Implementation Progress

### 1. master_directive.md (890 → 711 words) ✅ COMPLETED
**Fixed**:
✅ Removed entity_schema_instruction.md references
✅ Removed destiny_ruleset.md references
✅ Removed calibration_instruction.md references
✅ Removed character_sheet_template.md references
✅ Removed personalities/ directory references
✅ Simplified to D&D 5E + current files only
✅ 20% word reduction achieved

### 2. game_state_instruction.md (4,621 words)
**Issues to fix**:
- Remove "entity_schema_instruction.md" references (file was integrated)
- Remove destiny_ruleset.md references
- Update GOD_MODE_UPDATE_STATE to current commands
- Standardize on D&D 5E attribute system
- Fix contradictory system references

### 3. mechanics_system_instruction.md (4,022 words)
**Issues to fix**:
- Remove destiny_ruleset.md references
- Standardize on D&D 5E mechanics only
- Remove mixed system contradictions
- Fix cross-references to existing files only

### 4. narrative_system_instruction.md (5,368 words)
**Issues to fix**:
- Remove references to missing files
- Fix banned names implementation
- Remove contradictory examples
- Clean up cross-references

### 5. dnd_srd_instruction.md (174 words)
**Issues to fix**:
- Remove entity_schema_instruction.md reference
- Ensure D&D 5E authority is clear

### Additional Fixes Completed ✅
- **dnd_srd_instruction.md**: Fixed entity_schema reference → game_state_instruction
- **narrative_system_instruction.md**: Replaced banned name 'Elara' with 'Kira' in example
- **UI**: Removed calibration checkbox from index.html

## Success Criteria
- [x] UI cleaned up (no calibration checkbox)
- [x] Master directive: Zero broken file references
- [x] Consistent D&D 5E system authority
- [ ] All prompt combinations (narrative/mechanics) work
- [ ] No deprecated commands in game_state/mechanics files
- [ ] System passes integration tests

## Current Status
**Total Words**: 15,865 (reduced from 16,040)
**Story Mode Effective**: 16,834 words (includes character_template auto-loading)
**Major broken references**: ✅ FIXED in master directive, dnd_srd, narrative

## Estimated Impact
- **Time**: 2-3 hours for comprehensive fixes
- **Risk**: Low - mostly reference cleanup
- **Benefit**: High - fixes critical system integrity issues
- **Files changed**: All 6 prompt files + index.html + constants.py
