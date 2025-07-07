# Browser Tests Remaining - Scratchpad

## Current Status
✅ **COMPLETED TESTS:**
- Campaign Creation Test (`test_campaign_creation_browser_v2.py`) - WORKING
- Campaign Continuation Test (`test_continue_campaign_browser_v2.py`) - WORKING

## Framework Status
✅ Shared test framework created (`browser_test_base.py`)
✅ Flask server management with automatic cleanup
✅ Test mode authentication bypass working
✅ Screenshot management standardized to `/tmp/worldarchitect_browser_screenshots`

## Remaining Test Cases to Implement

### 1. God Mode Test
- **File**: `test_god_mode_browser.py` (needs conversion to v2 framework)
- **Coverage**: God mode toggle, command input, state verification
- **Status**: Exists but needs to use new framework

### 2. Campaign Deletion Test
- **Coverage**: Delete campaign from dashboard, confirm deletion dialog, verify removal
- **Priority**: HIGH - Critical user flow

### 3. Settings Management Test
- **Coverage**: Theme switching, auto-save toggle, display preferences
- **Priority**: MEDIUM - User experience feature

### 4. Search Functionality Test
- **Coverage**: Search campaigns by name, filter by date, search within story
- **Priority**: MEDIUM - Important for users with many campaigns

### 5. Story Download Test
- **Coverage**: Download story as text file, verify content
- **Priority**: LOW - Export feature

### 6. Story Sharing Test
- **Coverage**: Share story link generation, clipboard copy
- **Priority**: LOW - Social feature

### 7. Character/NPC Management Test
- **Coverage**: View character sheets, modify attributes, track inventory
- **Priority**: HIGH - Core gameplay feature

### 8. Combat System Test
- **Coverage**: Enter combat, roll dice, track HP, exit combat
- **Priority**: HIGH - Core gameplay feature

### 9. Multi-Campaign Management Test
- **Coverage**: Create multiple campaigns, switch between them, verify isolation
- **Priority**: HIGH - Data integrity critical

### 10. Error Handling Test
- **Coverage**: Network errors, API failures, graceful degradation
- **Priority**: HIGH - User experience critical

### 11. Long Story Performance Test
- **Coverage**: Test with very long story (50+ interactions), verify performance
- **Priority**: MEDIUM - Scalability concern

### 12. Concurrent Session Test
- **Coverage**: Multiple browser tabs, verify no conflicts
- **Priority**: MEDIUM - Edge case but important

### 13. Mobile Responsive Test
- **Coverage**: Test on mobile viewport sizes, touch interactions
- **Priority**: LOW - Future enhancement

### 14. Accessibility Test
- **Coverage**: Keyboard navigation, screen reader compatibility
- **Priority**: LOW - Future enhancement

## Implementation Order Recommendation

1. **Phase 1 - Core Functionality** (HIGH priority)
   - God Mode Test (convert existing)
   - Campaign Deletion Test
   - Character/NPC Management Test
   - Combat System Test
   - Multi-Campaign Management Test
   - Error Handling Test

2. **Phase 2 - User Experience** (MEDIUM priority)
   - Settings Management Test
   - Search Functionality Test
   - Long Story Performance Test
   - Concurrent Session Test

3. **Phase 3 - Nice to Have** (LOW priority)
   - Story Download Test
   - Story Sharing Test
   - Mobile Responsive Test
   - Accessibility Test

## Notes
- All tests should use the `BrowserTestBase` framework
- Each test should capture screenshots at key points
- Tests should verify both happy path and error cases
- Consider adding performance metrics to tests
- May need to add test data fixtures for complex scenarios