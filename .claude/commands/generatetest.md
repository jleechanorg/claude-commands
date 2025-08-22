# /generatetest - Intelligent Test Protocol Generator

**Purpose**: Generate execution-ready test protocols for both MCP and browser testing with automatic detection

**Usage**: `/generatetest [test_name] [target_component] [expected_behavior]`

## 🔍 INTELLIGENT TEST TYPE DETECTION

**Automatic Detection Logic:**
- **MCP Tests**: Detects MCP-related keywords → `mcp`, `worldarchitect`, `campaign`, `create_campaign`, `get_campaigns`, `process_action`, `firebase`, `gemini`, `api integration`, `server integration`
- **Browser Tests**: Detects UI/frontend keywords → `browser`, `ui`, `frontend`, `page`, `click`, `navigation`, `form`, `login`, `oauth`, `responsive`, `visual`
- **Hybrid Tests**: Detects both patterns → Asks user for clarification

**Keywords for MCP Test Generation:**
```
mcp, worldarchitect, campaign, create_campaign, get_campaigns_list, process_action, 
get_campaign_state, firebase, firestore, gemini, api integration, server integration,
real services, production mode, mcp tools, mcp server
```

**Keywords for Browser Test Generation:**
```
browser, ui, frontend, page, click, navigation, form, login, oauth, responsive, 
visual, playwright, screenshot, element, button, input, landing page, user interface
```

**Decision Matrix:**
- **IF** input contains MCP keywords → Generate MCP integration test
- **IF** input contains browser keywords → Generate browser automation test  
- **IF** input contains both → Ask user: "Detected both MCP and browser elements. Generate: (1) MCP integration test, (2) Browser automation test, or (3) Hybrid test?"
- **IF** unclear → Ask user: "Generate: (1) MCP integration test or (2) Browser automation test?"

**Default Behavior** (Focused & Execution-Ready):
1. **Problem-First Design**: Start with specific user problem to solve
2. **Execution Commands**: Include ready-to-run commands and URLs
3. **Priority Matrix**: Rank findings by actual user impact
4. **Validation Checkpoints**: Numbered steps with mandatory stop conditions
5. **Results Integration**: Template sections for actual findings
6. **Learning Capture**: Document expectations vs reality

## Test Generation Protocol

### 1. Problem Definition
- **What specific issue is being tested?**
- **What is the user impact if this issue exists?**
- **What would "working correctly" look like?**
- **CRITICAL ADDITION**: What service integration boundaries need validation?
- **CRITICAL ADDITION**: What user journey layers could fail independently?

### 2. Success Criteria Definition
- **Primary Goal**: Main problem that must be solved
- **Secondary Goals**: Nice-to-have improvements
- **Failure Conditions**: What constitutes a test failure requiring immediate action

### 3. Priority Matrix Setup
```
🚨 CRITICAL: Blocks core user functionality
⚠️ HIGH: Significant user experience degradation
📝 MEDIUM: Minor UX issues or cosmetic problems
ℹ️ LOW: Documentation or edge case issues
```

### 4. Evidence Collection Requirements
- **Screenshots**: Specific pages/states to capture
- **API Logs**: Which endpoints to monitor
- **Network Traffic**: Expected vs actual requests
- **Console Logs**: Error messages to watch for

## 🚨 MANDATORY STOP CONDITIONS PROTOCOL
**STOP testing immediately and implement fixes if:**
- Any 🚨 CRITICAL condition found that blocks core user functionality
- Data loss or corruption risk detected
- User cannot complete primary workflow
- System completely breaks or becomes unusable
- **CRITICAL ADDITION**: Hardcoded content appears instead of user data (service integration failure)
- **CRITICAL ADDITION**: User sees placeholder/demo content in final experience
- **CRITICAL ADDITION**: Any service layer fails to receive user context

**Protocol**: Test Discovery → Priority Assessment → IMMEDIATE FIX (if critical) → Verify Fix → Resume Testing

**Critical Rule**: Never continue testing with unresolved CRITICAL issues

