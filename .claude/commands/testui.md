# Browser Tests (Mock) Command

**Purpose**: Run REAL browser tests with mock APIs (free)

**Action**: Execute browser automation tests using Playwright with mocked API responses

**Usage**: `/testui`

**Action**: Run the UI test script with mock APIs and ALWAYS report the 3 critical confirmations:

```bash
./run_ui_tests.sh mock
```

**MANDATORY CONFIRMATIONS TO REPORT**:
After test execution, ALWAYS explicitly confirm these 3 points:

1. **📸 BROWSER TEST EVIDENCE**: 
   - List actual screenshot file paths from `/tmp/worldarchitectai/browser/`
   - Confirm real Playwright browser automation worked
   - Show count of PNG files generated

2. **🔥 FIREBASE CONNECTION STATUS**:
   - Confirm mock Firebase was used (not real Firebase)
   - Verify no real Firestore API calls were made
   - Report mock mode was active

3. **🤖 GEMINI API STATUS**:
   - Confirm mock Gemini responses were used (not real API calls)
   - Verify no real Gemini API charges occurred
   - Report mock AI mode was active

**CRITICAL REQUIREMENTS**:
- 🚨 **REAL browser automation only** - Must use Playwright
- 🚨 **NO HTTP simulation** - This is browser testing, not API testing  
- 🚨 **Mock APIs** - Uses mocked external API responses (free)
- 🚨 **Real screenshots** - PNG/JPG images taken by browsers, never text files
- ❌ **NEVER simulate** - If browser tests can't run, report honestly
- ✅ **ALWAYS list screenshot paths** - Show exact file locations generated