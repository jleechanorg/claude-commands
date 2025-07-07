# Browser Tests (Mock) Command

**Purpose**: Run REAL browser tests with mock APIs (free)

**Action**: Execute browser automation tests using Playwright with mocked API responses

**Usage**: `/testui`

**MANDATORY**: When using `/testui` command, follow this exact sequence:

1. **Check Playwright Installation**
   ```bash
   vpython -c "import playwright" || echo "STOP: Playwright not installed"
   ```
   - ✅ Continue only if import succeeds
   - ❌ FULL STOP if not installed - report: "Cannot run browser tests - Playwright not installed"

2. **Verify Browser Dependencies**
   ```bash
   vpython -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(headless=True); p.stop()" || echo "STOP: Browser deps missing"
   ```
   - ✅ Continue only if browser launches
   - ❌ FULL STOP if fails - report: "Cannot launch browsers - missing system dependencies"

3. **Start Test Server**
   ```bash
   TESTING=true PORT=6006 vpython mvp_site/main.py serve &
   sleep 3
   curl -s http://localhost:6006 || echo "STOP: Server not running"
   ```
   - ✅ Continue only if server responds
   - ❌ FULL STOP if fails - report: "Cannot start test server"

4. **Run Browser Test**
   ```bash
   TESTING=true vpython testing_ui/test_name.py
   ```
   - ✅ Report actual results/errors
   - ❌ NEVER create fake output

**GOLDEN RULE**: Stop at first failure. Never proceed to simulate missing components.

**CRITICAL REQUIREMENTS**:
- 🚨 **REAL browser automation only** - Must use Playwright
- 🚨 **NO HTTP simulation** - This is browser testing, not API testing  
- 🚨 **Mock APIs** - Uses mocked external API responses (free)
- 🚨 **Real screenshots** - PNG/JPG images taken by browsers, never text files
- ❌ **NEVER simulate** - If browser tests can't run, report honestly