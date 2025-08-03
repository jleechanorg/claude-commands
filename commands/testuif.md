# Browser Tests (FULL) Command

**Purpose**: Run REAL browser tests with REAL APIs using Playwright MCP by default (costs money!)

**Action**: Execute browser automation tests ONLY in testing_ui/core_tests/ with real Firebase + Gemini APIs

**Usage**: `/testuif`

**Default Action in Claude Code CLI**: Run core tests with Playwright MCP for optimal AI-driven automation:

```bash
./run_ui_tests.sh real --playwright
```

**Target Directory**: ONLY `testing_ui/core_tests/` (focused, essential tests)
**API Mode**: REAL Firebase + REAL Gemini (USE_MOCK_FIREBASE=false, USE_MOCK_GEMINI=false)

**Secondary**: For Chrome-specific testing, use Puppeteer MCP:
```bash
./run_ui_tests.sh real --puppeteer
```

**Fallback**: If MCP unavailable, use Playwright:
```bash
./run_ui_tests.sh real
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
- 🚨 **REAL browser automation only** - Must use Puppeteer MCP (preferred) or Playwright
- 🚨 **NO HTTP simulation** - This is browser testing, not API testing
- 🚨 **REAL APIs** - Makes actual external API calls (costs money!)
- 🚨 **Real screenshots** - PNG/JPG images or visual captures, never text files
- ❌ **NEVER simulate** - If browser tests can't run, report honestly
- ✅ **ALWAYS provide visual evidence** - Screenshots through MCP or file paths
- ⚠️ **COST WARNING** - Uses real API calls that incur charges

**PUPPETEER MCP BENEFITS** (Claude Code CLI default):
- ✅ **No dependencies** - Works immediately without setup
- ✅ **Visual capture** - Built-in screenshot functionality
- ✅ **Real browsers** - Actual Chrome/Chromium automation
- ✅ **Direct integration** - Native Claude Code environment support
- ✅ **Real API testing** - Tests actual Gemini and Firebase integration