## 🚨 PRIORITY-BASED ACTION PROTOCOL
**For each finding, apply immediate action:**
- 🚨 CRITICAL → STOP testing, implement fix, verify, then resume
- ⚠️ HIGH → Document thoroughly, add to immediate sprint backlog
- 📝 MEDIUM → Note for future improvement, continue testing
- ℹ️ LOW → Brief documentation, no action blocking

**Action Decision Matrix:**
```
IF finding is 🚨 CRITICAL → HALT workflow, fix immediately, verify, resume
IF finding is ⚠️ HIGH → Document with timeline, continue testing
IF finding is 📝 MEDIUM → Log for backlog, continue testing
IF finding is ℹ️ LOW → Note briefly, continue testing
```

## 🔄 EXPECTATION VS REALITY PROTOCOL
**When test findings don't match expectations:**
1. **Assess actual user impact** (not expectation accuracy)
2. **Re-classify findings** by real-world priority using 🚨/⚠️/📝 system
3. **If 🚨 CRITICAL issues found** → Focus on those immediately
4. **Update test expectations** for future runs after fixes
5. **NEVER dismiss real user problems** because they weren't expected

**Critical Rule**: Real user problems = Priority, regardless of test assumptions
**Example**: Landing page not checking campaigns = API integration failure (not "minor UX")

## 📝 EVIDENCE DOCUMENTATION PROTOCOL
**For each test step, MANDATORY collection:**
- **Screenshots**: Saved to `docs/[test-name]-[step]-[priority].png`
- **Network logs**: Specific API calls with status codes and timing
- **Console logs**: Error messages, warnings, and API success logs
- **Priority assessment**: Applied using 🚨/⚠️/📝 criteria for each finding
- **Action taken**: Document what was done for CRITICAL issues

**Evidence naming convention:** `docs/[test-name]-[finding-priority]-[description].png`
**Log format**: Include timestamps, request/response details, error traces

## ✅ TEST COMPLETION VALIDATION PROTOCOL
**Test is NOT complete until:**
- [ ] All 🚨 CRITICAL issues resolved and verified with evidence
- [ ] All ⚠️ HIGH issues documented with fix timeline and owner
- [ ] Evidence collected and properly named for all findings
- [ ] Next actions clearly defined with priorities and assignments
- [ ] Verification screenshots showing fixes work end-to-end

**No test can be marked "complete" with unresolved CRITICAL issues**

## 🔍 CONSOLE ERROR MONITORING PROTOCOL
**Automated error detection for each test step:**
- **Setup console monitoring**: Capture errors/warnings with timestamps
- **Define test-specific error patterns**: Authentication, API, navigation, etc.
- **Critical error patterns**: `TypeError`, `undefined`, `failed to fetch`, `401`, `500`, `CORS`
- **Validation function**: Check for test-specific critical errors vs acceptable warnings
- **Clean console requirement**: Zero critical errors, minimal non-critical warnings

**Implementation**:
```javascript
// Auto-generated console monitoring setup
window.testErrorLog = [];
const __origConsoleError = console.error.bind(console);
console.error = function(...args) {
    window.testErrorLog.push({
        type: 'error',
        timestamp: new Date().toISOString(),
        message: args.map(String).join(' ')
    });
    __origConsoleError(...args);
};

// Test-specific error validation
const criticalErrorPatterns = ['TypeError', 'undefined', 'failed to fetch', '401', '500'];
const hasCriticalErrors = window.testErrorLog.filter(e =>
    criticalErrorPatterns.some(pattern => e.message.includes(pattern))
).length > 0;
```

## 🎯 VISUAL CONTENT VALIDATION PROTOCOL
**End-to-end data flow verification:**
- **Test Data Tracking**: Use specific, unique test data (e.g., "Zara the Mystic" not generic "Character")
- **Data Flow Validation**: Input → API → Database → Retrieval → UI Display → **SERVICE INTEGRATION**
- **Visual Verification**: Screenshot actual displayed content to verify data persistence
- **Hardcoded Content Detection**: Ensure user input appears in UI, not placeholder values
- **CRITICAL ADDITION**: **Service Layer Validation**: AI/content generation must use user data, not defaults
- **CRITICAL ADDITION**: **Multi-Layer Testing**: Verify each integration boundary independently
- **Critical Rule**: If test data doesn't appear in final UI OR service output, it's a 🚨 CRITICAL data flow failure

