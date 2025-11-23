# Browser Automation Workflows

Practical workflows combining Playwright and Superpowers Chrome for WorldArchitect.AI testing.

---

## Workflow 1: Daily Development Testing

**Goal:** Fast feedback during development

**Tools:** Superpowers Chrome (quick) → Playwright (comprehensive)

```bash
# Morning: Start Chrome session
chrome-ws start

# During development: Quick checks
chrome-ws new "http://localhost:5000"
chrome-ws click 0 "button.feature"
chrome-ws screenshot 0 > test.png

# Before commit: Run smoke test
./worldarchitect-chrome.sh smoke

# Before push: Run full E2E
cd skills/playwright-worldarchitect
node run.js examples/campaign-flow-test.js
```

**Duration:**
- Quick checks: 1-2s each
- Smoke test: 15-30s
- Full E2E: 5-10min

**Why This Workflow:**
- Fast iteration with Chrome during dev
- Comprehensive validation before commit
- Minimal overhead for quick checks

---

## Workflow 2: PR Visual Regression

**Goal:** Ensure UI changes don't break design

**Tools:** Playwright only

```bash
# Step 1: Capture baselines from main branch
git checkout main
cd skills/playwright-worldarchitect
npm install
npx playwright install chromium
node run.js examples/visual-regression-complete.js --baseline

# Step 2: Switch to feature branch
git checkout feature/new-ui

# Step 3: Compare against baselines
node run.js examples/visual-regression-complete.js

# Step 4: Review diffs
ls /tmp/playwright-diffs/

# Step 5: If intentional changes, promote to baselines
# (Manual decision after review)
node -e "require('./lib/visual-regression.js').promoteToBaselines('game-view')"
```

**Duration:** 8-12s per page (3 viewports)

**Why Playwright:**
- Built-in visual regression system
- Baseline management
- Automated diff generation
- Multi-viewport support

---

## Workflow 3: Bug Investigation

**Goal:** Reproduce and understand a reported bug

**Tools:** Superpowers Chrome (exploration) → Playwright (verification)

```bash
# Step 1: Quick reproduction with Chrome
chrome-ws start
chrome-ws new "http://localhost:5000/campaigns/123"
chrome-ws click 0 "button.dice-roll"
chrome-ws extract 0 ".error-message"
# Found bug: "Dice roller fails on first click"

# Step 2: Capture evidence
chrome-ws screenshot 0 > bug-before.png
chrome-ws html 0 ".dice-roller" > bug-html.txt

# Step 3: Fix the bug
# ... make code changes ...

# Step 4: Verify fix with Playwright test
cat > /tmp/verify-dice-fix.js <<'EOF'
const { launchBrowser, performDiceRoll } = require('./lib/helpers.js');

(async () => {
  const browser = await launchBrowser({ headless: false });
  const page = await browser.newPage();

  await page.goto('http://localhost:5000/campaigns/123');

  // Test dice roll (should not error)
  await performDiceRoll(page, 'attack');

  // Verify result appears
  const result = await page.locator('.dice-result').textContent();
  console.log(`✅ Dice roll succeeded: ${result}`);

  await browser.close();
})();
EOF

cd skills/playwright-worldarchitect
node run.js /tmp/verify-dice-fix.js

# Step 5: Add regression test
# ... create permanent test file ...
```

**Duration:**
- Investigation: 2-5min
- Verification: 30s-1min

**Why This Workflow:**
- Fast bug reproduction with Chrome
- Persistent session for investigation
- Reliable verification with Playwright
- Creates regression test

---

## Workflow 4: CI/CD Pipeline

**Goal:** Comprehensive automated testing in CI

**Tools:** Both (staged approach)

