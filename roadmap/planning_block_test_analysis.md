# Planning Block Test Analysis

## Test File Inventory

### Core Planning Block Test Files (5 files)
1. **test_planning_block_enforcement.py** (33KB) - Tests planning block validation and enforcement
2. **test_planning_block_json_corruption_fix.py** (7KB) - Tests JSON corruption fixes
3. **test_planning_block_json_first_fix.py** (3KB) - Tests JSON-first implementation
4. **test_planning_block_simplified.py** (6KB) - Simplified planning block tests
5. **test_planning_blocks_ui.py** (3KB) - UI-related planning block tests

### Files with Planning Block Tests (additional)
- test_character_extraction_regex_bug.py
- test_narrative_response_extraction.py
- test_main_interaction_structured_fields.py
- test_structured_fields_storage.py
- test_extra_json_fields.py
- test_gemini_response_structured_fields.py

## Analysis Categories

### 1. JSON Field Tests (Keep)
- test_planning_block_json_first_fix.py
- test_planning_block_json_corruption_fix.py
- Parts of test_extra_json_fields.py
- Parts of test_structured_fields_storage.py

### 2. Enforcement/Validation Tests (Keep but Update)
- test_planning_block_enforcement.py (needs update to remove narrative references)

### 3. UI/Frontend Tests (Keep)
- test_planning_blocks_ui.py

### 4. Redundant/Similar Tests (Consolidate)
- test_planning_block_simplified.py (appears to duplicate other tests)
- Multiple tests checking same JSON extraction

### 5. Narrative Parsing Tests (Remove)
- Any tests that verify "--- PLANNING BLOCK ---" parsing
- Tests that check narrative text extraction

## Consolidation Plan

### Phase 1: Remove Deprecated Tests
1. Remove narrative parsing tests from all files
2. Remove tests that check for "--- PLANNING BLOCK ---" markers

### Phase 2: Merge Similar Tests
1. Combine test_planning_block_json_first_fix.py and test_planning_block_json_corruption_fix.py into single test_planning_block_json.py
2. Merge test_planning_block_simplified.py functionality into appropriate files

### Phase 3: Update Remaining Tests
1. Update test_planning_block_enforcement.py to only test JSON field enforcement
2. Ensure all tests validate JSON-first approach

### Target Structure (from 5+ files to 3 files)
1. **test_planning_block_json.py** - All JSON field handling tests
2. **test_planning_block_enforcement.py** - Validation and enforcement logic
3. **test_planning_blocks_ui.py** - Frontend/UI tests

## Next Steps
1. Execute removal of narrative tests
2. Merge similar test files
3. Update test assertions to match new architecture
4. Run full test suite to ensure coverage