**Test Data Pattern**:
```json
{
  "campaign_title": "[Test Name] - [Unique Identifier]",
  "character_name": "[Unique Name] the [Descriptor]",
  "setting": "[Unique World] where [distinctive feature]",
  "description": "A realm where [unique characteristic]"
}
```

## 🔄 MATRIX TESTING PROTOCOL
**Comparative testing between expected vs actual behavior:**
- **Feature Matrix**: Create comparison table with Expected vs Actual columns
- **Status Tracking**: 🔴 FAIL / ⚠️ PARTIAL / ✅ PASS for each feature
- **Evidence Column**: Screenshot references for each comparison
- **Regression Detection**: Compare with previous implementations (V1 vs V2)
- **Milestone Organization**: Group related features by implementation milestone

**Matrix Template**:
```markdown
| Feature Test | Expected Behavior | Actual Behavior | Status | Evidence |
|--------------|------------------|-----------------|---------|----------|
| [Feature] | [What should happen] | [What happens] | [🚨/⚠️/✅] | [screenshot.png] |
```

## 🔐 AUTHENTICATION INTEGRATION PROTOCOL
**Real authentication testing requirements:**
- **Credential Management**: Use secure credential loading (not hardcoded)
- **Environment Setup**: Verify both frontend and backend server health
- **OAuth Flow Testing**: Handle popup windows and real authentication
- **Session Persistence**: Verify authentication state across page loads
- **Error Handling**: Test authentication failures gracefully

**Pre-test Health Checks**:
```bash
# Backend health check
curl -f http://localhost:5005/ >/dev/null 2>&1 && echo "✅ Backend ready" || echo "❌ Backend unavailable"
# Frontend health check
curl -f http://localhost:3002/ >/dev/null 2>&1 && echo "✅ Frontend ready" || echo "❌ Frontend unavailable"
```

## 📊 MILESTONE-BASED TEST ORGANIZATION
**Structured test progression:**
- **Milestone Grouping**: Organize tests by implementation phases
- **Dependency Management**: Ensure prerequisite milestones pass before advanced testing
- **Progressive Enhancement**: Test basic functionality before complex features
- **Historical Context**: Document what problems each test was created to solve

## 🎮 MCP INTEGRATION TEST TEMPLATE

**Generated when MCP keywords detected:**

# MCP Integration Test: [TEST_NAME]

## Test Overview
This test validates [specific MCP functionality] using real WorldArchitect MCP server integration with Firebase and Gemini services.

## Test Configuration
- **Test Type**: MCP Integration Test
- **User ID**: `test-[test-name]-user@example.com`
- **Expected Duration**: [estimated time]
- **Dependencies**: MCP server running in production mode (`PRODUCTION_MODE=true`)

## Test Steps

### Phase 1: [Primary Test Objective]
**Objective**: [What this phase validates]
- **Action**: Call `mcp__worldarchitect__[relevant_mcp_tool]`
  - `user_id`: `test-[test-name]-user@example.com`
  - [additional parameters based on test]
- **Expected Results**:
  - [Specific outcome 1]
  - [Specific outcome 2]
  - [Data validation requirements]

### Phase 2: [Secondary Validation]
**Objective**: [Follow-up validation]
- **Action**: [Subsequent MCP tool call]
- **Expected Results**:
  - [Expected behavior]
  - [State persistence validation]

## Success Criteria
- ✅ [Primary success condition]
- ✅ All responses contain real AI-generated content (no mocks)
- ✅ [Data persistence requirement]
- ✅ No error responses or timeout issues

## Failure Indicators
- ❌ Mock data detected in any response
- ❌ [Specific failure condition]
- ❌ MCP server connection failures
- ❌ Firebase or Gemini API errors

## Test Execution Notes
- Run with MCP server in production mode (`PRODUCTION_MODE=true`)
- Monitor server logs for error messages during execution
- Verify all timestamps are realistic and progressive
- Check that Firebase documents are actually created
- Confirm Gemini API responses are genuine (not cached/mocked)

## 🌐 BROWSER AUTOMATION TEST TEMPLATE

**Generated when browser keywords detected:**

# Test: [TEST_NAME]