```yaml
# .github/workflows/test.yml

jobs:
  quick-smoke:
    name: Quick Smoke Test (30s)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install superpowers-chrome
        run: npm install github:obra/superpowers-chrome

      - name: Start dev server
        run: cd mvp_site && python main.py &

      - name: Wait for server
        run: sleep 10

      - name: Run smoke test
        run: ./worldarchitect-chrome.sh smoke http://localhost:5000
        timeout-minutes: 1

  full-e2e:
    name: Full E2E Suite (10min)
    needs: quick-smoke  # Only run if smoke passes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install Playwright
        run: |
          cd skills/playwright-worldarchitect
          npm install
          npx playwright install chromium

      - name: Start dev server
        run: cd mvp_site && python main.py &

      - name: Wait for server
        run: sleep 10

      - name: Run campaign flow test
        run: |
          cd skills/playwright-worldarchitect
          node run.js examples/campaign-flow-test.js

      - name: Run game mechanics test
        run: |
          cd skills/playwright-worldarchitect
          node run.js examples/game-mechanics-test.js

      - name: Run visual regression
        run: |
          cd skills/playwright-worldarchitect
          node run.js examples/visual-regression-test.js

      - name: Upload screenshots
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: screenshots
          path: /tmp/screenshot-*.png

  visual-regression:
    name: Visual Regression (PR only)
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0  # Need history for baseline comparison

      - name: Get baseline from main
        run: |
          git checkout main
          cd skills/playwright-worldarchitect
          npm install
          npx playwright install chromium
          node run.js examples/visual-regression-complete.js --baseline

      - name: Switch to PR branch
        run: git checkout ${{ github.head_ref }}

      - name: Compare visual changes
        run: |
          cd skills/playwright-worldarchitect
          node run.js examples/visual-regression-complete.js

      - name: Upload diffs
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: visual-diffs
          path: /tmp/playwright-diffs/
```

**Duration:**
- Smoke: 30s (fail fast)
- E2E: 10min (comprehensive)
- Visual: 5min (PR only)

**Why This Workflow:**
- Fast feedback with Chrome smoke test
- Comprehensive coverage with Playwright
- Visual regression on PRs only
- Parallel execution where possible

---

## Workflow 5: Manual QA Testing

**Goal:** Human verification of features

**Tools:** Superpowers Chrome

```bash
# QA engineer workflow

# 1. Start test session
chrome-ws start
SESSION_ID="qa-session-$(date +%s)"
mkdir -p "/tmp/$SESSION_ID"

# 2. Test new campaign feature
echo "Testing: Campaign creation"
chrome-ws new "http://localhost:5000/campaigns/new"
chrome-ws fill 0 "#campaign-name" "QA Test Campaign"
chrome-ws fill 0 "#description" "Testing new feature"
chrome-ws screenshot 0 > "/tmp/$SESSION_ID/01-campaign-form.png"
chrome-ws click 0 "button[type='submit']"
chrome-ws wait-for 0 ".success-message"
chrome-ws screenshot 0 > "/tmp/$SESSION_ID/02-campaign-created.png"

# 3. Test character creation
echo "Testing: Character creation"
chrome-ws click 0 "button:has-text('New Character')"
chrome-ws fill 0 "#character-name" "QA Test Character"
chrome-ws select 0 "#class" "Wizard"
chrome-ws screenshot 0 > "/tmp/$SESSION_ID/03-character-form.png"
chrome-ws click 0 "button[type='submit']"
chrome-ws screenshot 0 > "/tmp/$SESSION_ID/04-character-created.png"

# 4. Test game mechanics
echo "Testing: Dice rolling"
chrome-ws click 0 "button.dice-roll"
sleep 1
chrome-ws screenshot 0 > "/tmp/$SESSION_ID/05-dice-result.png"

# 5. Export test evidence
chrome-ws markdown 0 > "/tmp/$SESSION_ID/final-state.md"

# 6. Generate QA report
cat > "/tmp/$SESSION_ID/qa-report.md" <<EOF
# QA Test Report
Date: $(date)
Session: $SESSION_ID

## Tests Performed
1. Campaign Creation - ✅ PASS
2. Character Creation - ✅ PASS
3. Dice Rolling - ✅ PASS

## Evidence
- Screenshots: $(ls /tmp/$SESSION_ID/*.png | wc -l) files
- Final state: final-state.md

## Notes
- Feature works as expected
- No errors encountered
- Performance acceptable
EOF

echo "✅ QA session complete"
echo "📁 Report: /tmp/$SESSION_ID/qa-report.md"
echo "📁 Evidence: /tmp/$SESSION_ID/"
```

**Duration:** Flexible (human-paced)

**Why Superpowers Chrome:**
- CLI assists manual testing
- Easy screenshot capture
- Session persistence
- Organized evidence collection

---

## Workflow 6: Performance Testing

**Goal:** Measure page load and interaction speed

**Tools:** Both (different metrics)

