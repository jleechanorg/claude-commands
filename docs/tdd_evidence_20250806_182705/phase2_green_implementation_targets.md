PHASE 2: GREEN TESTS - V2 IMPLEMENTATION TARGETS
===============================================

TIMESTAMP: 2025-08-06 18:52:00

## Test 2.1: V2 Planning Block Implementation Target

### REQUIREMENT
After fixing, V2 should match V1 planning block behavior exactly

### IMPLEMENTATION TARGET SPECIFICATION

#### 1. API Integration Fix
**CRITICAL**: Add missing campaign retrieval step
```javascript
// REQUIRED: Add this API call after campaign creation
const campaignResponse = await fetch(`/api/campaigns/${campaignId}`, {
  method: 'GET',
  headers: { 'Authorization': `Bearer ${token}` }
});
const campaignData = await campaignResponse.json();
```

#### 2. Planning Block Data Structure
**Expected API Response Structure** (based on V1 evidence):
```json
{
  "id": "campaign_id",
  "name": "Campaign Name",
  "planning_block": {
    "thinking": "AI reasoning about character options for this specific campaign",
    "choices": {
      "AIGenerated": "I'll create a complete D&D version based on their lore...",
      "CustomClass": "We'll create custom mechanics for their unique abilities...",
      "StandardDND": "You choose from D&D races and classes...",
      "Other": "Custom action option"
    }
  }
}
```

#### 3. React Component Requirements
**Planning Block Component Specifications**:
- Component name: `PlanningBlock` or `CharacterChoices`
- Props: `planningData: { thinking: string, choices: object }`
- Renders 4 character choice buttons based on choices object
- Each button displays choice description text
- Buttons are interactive (onClick handlers)
- Visual styling consistent with V2 theme (modern, clean)

#### 4. User Experience Targets
**Functional Requirements**:
- Planning block appears immediately after campaign creation success
- Character choices are clearly displayed with readable descriptions
- All choice buttons are clickable and responsive
- Planning block container visually distinct from other UI elements
- No console errors during planning block rendering
- Smooth transition from campaign creation to planning block display

#### 5. Integration Points
**Campaign Flow Integration**:
1. User completes campaign creation form
2. POST /api/campaigns → success response
3. **NEW**: GET /api/campaigns/{id} → retrieve planning_block data
4. **NEW**: Render PlanningBlock component with choice options
5. User selects character choice → proceed to game interaction

### SUCCESS CRITERIA CHECKLIST
- [ ] Planning block appears immediately after campaign creation
- [ ] 4 character choices are displayed (AIGenerated, CustomClass, StandardDND, Other)
- [ ] Choice descriptions match V1 functionality (clear, actionable text)
- [ ] All buttons are interactive and properly formatted
- [ ] Visual design consistent with V2 modern theme
- [ ] No console errors in planning block rendering
- [ ] Campaign data loads successfully via GET API call
- [ ] planning_block field is properly parsed and displayed

### EVIDENCE REQUIREMENTS FOR GREEN STATE
**Required Screenshots**:
- `docs/v2_fixed_planning_block.png` - Shows working planning block in V2
- `docs/v1_v2_side_by_side_comparison.png` - Visual parity verification

**Required Code References**:
- Component file implementing planning block display
- API integration code adding GET campaign call
- Specific line numbers for planning block rendering logic

**Required Console Logs**:
- Successful planning block data loading
- No console errors during rendering
- Confirmation of component mount and data display

### IMPLEMENTATION PRIORITY
**HIGH PRIORITY FIXES**:
1. Add GET /api/campaigns/{id} API call after creation
2. Create PlanningBlock React component
3. Integrate component into post-creation flow
4. Test all 4 character choice buttons

**MEDIUM PRIORITY ENHANCEMENTS**:
- Visual styling to match V2 theme
- Loading states during API calls
- Error handling for API failures

### ROOT CAUSE RESOLUTION
**Primary Issue**: Missing API integration step
**Solution**: Add campaign retrieval between creation and interaction
**Validation**: Compare API call sequence with working V1 implementation