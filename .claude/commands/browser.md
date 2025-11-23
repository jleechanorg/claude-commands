---
description: Unified browser automation - intelligently uses Playwright or Superpowers Chrome
type: tool
scope: project
execution_mode: immediate
---

# /browser - Unified Browser Automation

## Purpose
Intelligent browser automation command that automatically selects the best tool (Playwright or Superpowers Chrome) based on the task requirements.

## Activation
User types `/browser` followed by a task description or uses one of the subcommands.

## Decision Logic

The command analyzes the request and chooses:

### **Playwright** for:
- Visual regression testing
- Multi-step E2E workflows (>5 steps)
- Fresh browser requirements
- Multi-browser testing (Firefox, WebKit)
- Complex scenarios with retry logic
- Token optimization needs (FocusAgent, D2Snap)

### **Superpowers Chrome** for:
- Quick smoke tests (<5 steps)
- Debugging and exploration
- Persistent session needs
- CLI-style automation
- Zero-dependency requirements
- Fast iteration cycles

## Usage

### Smart Mode (Auto-detect)
```
/browser test campaign creation flow with screenshots
→ Uses Playwright (visual + multi-step)

/browser quick smoke test
→ Uses Superpowers Chrome (quick + simple)

/browser debug the login page
→ Uses Superpowers Chrome (debug + exploration)

/browser run visual regression on game interface
→ Uses Playwright (visual regression)
```

### Explicit Tool Selection
```
/browser playwright <task>
→ Forces Playwright

/browser chrome <task>
→ Forces Superpowers Chrome
```

## Subcommands

### `/browser smoke [url]`
Quick smoke test across main pages

**Tool:** Superpowers Chrome (fast, lightweight)

```
/browser smoke http://localhost:5000
```

**Runs:**
- Home page loads
- Navigation exists
- Login page loads
- Campaigns page loads

**Duration:** ~15-30 seconds

---

### `/browser campaign [url] [name]`
Test campaign creation flow

**Tool:** Auto-detect
- Simple test (no screenshots): Superpowers Chrome
- With screenshots: Playwright

```
/browser campaign http://localhost:5000 "Test Campaign"
```

---

### `/browser visual [url] [name]`
Visual regression testing

**Tool:** Playwright (required for visual regression)

```
/browser visual http://localhost:5000/game game-interface
```

**Captures:**
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

**Compares** against baselines and reports differences.

---

### `/browser debug [url]`
Interactive debugging session

**Tool:** Superpowers Chrome (persistent session)

```
/browser debug http://localhost:5000/campaigns/123
```

**Opens:** Chrome with remote debugging, provides CLI for exploration

---

### `/browser e2e [test-name]`
Run E2E test suite

**Tool:** Playwright (comprehensive testing)

```
/browser e2e campaign-flow
```

**Available tests:**
- `campaign-flow` - Campaign creation, viewing, deletion
- `game-mechanics` - Character creation, dice rolling, actions
- `smoke` - Quick validation across pages
- `visual-regression` - Screenshot comparison

---

## Execution Workflow

### Phase 1: Analyze Request

Claude analyzes the user's request for:

1. **Complexity indicators:**
   - "quick", "fast", "smoke" → Superpowers Chrome
   - "E2E", "comprehensive", "full" → Playwright

2. **Feature requirements:**
   - "screenshot", "visual", "regression" → Playwright
   - "debug", "explore", "check" → Superpowers Chrome

3. **Duration hints:**
   - "< 1 minute" → Superpowers Chrome
   - "> 5 minutes" → Playwright

4. **Session needs:**
   - "persistent", "keep open", "continue" → Superpowers Chrome
   - "fresh", "clean", "isolated" → Playwright

### Phase 2: Execute with Chosen Tool

**If Superpowers Chrome:**
```bash
# Start Chrome
./worldarchitect-chrome.sh start

# Execute task
./worldarchitect-chrome.sh <task> [args...]

# Report results
```

**If Playwright:**
```bash
# Execute Playwright test
cd skills/playwright-worldarchitect
node run.js <test-script>

# Report results with screenshots
```

### Phase 3: Report Results

**Standard Report Format:**
```
🎭 Browser Automation Results
Tool: [Playwright | Superpowers Chrome]
Duration: [time]

✅ Task completed successfully

Details:
- [Step 1]: Passed
- [Step 2]: Passed
- [Step 3]: Passed

Screenshots:
- /tmp/screenshot-1.png
- /tmp/screenshot-2.png

Next steps:
- [Suggested follow-up actions]
```

## Examples

### Example 1: Smart Detection (Visual Regression)
```
User: /browser test the game interface visually

Analysis:
- Keywords: "test", "visually"
- Implies: Visual regression testing
- Tool: Playwright

Execution:
1. cd skills/playwright-worldarchitect
2. node run.js examples/visual-regression-test.js

Result:
✅ Visual regression completed
- Desktop: Passed
- Tablet: Passed
- Mobile: Passed
```

### Example 2: Smart Detection (Quick Smoke)
```
User: /browser quick smoke test on localhost

Analysis:
- Keywords: "quick", "smoke"
- Duration: Short (<1 min)
- Tool: Superpowers Chrome

Execution:
1. ./worldarchitect-chrome.sh smoke http://localhost:5000

Result:
✅ All smoke tests passed (18s)
- Home page: ✅
- Navigation: ✅
- Login: ✅
- Campaigns: ✅
```

### Example 3: Explicit Tool Selection
```
User: /browser playwright run campaign flow test

Analysis:
- Explicit: "playwright"
- Tool: Playwright (forced)

Execution:
1. cd skills/playwright-worldarchitect
2. node run.js examples/campaign-flow-test.js

Result:
✅ Campaign flow test passed (8.3s)
- Campaign created: ✅
- Campaign appears in list: ✅
- Screenshots captured: ✅
```

