# Manual Test Procedure: Campaign Workflow End-to-End

🚨 **NOT AN AUTOMATED TEST**: This is a manual testing procedure requiring human browser interaction. Despite the filename suggesting "generated test", this contains no executable automated testing code.

## 🎯 PRIMARY PROBLEM
Validate complete user journey from landing page through campaign creation to active gameplay, ensuring React V2 integration with Flask backend works seamlessly and persists user data throughout entire workflow.

## 📋 SUCCESS CRITERIA
- **Primary**: User can complete full journey (landing → auth → campaign creation → gameplay) with data persistence
- **Secondary**: Smooth transitions, proper error handling, and optimal performance throughout workflow

## 🚨 CRITICAL FAILURE CONDITIONS
- [ ] User cannot complete authentication to campaigns transition
- [ ] Custom campaign data (character names, settings) not persisted from creation to gameplay
- [ ] React V2 components fail to integrate with Flask backend APIs
- [ ] Landing page doesn't show dynamic content based on user state
- [ ] Campaign creation process loses user input data

## 🔐 READY-TO-EXECUTE SETUP

🚨 **CRITICAL: REAL MODE TESTING ONLY**
- **NO MOCK MODE**: This test requires real API integration testing
- **NO TEST MODE**: Use actual authentication and backend APIs
- **REAL AUTHENTICATION**: Google OAuth with actual test credentials
- **REAL BACKEND**: Flask server must be running on localhost:5005
- **REAL FRONTEND**: React V2 on localhost:3002 (NOT 3003 or test modes)

🚨 **ABSOLUTE MOCK MODE PROHIBITION - ZERO TOLERANCE**:
- ❌ **FORBIDDEN: ANY click on "Dev Tools" button**
- ❌ **FORBIDDEN: ANY "Enable Mock Mode" or similar options**
- ❌ **FORBIDDEN: ANY test-user-basic, mock users, or simulated authentication**
- ❌ **FORBIDDEN: ANY "🎭 Mock mode enabled" messages**
- ⛔ **IMMEDIATE STOP RULE**: If ANY mock mode is detected → ABORT TEST → START OVER
- ✅ **MANDATORY**: Real Google OAuth popup with actual login credentials only

**MOCK MODE = TEST FAILURE**: Using mock mode makes this test meaningless and invalid

**Health Checks**:
```bash
# Backend health check
curl -f http://localhost:5005/ && echo "✅ Backend ready"
# Frontend health check
curl -f http://localhost:3002/ && echo "✅ Frontend ready"
# Monitor logs: tail -f /tmp/worldarchitect.ai/$(git branch --show-current)/flask-server.log
```

**Test Data**:
```json
{
  "campaign_title": "Campaign_Workflow_E2E - $(date +%Y%m%d_%H%M)",
  "character_name": "Zara the Mystic Warrior",
  "campaign_setting": "Mystical Realm of Aethermoor",
  "character_background": "A warrior-mage seeking the Lost Crystal of Eternity",
  "test_identifier": "ZARA_MYSTIC_$(date +%H%M)"
}
```

**Console Monitoring**:
```javascript
// Execute in browser console before testing
window.testErrorLog = [];
window.originalConsoleError = console.error;
console.error = function(...args) {
    window.testErrorLog.push({type: 'error', timestamp: new Date().toISOString(), message: args.join(' ')});
    window.originalConsoleError.apply(console, args);
};
```

## 🔴 RED PHASE EXECUTION

### Step 1: Landing Page State Detection
**Navigate**: http://localhost:3002/
**Expected**: Landing page makes API call to check user campaigns and shows appropriate content
**Evidence**: Screenshot → `docs/campaign-workflow-step1-landing.png`
**API Check**: Monitor for GET /api/campaigns or similar endpoint
**Console Check**: No errors matching: `['TypeError', 'undefined', 'failed to fetch', '401', '500']`

**🔴 VALIDATION CHECKPOINT 1**:
- [ ] Screenshot captured and saved
- [ ] API calls logged (present/absent as expected)
- [ ] Console errors checked and logged
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 2: Authentication Flow Initiation
**Action**: Click "Sign In" or login button on landing page
**Expected**: Google OAuth popup appears, NOT mock authentication screen
**Evidence**: Screenshot → `docs/campaign-workflow-step2-auth-popup.png`
**Data Validation**: Verify real Google OAuth popup (not mock login)
**Backend Logs**: Check Flask logs for OAuth initialization

