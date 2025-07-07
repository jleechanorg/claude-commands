# Browser Tests (Mock) Command

**Purpose**: Run REAL browser tests with mock APIs (free)

**Action**: Execute browser automation tests using Playwright with mocked API responses

**Usage**: `/testui`

**Action**: Simply run the UI test script with mock APIs:

```bash
./run_ui_tests.sh mock
```

- ✅ Script handles all setup automatically (Playwright installation, browser dependencies, server startup)
- ✅ Report actual results/errors
- ❌ NEVER create fake output

**CRITICAL REQUIREMENTS**:
- 🚨 **REAL browser automation only** - Must use Playwright
- 🚨 **NO HTTP simulation** - This is browser testing, not API testing  
- 🚨 **Mock APIs** - Uses mocked external API responses (free)
- 🚨 **Real screenshots** - PNG/JPG images taken by browsers, never text files
- ❌ **NEVER simulate** - If browser tests can't run, report honestly