```bash
# Chrome: Quick timing measurements
chrome-ws start
chrome-ws new "http://localhost:5000"

# Measure page load
chrome-ws eval 0 "performance.timing.loadEventEnd - performance.timing.navigationStart"
# Output: 1234 (ms)

# Measure interaction timing
chrome-ws eval 0 "performance.mark('start');
  document.querySelector('button').click();
  performance.mark('end');
  performance.measure('click', 'start', 'end');
  performance.getEntriesByName('click')[0].duration"

# Playwright: Comprehensive performance metrics
cat > /tmp/perf-test.js <<'EOF'
const { launchBrowser } = require('./lib/helpers.js');

(async () => {
  const browser = await launchBrowser({ headless: false });
  const page = await browser.newPage();

  // Enable performance metrics
  const client = await page.context().newCDPSession(page);
  await client.send('Performance.enable');

  // Navigate and measure
  const start = Date.now();
  await page.goto('http://localhost:5000');
  const loadTime = Date.now() - start;

  // Get metrics
  const metrics = await client.send('Performance.getMetrics');

  console.log(`Load Time: ${loadTime}ms`);
  console.log('Metrics:', metrics);

  // Test interaction performance
  await page.click('button.new-campaign');
  const timing = await page.evaluate(() =>
    JSON.stringify(performance.getEntriesByType('navigation')[0])
  );

  console.log('Navigation Timing:', timing);

  await browser.close();
})();
EOF

cd skills/playwright-worldarchitect
node run.js /tmp/perf-test.js
```

**Duration:** 1-2min per test

**Why Both:**
- Chrome: Quick spot checks
- Playwright: Comprehensive metrics

---

## Workflow 7: Regression Testing After Deploy

**Goal:** Verify deployed version works correctly

**Tools:** Playwright (fresh browser, comprehensive)

```bash
# Test deployed preview/staging environment

export BASE_URL="https://preview-pr-123.worldarchitect.ai"

cd skills/playwright-worldarchitect

# Run comprehensive test suite
node run.js examples/smoke-test.js
node run.js examples/campaign-flow-test.js
node run.js examples/game-mechanics-test.js

# Visual regression against production
git checkout main
node run.js examples/visual-regression-complete.js --baseline
git checkout feature/new-feature
# Compare feature against production baselines
node run.js examples/visual-regression-complete.js

# Generate deployment report
cat > /tmp/deploy-report.md <<EOF
# Deployment Verification Report

Environment: $BASE_URL
Date: $(date)

## Test Results
- Smoke Tests: ✅ PASS
- Campaign Flow: ✅ PASS
- Game Mechanics: ✅ PASS
- Visual Regression: ⚠️ 2 differences

## Visual Changes
- Desktop view: Changed (intentional)
- Tablet view: Changed (intentional)
- Mobile view: No change

## Recommendation
✅ Safe to deploy - changes are intentional
EOF

echo "✅ Deployment verification complete"
cat /tmp/deploy-report.md
```

**Duration:** 5-10min

**Why Playwright:**
- Fresh browser simulates user experience
- Comprehensive test coverage
- Visual regression comparison
- Reliable for deployment validation

---

## Choosing the Right Workflow

| Scenario | Recommended Workflow |
|----------|---------------------|
| Daily development | Workflow 1 (Chrome → Playwright) |
| PR review | Workflow 2 (Playwright visual) |
| Bug investigation | Workflow 3 (Chrome → Playwright) |
| CI/CD pipeline | Workflow 4 (Both, staged) |
| Manual QA | Workflow 5 (Chrome only) |
| Performance testing | Workflow 6 (Both) |
| Post-deploy verification | Workflow 7 (Playwright only) |

---

## Best Practices Summary

1. **Use Chrome for exploration, Playwright for automation**
2. **Start fast (smoke), go deep (E2E) only if needed**
3. **Keep Chrome sessions open during development**
4. **Fresh Playwright browsers for clean tests**
5. **Visual regression only when UI changes**
6. **Document workflows in scripts**
7. **Collect evidence (screenshots, markdown)**
8. **Automate repetitive workflows**

---

## Resources

- [Playwright Skill](../skills/playwright-worldarchitect/)
- [Superpowers Chrome Skill](../skills/superpowers-chrome-worldarchitect/)
- [Comparison Guide](./BROWSER_AUTOMATION_COMPARISON.md)
- [Unified /browser Command](../.claude/commands/browser.md)
