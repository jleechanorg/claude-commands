# Browser Tests (FULL) Command

**Purpose**: Run REAL browser tests with REAL APIs (costs money!)

**Action**: Execute browser automation tests using Playwright with real API calls

**Usage**: `/testuif`

**Action**: Run the UI test script with real APIs and ALWAYS report the 3 critical confirmations:

```bash
./run_ui_tests.sh
```

**MANDATORY CONFIRMATIONS TO REPORT**:
After test execution, ALWAYS explicitly confirm these 3 points:

1. **📸 BROWSER TEST EVIDENCE**: 
   - List actual screenshot file paths from `/tmp/worldarchitectai/browser/`
   - Confirm real Playwright browser automation worked
   - Show count of PNG files generated

2. **🔥 FIREBASE CONNECTION STATUS**:
   - Confirm REAL Firebase/Firestore was used (not mocked)
   - Verify actual Firestore API calls were made
   - Report production Firebase mode was active

3. **🤖 GEMINI API STATUS**:
   - Confirm REAL Gemini API calls were made (costs money!)
   - Verify actual AI responses were generated
   - Report production Gemini mode was active

**CRITICAL REQUIREMENTS**:
- 🚨 **REAL browser automation only** - Must use Playwright
- 🚨 **NO HTTP simulation** - This is browser testing, not API testing
- 🚨 **REAL APIs** - Makes actual external API calls (costs money!)
- 🚨 **Real screenshots** - PNG/JPG images taken by browsers, never text files
- ❌ **NEVER simulate** - If browser tests can't run, report honestly
- ✅ **ALWAYS list screenshot paths** - Show exact file locations generated
- ⚠️ **COST WARNING** - Uses real API calls that incur charges