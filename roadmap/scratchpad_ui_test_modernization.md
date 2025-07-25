# UI Test Suite Modernization - Scratchpad

**Branch:** explicit_char_design
**Date:** 2025-07-10
**Goal:** Transform 45-test suite into efficient 13-test core with mock/real hybrid architecture

## Problem Statement
- 45 UI tests are redundant/overlapping
- Tests are slow due to real Gemini API calls
- Expensive to run frequently (Gemini costs)
- User wants focused, fast test suite

## Solution Architecture
**Mock Gemini + Real Firebase Strategy:**
- Firebase is fast, reliable, no cost issues → Keep real
- Gemini is slow, expensive → Mock with real captured data
- Capture real responses from /testuif runs for authenticity

## Phase Plan

### Phase 1: Test Reorganization ⏳ IN PROGRESS
**Goal:** Restructure 45 tests into organized categories

**Core Tests (5):**
- test_wizard_character_setting.py - Our current PR work
- test_campaign_creation_browser.py - Core user journey
- test_api_response_structure.py - Backend validation
- test_structured_fields_browser.py - Game mechanics
- test_continue_campaign_browser.py - User retention

**Functionality Tests (8):**
- test_story_download_browser.py - Export features
- test_story_sharing_browser.py - Share features
- test_settings_browser.py - Settings management
- test_accessibility_browser.py - UX basics
- test_error_handling_browser.py - Error recovery
- test_character_management_browser.py - Character features
- test_campaign_deletion_browser.py - Delete campaigns
- test_performance_browser.py - Performance monitoring

**Archive (32):** All other tests → testing_ui/archive/

**Directory Structure:**
```
testing_ui/
├── archive/          # 32+ archived tests
├── mock_data/        # Captured Gemini responses
├── core_tests/       # 5 critical tests
├── functionality/    # 8 feature tests
└── utils/           # Test helpers (keep existing)
```

**Status:** ✅ Directories created, moving tests...

### Phase 2: Real API Data Capture
**Goal:** Run /testuif on core tests, capture Gemini responses

**Actions:**
1. Run /testuif on 5 core tests with real Gemini API
2. Capture successful API responses in structured format
3. Save to testing_ui/mock_data/ with organized naming
4. Document response patterns for mock system

**Expected Output:**
- mock_data/wizard_responses.json
- mock_data/campaign_creation_responses.json
- mock_data/api_structure_responses.json
- mock_data/structured_fields_responses.json
- mock_data/continue_campaign_responses.json

### Phase 3: Mock Infrastructure Implementation
**Goal:** Build hybrid mock system

**Actions:**
1. Create mock Gemini service using captured data
2. Keep real Firebase connections (fast, reliable)
3. Update tests to use mock Gemini + real Firebase
4. Ensure deterministic, repeatable results

**Benefits:**
- 10x faster test execution
- No Gemini API costs for /testui
- Real database operations still tested
- Authentic responses from real captures

### Phase 4: Validation & Optimization
**Goal:** Verify new system works perfectly

**Actions:**
1. Run /testui with new mock system
2. Compare results with /testuif baseline
3. Performance benchmarking
4. Update /testui and /testuif commands

**Success Criteria:**
- All 13 tests pass consistently
- /testui runs in <2 minutes (vs current timeout issues)
- /testuif still works for when real API testing needed
- Zero false positives/negatives

## Progress Log

### 2025-07-10 - Phase 1 COMPLETED ✅
- ✅ Created directory structure (archive/, mock_data/, core_tests/, functionality/)
- ✅ Moved 5 core tests to core_tests/
- ✅ Moved 8 functionality tests to functionality/
- ✅ Archived 32 redundant tests to archive/
- ✅ Updated test runner for new structure
- ✅ Created mock_data infrastructure with README

**Results:**
- **Before:** 45 tests (slow, expensive, overlapping)
- **After:** 13 tests (5 core + 8 functionality)
- **Archived:** 32 tests preserved but not run by default

### 2025-07-10 - Phase 2 PROGRESS: Real API Data Capture ⏳
**Goal:** Run /testuif on core tests to capture authentic Gemini responses

**✅ Critical Bug Discovery & Fix:**
- Found campaign_type wasn't being sent from frontend to backend
- Fixed frontend: Now sends `campaign_type: 'dragon-knight'` vs `'custom'`
- Fixed backend: Uses expanded Dragon Knight narrative when `campaign_type === 'dragon-knight'`
- **Verified**: Server logs show campaign type received correctly

**✅ Test Infrastructure Working:**
- Wizard test passes ✅ (character/setting inputs work)
- Campaign creation API working ✅ (both types)
- Port 6007 configuration working ✅ (no dev server conflicts)
- Test authentication working ✅ (X-Test-Bypass-Auth headers)

**⚠️ Mock Data Strategy - Real Capture Needed:**
User wants authentic Gemini responses for key tests:
1. Capture real Gemini responses for 5 core tests (costs money but authentic)
2. Build hybrid system: Mock Gemini + Real Firebase
3. Toggle between `/testui` (mock) and `/testuif` (real) modes
4. Firebase stays real (fast, reliable, no cost issues)

### Next Steps
1. ✅ Phase 1 complete
2. ✅ Campaign type bug fixed
3. ✅ Mock data created from known Dragon Knight content
4. ✅ Mock Gemini service built and tested
5. ⏳ Integrate mock system with backend
6. ⏳ Update test commands for /testui vs /testuif

## Questions/Decisions
- **Firebase mocking?** Decision: Keep real Firebase (fast, reliable, no cost issues)
- **Mock data format?** JSON files with structured Gemini response objects
- **Test selection criteria?** Core user flows + essential features only

## Notes
- Fixed critical bug during discovery: campaign_type wasn't being sent to backend
- This reorganization will prevent similar issues by focusing tests on core flows
- Current branch has character/setting wizard changes that need validation