## 🎯 PRIMARY PROBLEM
[What specific user problem are we testing for?]

## 📋 SUCCESS CRITERIA
- **Primary**: [Main thing that must work]
- **Secondary**: [Nice-to-have improvements]

## 🚨 CRITICAL FAILURE CONDITIONS
- [ ] [Condition that requires immediate fix]
- [ ] [Another critical condition]

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
curl -f http://localhost:5005/ >/dev/null 2>&1 && echo "✅ Backend ready" || echo "❌ Backend unavailable"
# Frontend health check
curl -f http://localhost:3002/ >/dev/null 2>&1 && echo "✅ Frontend ready" || echo "❌ Frontend unavailable"
# Monitor logs: tail -f /tmp/worldarchitect.ai/$(git branch --show-current)/flask-server.log
```

**Test Data**:
```json
{
  "campaign_title": "[TEST_NAME] - $(date +%Y%m%d_%H%M)",
  "character_name": "[Unique Name] the [Descriptor]",
  "test_identifier": "[Unique value to track in UI]"
}
```

**Console Monitoring**:
```javascript
// Execute in browser console before testing
window.testErrorLog = [];
console.error = function(...args) {
    window.testErrorLog.push({type: 'error', timestamp: new Date().toISOString(), message: args.join(' ')});
};
```

## 🔴 RED PHASE EXECUTION

### Step 1: [Specific Action]
**Navigate**: http://localhost:3002/[specific-path]
**Expected**: [What should happen]
**Evidence**: Screenshot → `docs/[test-name]-step1-[status].png`
**API Check**: Monitor for [specific API calls]
**Console Check**: No errors matching: `['TypeError', 'undefined', 'failed to fetch', '401', '500']`

**🔴 VALIDATION CHECKPOINT 1**:
- [ ] Screenshot captured and saved
- [ ] API calls logged (present/absent as expected)
- [ ] Console errors checked and logged
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 2: [Specific Action]
**Action**: [Specific user action to perform]
**Expected**: [What should happen]
**Evidence**: Screenshot → `docs/[test-name]-step2-[status].png`
**Data Validation**: Verify "[test_identifier]" appears in UI
**Backend Logs**: Check Flask logs for [expected activity]

**🔴 VALIDATION CHECKPOINT 2**:
- [ ] Action completed successfully
- [ ] Test data visible in UI (no hardcoded values)
- [ ] Backend logs show expected activity
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: If CRITICAL found, STOP and implement fixes before proceeding

### Step 2.5: Service Integration Validation - **CRITICAL LAYER**
**Action**: Verify service layers receive and use user data correctly
**Expected**: AI/content generation services incorporate user's specific data
**Evidence**: Screenshot of service output (content, emails, AI responses)
**Service Validation**: Check that generated content references user data, not placeholders
**Integration Logs**: Monitor service API calls and data payloads

**🔴 VALIDATION CHECKPOINT 2.5**:
- [ ] Service output incorporates user test data
- [ ] No hardcoded/placeholder content in service responses
- [ ] Service APIs receive user context correctly
- [ ] Priority assessment: 🚨 CRITICAL / ⚠️ HIGH / 📝 MEDIUM
**🚨 MANDATORY**: Service integration failures are CRITICAL - STOP and fix immediately

## 📊 RESULTS DOCUMENTATION (Fill During Execution)

### 🚨 CRITICAL Issues Found (Update After Testing)
**Issue 1**: [Description]
- **Evidence**: [Screenshot/log reference]
- **Impact**: [How this blocks core functionality]
- **Action**: [Immediate fix required]

### ✅ Working Correctly (Update After Testing)
**Functionality**: [What works as expected]
- **Evidence**: [Screenshot/log reference]
- **Console**: [Clean or acceptable warnings]

### 🎯 KEY LEARNINGS (Update After Testing)
**Expected vs Reality**:
- **Expected**: [Original assumptions]
- **Reality**: [What was actually found]
- **Learning**: [Insights for future tests]

## 🚀 GREEN PHASE IMPLEMENTATION (Update With Fix Code)
```typescript
// Implementation code will go here after issues identified
```

## 🚨 TEST EXECUTION FAILURE PROTOCOL
**If ANY validation checkpoint fails:**
1. **IMMEDIATELY STOP** the test execution
2. **REPORT DEVIATION** with exact details
3. **DO NOT CONTINUE** without explicit approval
4. **PRIORITY ASSESSMENT**: Real user impact overrides expectations

## ✅ COMPLETION CRITERIA
- [ ] All CRITICAL issues resolved with evidence
- [ ] HIGH issues documented with timeline
- [ ] Test data appears correctly in final UI
- [ ] Clean console (zero critical errors)
- [ ] Learning section completed with insights

## Implementation Examples

### Example: Landing Page API Integration Test

**🎯 PRIMARY PROBLEM**: Landing page may not check user's existing campaigns

**📋 SUCCESS CRITERIA**:
- [x] Primary: Landing page shows different content based on user's campaign state
- [x] Secondary: Page loads quickly with good UX

**🚨 CRITICAL FAILURE CONDITIONS**:
- [ ] Landing page always shows same content regardless of user state
- [ ] No API calls made to check user campaigns
- [ ] User cannot access their existing campaigns

**⚠️ HIGH PRIORITY CONDITIONS**:
- [ ] Slow API response times (>2s)
- [ ] API errors not handled gracefully
- [ ] Confusing navigation flow

**📝 EVIDENCE COLLECTION**:
- [ ] Screenshot: landing_page_with_campaigns.png
- [ ] Screenshot: landing_page_no_campaigns.png
- [ ] API Logs: Monitor GET /api/campaigns calls
- [ ] Network: Verify campaigns API is called on page load
- [ ] Console: Check for API errors or warnings

**🔄 TEST EXECUTION**:

#### Step 1: Load Landing Page (User with Campaigns)
**Expected**: Page should check for existing campaigns and show appropriate UI
**Evidence**:
- Screenshot of page content
- Network logs showing API call
- Console logs for any errors
**Priority Assessment**:
- IF no API call made → 🚨 CRITICAL - This is core integration issue
- IF API call fails → ⚠️ HIGH - Error handling problem
- IF slow loading → 📝 MEDIUM - Performance issue

#### Step 2: Load Landing Page (User without Campaigns)
**Expected**: Page should show "Create Your First Campaign"
**Evidence**:
- Screenshot of page content
- Confirmation of appropriate messaging
**Priority Assessment**:
- IF same content shown → 🚨 CRITICAL - Not checking user state
- IF confusing messaging → 📝 MEDIUM - UX improvement

**🚨 MANDATORY STOP CONDITIONS**:
- Landing page doesn't call campaigns API
- Same content shown regardless of user state
- User cannot proceed to create or access campaigns

**📊 RESULTS EVALUATION**:
Based on findings, classify each issue and determine immediate actions needed.

## Command Implementation

When user runs `/generatetest landing_page_integration "Landing Page" "Dynamic content based on user campaigns"`:

1. **Generate Focused Test**: Create execution-ready test in `roadmap/tests/`
2. **Include Project Specifics**: URLs, commands, log paths, auth methods
3. **Set Validation Checkpoints**: Numbered steps with mandatory stops
4. **Create Results Templates**: Sections for actual findings integration
5. **Add Learning Capture**: Template for expectation vs reality analysis
6. **Provide Implementation Guide**: Code snippet placeholders for fixes

## Key Improvements Over Previous Version

**✅ Execution-Ready by Default**:
- Specific commands to run (curl health checks, log monitoring)
- Project URLs and paths (localhost:3002, flask-server.log)
- Ready-to-execute console monitoring setup
- Concrete evidence naming conventions

**✅ Results Integration**:
- Template sections that get filled during execution
- Learning capture for expectation vs reality
- Implementation code placeholders for fixes
- Clear distinction between template and results sections

**✅ Focused Structure**:
- RED/GREEN phase organization like successful original
- Numbered validation checkpoints with mandatory stops
- Concise but comprehensive protocols
- Balance of methodology and actionability

**✅ Priority-First Design**:
- User impact assessment built into every step
- Never dismiss real user problems as "minor"
- CRITICAL issues trigger immediate stop and fix
- Learning from previous testing failures integrated

This creates tests that are both methodologically sound AND immediately executable with real results integration.
