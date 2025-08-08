# TDD: Planning Block Missing After Campaign Creation - V1/V2 Side-by-Side Comparison

## Purpose
Red-Green-Refactor TDD approach to fix missing planning block functionality in React V2 after campaign creation by comparing with Flask V1 behavior.

## Critical Issue Identified
After campaign creation in React V2, the **planning block** with character choices is missing, causing a significant UX regression compared to Flask V1.

## Test Environment Requirements
- **Flask V1 Server**: Running at `http://localhost:5005` (baseline behavior)
- **React V2 Server**: Running at `http://localhost:3002` (implementation under test)
- **Real Authentication**: Google OAuth (no mock/test mode)
- **Browser Automation**: Playwright MCP (headless mode)

## TDD Test Specification

### Phase 1: RED TESTS (Should FAIL - Missing Planning Block)

#### Test 1.1: Post-Creation Planning Block Presence
**Requirement**: After campaign creation, both V1 and V2 should display planning block with character choices

**V1 Expected Behavior** (Baseline):
1. Navigate to `http://localhost:5005`
2. Complete Google OAuth authentication
3. Create a new campaign (Dragon Knight or Custom)
4. After creation success, verify planning block appears with:
   - Character action choices (3-5 options)
   - "Other" option available
   - Properly formatted choice buttons/interface

**V2 Current Behavior** (Should FAIL):
1. Navigate to `http://localhost:3002`  
2. Complete Google OAuth authentication
3. Create a new campaign (Dragon Knight or Custom)
4. After creation success, verify planning block:
   - **EXPECTED FAILURE**: Planning block missing or incomplete
   - Character choices not displayed
   - Game interface lacks interactive elements

**Evidence Required**:
- Screenshot: `docs/v1_post_creation_planning_block.png`
- Screenshot: `docs/v2_missing_planning_block.png` 
- Console logs showing API response structure
- Network requests for campaign creation and game state

#### Test 1.2: API Response Structure Validation
**Requirement**: Both V1 and V2 should receive `planning_block` field in API responses

**API Response Analysis**:
1. **V1 API Response** (after campaign creation):
   - Check for `planning_block` field presence
   - Validate structure: `{thinking: string, choices: object}`
   - Verify choices have proper format: `{choice_id: "description"}`

2. **V2 API Response** (after campaign creation):
   - Check for `planning_block` field presence
   - **EXPECTED FINDING**: Missing or malformed planning block
   - Document exact response structure differences

**Evidence Required**:
- Network logs: `docs/v1_api_response_structure.json`
- Network logs: `docs/v2_api_response_structure.json`
- Console output showing response differences

### Phase 2: GREEN TESTS (Implementation Target)

#### Test 2.1: V2 Planning Block Implementation
**Requirement**: After fixing, V2 should match V1 planning block behavior exactly

**Implementation Target**:
1. React V2 receives planning block data from API
2. Planning block component renders character choices
3. Choices are interactive and properly formatted
4. UI matches or exceeds V1 user experience

**Success Criteria**:
- Planning block appears immediately after campaign creation
- Character choices are clickable and functional
- Visual design consistent with V2 theme
- No console errors in planning block rendering

**Evidence Required**:
- Screenshot: `docs/v2_fixed_planning_block.png`
- Code references: Components implementing planning block display
- Console logs showing successful rendering

#### Test 2.2: End-to-End Behavioral Parity
**Requirement**: Complete user journey should be identical between V1 and V2

**User Journey Validation**:
1. Authentication → Dashboard → Create Campaign → Planning Block → Character Action
2. Both V1 and V2 complete the same journey without UX gaps
3. Planning block interactions work correctly in both versions

**Success Criteria**:
- No missing steps in V2 user journey
- Planning block interactions function correctly
- User can proceed to next game state seamlessly

**Evidence Required**:
- Screenshot comparison: `docs/v1_v2_journey_comparison.png`
- Behavioral flow documentation
- Interaction testing results

### Phase 3: REFACTOR TESTS (Code Quality)

#### Test 3.1: Component Architecture Quality
**Requirement**: Planning block implementation should be maintainable and reusable

**Architecture Validation**:
- Planning block is a reusable React component
- Proper separation of concerns (data vs presentation)
- TypeScript type safety for planning block data
- Consistent with existing V2 component patterns

#### Test 3.2: Error Handling Robustness  
**Requirement**: Planning block gracefully handles missing or malformed data

**Error Scenarios**:
- API returns no planning_block field
- Planning block has missing choices
- Network request fails during planning block fetch

## Systematic Validation Protocol

### Pre-Execution Checklist
- [ ] Flask V1 server running and accessible at :5005
- [ ] React V2 server running and accessible at :3002
- [ ] Google OAuth credentials configured for real authentication
- [ ] Playwright MCP available for browser automation
- [ ] Network connectivity verified for both servers

### Evidence Collection Requirements
- [ ] Screenshots saved to `docs/` directory with descriptive names
- [ ] API response logs captured and saved as JSON files
- [ ] Console error messages documented with exact text
- [ ] Network request/response data captured for analysis
- [ ] Code file references with specific line numbers

### Success Declaration Criteria
- [ ] ALL RED tests show expected failures (missing planning block in V2)
- [ ] ROOT CAUSE identified through side-by-side comparison
- [ ] IMPLEMENTATION PATH clearly documented
- [ ] Evidence portfolio complete with file references
- [ ] Actionable fix recommendations provided

## Priority Classification
- **CRITICAL**: Planning block missing prevents core gameplay progression
- **HIGH**: User experience regression from V1 to V2
- **MEDIUM**: Code architecture and maintainability concerns

## Expected Outcomes
1. **RED PHASE**: Confirm V2 missing planning block vs V1 working implementation
2. **GREEN PHASE**: Clear implementation requirements for V2 planning block fix
3. **REFACTOR PHASE**: Code quality guidelines for maintainable implementation

## Implementation Notes
- Focus on behavioral comparison, not visual styling differences
- Prioritize functional parity over visual perfection
- Document exact API response structure differences
- Identify minimal code changes needed for fix