**🔴 VALIDATION CHECKPOINT 2**:
- [ ] Real OAuth popup displayed (not mock mode)
- [ ] Flask logs show OAuth flow start
- [ ] No mock mode indicators visible
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 3: Authentication Completion
**Action**: Complete Google OAuth authentication with real credentials
**Expected**: User successfully authenticated and redirected to campaigns page
**Evidence**: Screenshot → `docs/campaign-workflow-step3-auth-complete.png`
**Data Validation**: User profile data loaded, session established
**Backend Logs**: Check for successful authentication and session creation

**🔴 VALIDATION CHECKPOINT 3**:
- [ ] Authentication successful with real credentials
- [ ] User redirected to appropriate post-auth page
- [ ] Session established (user info visible)
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 4: Campaigns Dashboard Load
**Navigate**: Post-authentication redirect (likely campaigns page)
**Expected**: User's existing campaigns loaded (if any) or "Create Campaign" option displayed
**Evidence**: Screenshot → `docs/campaign-workflow-step4-campaigns-page.png`
**API Check**: Monitor for campaigns API calls after authentication
**Console Check**: Verify React V2 components load without errors

**🔴 VALIDATION CHECKPOINT 4**:
- [ ] Campaigns page loads successfully
- [ ] Dynamic content based on user state
- [ ] React V2 components render properly
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 5: Campaign Creation Initiation
**Action**: Click "Create New Campaign" or similar button
**Expected**: Campaign creation wizard/form opens with V2 React components
**Evidence**: Screenshot → `docs/campaign-workflow-step5-create-start.png`
**Data Validation**: Form fields load properly, no hardcoded placeholder values
**Backend Logs**: Check for campaign creation flow initialization

**🔴 VALIDATION CHECKPOINT 5**:
- [ ] Campaign creation interface loads
- [ ] Form fields are interactive and empty (ready for input)
- [ ] React V2 components render correctly
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 6: Campaign Title and Setting Input
**Action**: Input campaign title: "Campaign_Workflow_E2E - [timestamp]" and setting: "Mystical Realm of Aethermoor"
**Expected**: Form accepts input, shows live updates, no validation errors
**Evidence**: Screenshot → `docs/campaign-workflow-step6-campaign-details.png`
**Data Validation**: Verify input text appears correctly in form fields
**Backend Logs**: Monitor for any real-time API calls or validation

**🔴 VALIDATION CHECKPOINT 6**:
- [ ] Campaign details entered successfully
- [ ] Form shows user input (not placeholders)
- [ ] No validation errors or JavaScript errors
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 7: Character Creation - Basic Details
**Action**: Navigate to character creation section, enter "Zara the Mystic Warrior" as character name
**Expected**: Character creation form accepts input, updates preview if available
**Evidence**: Screenshot → `docs/campaign-workflow-step7-character-name.png`
**Data Validation**: Verify "Zara the Mystic Warrior" appears in character name field
**Backend Logs**: Check for character data handling

**🔴 VALIDATION CHECKPOINT 7**:
- [ ] Character name entered successfully
- [ ] Test character name visible in form
- [ ] Character creation flow progresses normally
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 8: Character Background and Details
**Action**: Enter character background: "A warrior-mage seeking the Lost Crystal of Eternity"
**Expected**: Background text accepted, form validation passes
**Evidence**: Screenshot → `docs/campaign-workflow-step8-character-background.png`
**Data Validation**: Verify background text appears in form field
**Backend Logs**: Monitor for character data processing

**🔴 VALIDATION CHECKPOINT 8**:
- [ ] Character background entered successfully
- [ ] All character details preserved in form
- [ ] Form validation working properly
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 9: Campaign Settings and Configuration
**Action**: Configure additional campaign settings (game rules, difficulty, etc.)
**Expected**: Settings form works properly, saves user preferences
**Evidence**: Screenshot → `docs/campaign-workflow-step9-campaign-settings.png`
**Data Validation**: Verify selected settings are reflected in UI
**Backend Logs**: Check for settings persistence API calls

**🔴 VALIDATION CHECKPOINT 9**:
- [ ] Campaign settings configured successfully
- [ ] User preferences saved and reflected
- [ ] No errors in settings form
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 10: Campaign Creation Submission
**Action**: Submit/create the campaign with all entered data
**Expected**: Campaign creation API call succeeds, user redirected to new campaign
**Evidence**: Screenshot → `docs/campaign-workflow-step10-campaign-submit.png`
**API Check**: Monitor POST request to campaign creation endpoint
**Backend Logs**: Verify successful campaign creation in Flask logs

