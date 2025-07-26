# Browser Tests (Mock) Command

**Purpose**: Run REAL browser tests with mock APIs using Playwright MCP by default

**Action**: Execute browser automation tests using Playwright MCP (preferred) or Puppeteer MCP secondary

**Usage**: `/testui [mode]`

**Default Action in Claude Code CLI**: Run with Playwright MCP for optimal AI-driven automation:

```bash
./run_ui_tests.sh mock --playwright
```

**Secondary**: For Chrome-specific testing, use Puppeteer MCP:
```bash
./run_ui_tests.sh mock --puppeteer
```

**Fallback**: If MCP unavailable, use Playwright:
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
- 🚨 **REAL browser automation only** - Must use Puppeteer MCP (preferred) or Playwright
- 🚨 **NO HTTP simulation** - This is browser testing, not API testing
- 🚨 **Mock APIs** - Uses mocked external API responses (free)
- 🚨 **Real screenshots** - PNG/JPG images or visual captures, never text files
- ❌ **NEVER simulate** - If browser tests can't run, report honestly
- ✅ **ALWAYS provide visual evidence** - Screenshots through MCP or file paths

**PUPPETEER MCP BENEFITS** (Claude Code CLI default):
- ✅ **No dependencies** - Works immediately without setup
- ✅ **Visual capture** - Built-in screenshot functionality
- ✅ **Real browsers** - Actual Chrome/Chromium automation
- ✅ **Direct integration** - Native Claude Code environment support
