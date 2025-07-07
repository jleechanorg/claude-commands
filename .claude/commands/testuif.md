# Browser Tests (FULL) Command

**Purpose**: Run REAL browser tests with REAL APIs (costs money!)

**Action**: Execute browser automation tests using Playwright with real API calls

**Usage**: `/testuif`

**Action**: Simply run the UI test script with real APIs:

```bash
./run_ui_tests.sh
```

- ✅ Script handles all setup automatically (Playwright installation, browser dependencies, server startup)
- ✅ Report actual results/errors
- ❌ NEVER create fake output
- ⚠️ **WARNING**: This costs real money through API calls

**CRITICAL REQUIREMENTS**:
- 🚨 **REAL browser automation only** - Must use Playwright
- 🚨 **NO HTTP simulation** - This is browser testing, not API testing
- 🚨 **REAL APIs** - Makes actual external API calls (costs money!)
- 🚨 **Real screenshots** - PNG/JPG images taken by browsers, never text files
- ❌ **NEVER simulate** - If browser tests can't run, report honestly
- ⚠️ **COST WARNING** - Uses real API calls that incur charges