**🔴 VALIDATION CHECKPOINT 10**:
- [ ] Campaign submission successful
- [ ] API call completed without errors
- [ ] User redirected appropriately
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 11: Campaign Dashboard/Overview
**Navigate**: Post-creation redirect (campaign dashboard or overview)
**Expected**: New campaign appears with user-entered data (title, setting, character name)
**Evidence**: Screenshot → `docs/campaign-workflow-step11-campaign-overview.png`
**Data Validation**: Verify "Zara the Mystic Warrior" and other test data appears
**Backend Logs**: Check for campaign data retrieval API calls

**🔴 VALIDATION CHECKPOINT 11**:
- [ ] Campaign overview displays correctly
- [ ] User-entered data visible (not placeholders)
- [ ] Campaign title and character name match input
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 12: Game Session Initiation
**Action**: Start or launch the campaign for gameplay
**Expected**: Game interface loads with campaign data intact
**Evidence**: Screenshot → `docs/campaign-workflow-step12-game-start.png`
**Data Validation**: Verify campaign setting "Mystical Realm of Aethermoor" appears in game
**Backend Logs**: Monitor for game session initialization APIs

**🔴 VALIDATION CHECKPOINT 12**:
- [ ] Game session starts successfully
- [ ] Campaign data carried over to game interface
- [ ] Character "Zara the Mystic Warrior" appears in game
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 13: In-Game Character Display
**Action**: Navigate to character sheet or character display in game
**Expected**: Character details match creation input exactly
**Evidence**: Screenshot → `docs/campaign-workflow-step13-character-ingame.png`
**Data Validation**: Verify "Zara the Mystic Warrior" and background text appear
**Backend Logs**: Check for character data retrieval in game context

**🔴 VALIDATION CHECKPOINT 13**:
- [ ] Character data displays correctly in game
- [ ] All entered character details preserved
- [ ] Background text intact and readable
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 14: Game World Display
**Action**: Navigate to or view game world/setting information
**Expected**: Campaign setting "Mystical Realm of Aethermoor" displayed appropriately
**Evidence**: Screenshot → `docs/campaign-workflow-step14-world-display.png`
**Data Validation**: Verify custom setting appears, not default/hardcoded world
**Backend Logs**: Monitor for world/setting data API calls

**🔴 VALIDATION CHECKPOINT 14**:
- [ ] Game world displays custom setting
- [ ] Setting matches user input from creation
- [ ] No default/placeholder world displayed
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 15: Data Persistence Verification
**Action**: Refresh page or navigate away and back to verify data persistence
**Expected**: All user data remains intact after page refresh
**Evidence**: Screenshot → `docs/campaign-workflow-step15-persistence-check.png`
**Data Validation**: Verify "Zara the Mystic Warrior" still appears after refresh
**Backend Logs**: Check for session/data persistence handling

**🔴 VALIDATION CHECKPOINT 15**:
- [ ] Data persists across page refreshes
- [ ] User session maintained properly
- [ ] All custom data intact after navigation
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 16: End-to-End Data Flow Verification
**Action**: Trace complete data flow from input to final display
**Expected**: User input → API → Database → Retrieval → UI Display chain works perfectly
**Evidence**: Screenshot → `docs/campaign-workflow-step16-data-flow-complete.png`
**Data Validation**: Final verification that "ZARA_MYSTIC_[timestamp]" identifier is trackable
**Backend Logs**: Complete audit trail of data handling

**🔴 VALIDATION CHECKPOINT 16**:
- [ ] Complete data flow verified end-to-end
- [ ] Test identifier trackable throughout system
- [ ] No data loss or corruption detected
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

## 📊 RESULTS DOCUMENTATION (Fill During Execution)

### 🚨 CRITICAL Issues Found (Update After Testing)
**Issue 1**: [Description]
- **Evidence**: [Screenshot/log reference]
- **Impact**: [How this blocks core functionality]
- **Action**: [Immediate fix required]

**Issue 2**: [Description]
- **Evidence**: [Screenshot/log reference]
- **Impact**: [How this blocks core functionality]
- **Action**: [Immediate fix required]

### ⚠️ HIGH Priority Issues (Update After Testing)
**Issue 1**: [Description]
- **Evidence**: [Screenshot/log reference]
- **Impact**: [User experience degradation]
- **Timeline**: [When to fix]

### 📝 MEDIUM Priority Issues (Update After Testing)
**Issue 1**: [Description]
- **Evidence**: [Screenshot/log reference]
- **Impact**: [Minor UX issues]
- **Backlog**: [Future improvement]