### Example 4: Debug Session
```
User: /browser debug http://localhost:5000/campaigns/123

Analysis:
- Keywords: "debug"
- Implies: Interactive exploration
- Tool: Superpowers Chrome

Execution:
1. chrome-ws start
2. chrome-ws new "http://localhost:5000/campaigns/123"
3. Provides CLI commands for exploration

Result:
🔍 Debug session started
Chrome DevTools: http://localhost:9222

Available commands:
- chrome-ws extract 0 ".campaign-name"
- chrome-ws screenshot 0 > debug.png
- chrome-ws eval 0 "console.log('debug')"

Session: /tmp/chrome-worldarchitect-<pid>
```

## Tool Comparison Quick Reference

| Feature | Playwright | Superpowers Chrome |
|---------|-----------|-------------------|
| Startup Time | 3-5s | 1-2s |
| Dependencies | ~200 packages | 0 |
| Visual Regression | ✅ Built-in | ❌ Manual |
| Multi-browser | ✅ Yes | ❌ Chrome only |
| Session Persistence | ❌ No | ✅ Yes |
| CLI Workflow | ❌ No | ✅ Yes |
| Token Optimization | ✅ 50-80% reduction | ❌ No |
| Best For | E2E, visual testing | Quick tests, debug |

## Configuration

### Environment Variables

```bash
# Force specific tool
export BROWSER_TOOL=playwright  # or 'chrome'

# Headless mode
export PLAYWRIGHT_HEADLESS=true
export CHROME_HEADLESS=true

# Custom ports
export CHROME_WS_PORT=9222

# Screenshot directory
export SCREENSHOT_DIR=/tmp/browser-screenshots
```

### Defaults

```bash
# Default URLs
DEFAULT_URL=http://localhost:5000

# Default timeouts
PLAYWRIGHT_TIMEOUT=30000  # 30s
CHROME_TIMEOUT=10000      # 10s

# Default viewports
DESKTOP_VIEWPORT=1920x1080
TABLET_VIEWPORT=768x1024
MOBILE_VIEWPORT=375x667
```

## Integration with Other Commands

- `/teste` - Mock E2E tests → Use `/browser smoke` for real verification
- `/smoke` - MCP smoke tests → Add `/browser smoke` for UI layer
- `/playwright` - Direct Playwright access → Use `/browser` for smart selection
- `/tdd` - Test-driven development → Write `/browser` tests first

## Troubleshooting

### Error: "No browser tool available"
```bash
# Install both tools
cd skills/playwright-worldarchitect && npm install
npm install github:obra/superpowers-chrome
```

### Error: "Chrome not responding"
```bash
# Restart Chrome
pkill chrome
./worldarchitect-chrome.sh start
```

### Error: "Playwright browser not found"
```bash
# Install browsers
cd skills/playwright-worldarchitect
npx playwright install chromium
```

### Slow Performance
```
Problem: Tests taking too long

Solution 1: Use Superpowers Chrome for quick tests
/browser chrome quick smoke

Solution 2: Enable headless mode
export PLAYWRIGHT_HEADLESS=true
/browser smoke

Solution 3: Reduce viewport count
/browser visual (only desktop)
```

## Best Practices

### 1. Let Auto-Detection Work
```
✅ GOOD: /browser test campaign creation
❌ AVOID: Manually choosing tool without reason
```

### 2. Use Subcommands for Common Tasks
```
✅ GOOD: /browser smoke http://localhost:5000
❌ AVOID: Typing full Playwright/Chrome commands
```

### 3. Combine with Other Commands
```
✅ GOOD: /teste → /browser smoke → /browser e2e campaign-flow
❌ AVOID: Only running one type of test
```

### 4. Debug with Chrome, Test with Playwright
```
✅ GOOD: /browser debug (find issue) → /browser playwright (verify fix)
❌ AVOID: Debugging with heavy E2E suite
```

## Performance Benchmarks

| Task | Playwright | Superpowers Chrome | Winner |
|------|-----------|-------------------|--------|
| Smoke test (5 pages) | 45s | 15s | Chrome (3x faster) |
| Campaign creation | 8s | 4s | Chrome (2x faster) |
| Visual regression (3 views) | 12s | N/A | Playwright (only option) |
| Full E2E (20 tests) | 12 min | N/A | Playwright (only option) |
| Debug single page | 5s | 2s | Chrome (2.5x faster) |

## Advanced Usage

### Parallel Execution
```bash
# Run smoke test while E2E runs
/browser chrome smoke &
/browser playwright e2e campaign-flow &
wait
```

### Custom Test Scripts
```bash
# Create custom Playwright test
cat > /tmp/my-test.js <<EOF
const { launchBrowser } = require('./lib/helpers.js');
// ... your test code
EOF

/browser playwright run /tmp/my-test.js
```

### MCP Mode Integration
```json
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": ["github:obra/superpowers-chrome"]
    }
  }
}
```

Then in Claude Desktop:
```
User: /browser (auto-detects MCP, uses superpowers-chrome)
```

## Resources

- [Playwright Skill Documentation](../skills/playwright-worldarchitect/SKILL.md)
- [Superpowers Chrome Documentation](../skills/superpowers-chrome-worldarchitect/README.md)
- [Comparison Guide](../docs/BROWSER_AUTOMATION_COMPARISON.md)
- [Example Workflows](../skills/playwright-worldarchitect/examples/)

---

**Note:** This command intelligently chooses between Playwright and Superpowers Chrome based on your needs. For direct control, use `/playwright` or the chrome-ws CLI directly.