### ✅ Working Correctly (Update After Testing)
**Functionality**: [What works as expected]
- **Evidence**: [Screenshot/log reference]
- **Console**: [Clean or acceptable warnings]

**Data Flow**: [Successful data persistence]
- **Evidence**: [Screenshots showing data throughout flow]
- **Verification**: [Test identifier tracking successful]

### 🎯 KEY LEARNINGS (Update After Testing)
**Expected vs Reality**:
- **Expected**: [Original assumptions about workflow]
- **Reality**: [What was actually found during testing]
- **Learning**: [Insights for future development and testing]

**React V2 Integration**:
- **Expected**: [Assumptions about React V2 + Flask integration]
- **Reality**: [Actual integration behavior observed]
- **Learning**: [Technical insights about the integration]

**Data Persistence Patterns**:
- **Expected**: [Assumptions about data flow]
- **Reality**: [Actual data handling behavior]
- **Learning**: [Insights about system architecture]

## 🚀 GREEN PHASE IMPLEMENTATION (Update With Fix Code)

### Critical Issue Fixes
```typescript
// Implementation code will go here after issues identified
// Example: Authentication flow fixes
```

```python
# Backend API fixes if needed
# Example: Campaign creation endpoint improvements
```

### Integration Improvements
```typescript
// React V2 component improvements
// Example: Better error handling for API calls
```

```python
# Flask backend improvements
# Example: Better session management
```

## 🔄 MATRIX TESTING RESULTS

| Feature Test | Expected Behavior | Actual Behavior | Status | Evidence |
|--------------|------------------|-----------------|---------|----------|
| Landing Page API Call | Calls campaigns API on load | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |
| Google OAuth Integration | Real OAuth popup appears | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |
| Campaign Creation Form | Accepts and validates user input | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |
| Character Name Persistence | "Zara the Mystic Warrior" appears throughout | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |
| Campaign Setting Display | "Mystical Realm of Aethermoor" in game | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |
| Data Flow End-to-End | Input → API → DB → UI chain works | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |
| Session Persistence | Data survives page refresh | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |
| React V2 Integration | Components load and function properly | [Fill after testing] | [🚨/⚠️/✅] | [screenshot.png] |

## 🚨 TEST EXECUTION FAILURE PROTOCOL
**If ANY validation checkpoint fails:**
1. **IMMEDIATELY STOP** the test execution
2. **REPORT DEVIATION** with exact details and screenshots
3. **DO NOT CONTINUE** without explicit approval
4. **PRIORITY ASSESSMENT**: Real user impact overrides expectations
5. **IMPLEMENT FIXES**: Address CRITICAL issues before resuming

## ✅ COMPLETION CRITERIA
- [ ] All 16 validation checkpoints completed successfully
- [ ] All CRITICAL issues resolved with evidence
- [ ] HIGH issues documented with timeline and owner
- [ ] Test data "Zara the Mystic Warrior" appears correctly throughout entire flow
- [ ] Clean console (zero critical errors matching patterns)
- [ ] Results documentation section completed with insights
- [ ] Matrix testing table filled with actual results and evidence
- [ ] Learning section completed with expectation vs reality analysis

## 🔍 CONSOLE ERROR PATTERNS TO MONITOR
**Critical Errors** (Require immediate fix):
- `TypeError: Cannot read property`
- `ReferenceError: [variable] is not defined`
- `Failed to fetch` (API call failures)
- `401 Unauthorized` (Authentication failures)
- `500 Internal Server Error` (Backend failures)
- `CORS policy` errors

**Acceptable Warnings** (Document but don't stop):
- Development mode warnings
- Performance suggestions
- Non-critical third-party library warnings

## 🎯 VISUAL CONTENT VALIDATION REQUIREMENTS
**Data Tracking Success Criteria**:
- [ ] "Campaign_Workflow_E2E - [timestamp]" appears in campaign list/overview
- [ ] "Zara the Mystic Warrior" visible in character displays
- [ ] "Mystical Realm of Aethermoor" shown in world/setting displays
- [ ] "A warrior-mage seeking the Lost Crystal of Eternity" appears in character background
- [ ] Test identifier "ZARA_MYSTIC_[timestamp]" trackable in logs/data

**Anti-Pattern Detection**:
- [ ] No hardcoded character names like "Shadowheart" or "Astarion"
- [ ] No default world names when custom setting provided
- [ ] No placeholder text in place of user input
- [ ] No mock mode indicators or test user displays

This comprehensive test covers the complete user journey while focusing on data persistence, React V2 integration, and real authentication flows - the core components of Milestone 2 success.
