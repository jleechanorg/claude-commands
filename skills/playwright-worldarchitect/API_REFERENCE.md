# WorldArchitect.AI Playwright Skill - API Reference

## Table of Contents

1. [Core Helpers](#core-helpers)
2. [RPG-Specific Functions](#rpg-specific-functions)
3. [DOM Optimization](#dom-optimization)
4. [Modular Agent Architecture](#modular-agent-architecture)
5. [Visual Regression Testing](#visual-regression-testing)
6. [Advanced Patterns](#advanced-patterns)

---

## Core Helpers

### Browser Management

#### `launchBrowser(options)`
Launch browser with configurable options.

```javascript
const browser = await launchBrowser({
  headless: false,
  slowMo: 100,
  browserType: 'chromium',
  args: []
});
```

**Options:**
- `headless` (boolean): Run in headless mode (default: false)
- `slowMo` (number): Slow motion delay in ms (default: 100)
- `browserType` (string): 'chromium', 'firefox', or 'webkit' (default: 'chromium')
- `args` (array): Additional browser arguments

#### `createContext(browser, options)`
Create browser context with options.

```javascript
const context = await createContext(browser, {
  viewport: { width: 1920, height: 1080 },
  locale: 'en-US',
  timezone: 'America/New_York'
});
```

#### `createPage(context, options)`
Create new page with optional configuration.

```javascript
const page = await createPage(context, {
  viewport: { width: 1920, height: 1080 },
  extraHTTPHeaders: { 'X-Test-Mode': 'true' }
});
```

### Element Interaction

#### `safeClick(page, selector, options)`
Safe click with retry logic.

```javascript
await safeClick(page, 'button.submit', {
  retries: 3,
  delay: 1000
});
```

**Parameters:**
- `page` (Page): Playwright page
- `selector` (string): Element selector
- `options.retries` (number): Retry attempts (default: 3)
- `options.delay` (number): Delay between retries in ms (default: 1000)

#### `safeType(page, selector, text, options)`
Safe typing with field clearing.

```javascript
await safeType(page, '#username', 'testuser', {
  clear: true,
  slow: false
});
```

#### `scrollPage(page, direction, distance)`
Scroll page in specified direction.

```javascript
await scrollPage(page, 'down', 500);
// Directions: 'down', 'up', 'top', 'bottom'
```

### Data Extraction

#### `extractTexts(page, selector)`
Extract text from multiple elements.

```javascript
const texts = await extractTexts(page, '.campaign-name');
// Returns: ['Campaign 1', 'Campaign 2', ...]
```

#### `extractTableData(page, tableSelector)`
Extract table data into structured format.

```javascript
const data = await extractTableData(page, 'table.campaigns');
// Returns: [{ name: '...', created: '...' }, ...]
```

### Utilities

#### `takeScreenshot(page, name, options)`
Take screenshot with timestamp.

```javascript
const filepath = await takeScreenshot(page, 'error-state', {
  fullPage: true
});
```

#### `authenticate(page, credentials, selectors)`
Authenticate user with flexible selectors.

```javascript
await authenticate(page,
  { username: 'test@example.com', password: 'pass123' },
  { usernameSelector: '#email', passwordSelector: '#password' }
);
```

#### `detectDevServers()`
Detect running development servers.

```javascript
const servers = await detectDevServers();
// Returns: ['http://localhost:5000', 'http://localhost:8080']
```

---

## RPG-Specific Functions

### Campaign Management

#### `createCampaign(page, campaignData)`
Create a new campaign.

```javascript
await createCampaign(page, {
  name: 'Dragon Quest',
  description: 'Epic adventure in the mountains',
  setting: 'fantasy'
});
```

#### `verifyCampaignState(page, expectedElements)`
Verify campaign state elements.

```javascript
await verifyCampaignState(page, [
  '.campaign-name',
  '.character-list',
  '.game-log'
]);
```

### Character Management

#### `createCharacter(page, characterData)`
Create a new character.

```javascript
await createCharacter(page, {
  name: 'Gandalf the Grey',
  characterClass: 'Wizard',
  race: 'Human',
  level: 5
});
```

### Game Mechanics

#### `performDiceRoll(page, actionType)`
Perform a dice roll action.

```javascript
const result = await performDiceRoll(page, 'attack');
// Action types: 'attack', 'skill', 'save'
```

#### `sendGameAction(page, action)`
Send a game action/message.

```javascript
await sendGameAction(page, 'I cast fireball at the dragon');
```

### Visual Testing

#### `takeResponsiveScreenshots(page, name)`
Take screenshots across viewports.

```javascript
const screenshots = await takeResponsiveScreenshots(page, 'game-view');
// Returns: [
//   { viewport: 'desktop', file: '/tmp/screenshot-game-view-desktop-...' },
//   { viewport: 'tablet', file: '...' },
//   { viewport: 'mobile', file: '...' }
// ]
```

---

## DOM Optimization

*Reduces observation size by 50-80% while maintaining performance.*

### Focused DOM Extraction

#### `getFocusedDOM(page, options)`
Extract focused DOM snapshot with reduced token size.

```javascript
const { getFocusedDOM } = require('./lib/dom-optimizer.js');

const focusedDOM = await getFocusedDOM(page, {
  includeHidden: false,
  maxDepth: 3,
  includeStyles: false,
  focusSelectors: ['main', 'article', '[role="main"]']
});
```

**Options:**
- `includeHidden` (boolean): Include hidden elements (default: false)
- `maxDepth` (number): Maximum DOM traversal depth (default: 3)
- `includeStyles` (boolean): Include computed styles (default: false)
- `focusSelectors` (array): Areas to focus on

**Benefits:**
- 50-80% token reduction (FocusAgent research)
- Focuses on relevant interactive elements
- Maintains semantic structure
- Filters noise (hidden elements, decorative content)

### Accessibility Snapshot

#### `getAccessibilitySnapshot(page)`
Extract accessibility tree for semantic DOM information.

```javascript
const a11ySnapshot = await getAccessibilitySnapshot(page);
```

### Security-Aware Patterns

#### `observeAction(page, selector, actionType)`
Observe action without execution (Stagehand pattern).

```javascript
const observation = await observeAction(page, 'button.submit', 'click');

if (observation.safeToExecute) {
  await page.click('button.submit');
}
```

**Returns:**
```javascript
{
  success: true,
  selector: 'button.submit',
  element: {
    tag: 'button',
    text: 'Submit',
    visible: true,
    actionValid: true
  },
  safeToExecute: true
}
```

#### `filterSensitiveData(snapshot, sensitivePatterns)`
Filter sensitive information from DOM snapshot.

```javascript
const safeSnapshot = filterSensitiveData(domSnapshot, [
  /password/i,
  /token/i,
  /api[_-]?key/i
]);
```

### Interactive Elements Only

#### `getInteractiveElements(page)`
Extract interactive elements only (minimal toolset curation).

```javascript
const elements = await getInteractiveElements(page);
// Returns: Array of clickable/typeable elements only
```

**Benefits:**
- Dramatic token reduction (>80%)
- Prevents tool overload
- Focuses on actionable elements
- Reduces decision fatigue

### Optimization Measurement

#### `measureOptimization(fullDOM, focusedDOM)`
Measure DOM observation size reduction.

```javascript
const metrics = measureOptimization(fullDOM, focusedDOM);
console.log(`Reduction: ${metrics.reduction}`);
// Output: "Reduction: 72.5%"
```

---

## Modular Agent Architecture

*Separation of concerns: Planner → Generator → Healer*

### AgentOrchestrator

#### Constructor
```javascript
const { AgentOrchestrator } = require('./lib/modular-agent.js');
const orchestrator = new AgentOrchestrator(page, { verbose: true });
```

#### `executeWorkflow(goal, actions)`
Execute complete workflow with planning and healing.

```javascript
const result = await orchestrator.executeWorkflow(
  'Create new campaign',
  [
    {
      type: 'click',
      selector: 'button:has-text("New Campaign")',
      alternativeSelectors: ['a[href="/campaigns/new"]']
    },
    {
      type: 'type',
      selector: '#campaign-name',
      text: 'Test Campaign'
    }
  ]
);
```

**Action Types:**
- `click`: Click element
- `type`: Type text into input
- `navigate`: Navigate to URL
- `wait`: Wait for duration

**Returns:**
```javascript
{
  goal: 'Create new campaign',
  success: true,
  duration: 5432,
  executionResults: [...],
  healingResults: [...]
}
```

### Individual Agents

#### PlannerAgent
High-level reasoning about browser state.

```javascript
const { PlannerAgent } = require('./lib/modular-agent.js');
const planner = new PlannerAgent(page, { verbose: true });

const plan = await planner.analyzePage('Navigate to campaigns');
```

#### GeneratorAgent
Execute specific actions based on plan.

```javascript
const { GeneratorAgent } = require('./lib/modular-agent.js');
const generator = new GeneratorAgent(page, { verbose: true });

const result = await generator.executeAction({
  type: 'click',
  selector: 'button.submit'
});
```

#### HealerAgent
Error recovery and retry logic.

```javascript
const { HealerAgent } = require('./lib/modular-agent.js');
const healer = new HealerAgent(page, { verbose: true });

const healing = await healer.heal(failedAction, error);
```

**Healing Strategies:**
1. Wait and retry
2. Try alternative selectors
3. Reload page and retry

---

## Visual Regression Testing

### Workflow Functions

#### `runVisualRegression(page, testName, options)`
Complete visual regression workflow.

```javascript
const { runVisualRegression } = require('./lib/visual-regression.js');

const results = await runVisualRegression(page, 'home-page', {
  captureBaseline: false,
  compare: true,
  promoteOnPass: false
});
```

**Options:**
- `captureBaseline` (boolean): Capture new baselines
- `compare` (boolean): Compare against baselines
- `promoteOnPass` (boolean): Promote if all tests pass

### Baseline Management

#### `captureBaselines(page, testName, options)`
Capture baseline screenshots.

```javascript
await captureBaselines(page, 'campaign-view', {
  viewports: [VIEWPORTS.desktop, VIEWPORTS.tablet, VIEWPORTS.mobile],
  fullPage: true
});
```

#### `compareWithBaselines(testName, options)`
Compare current screenshots against baselines.

```javascript
const results = await compareWithBaselines('campaign-view', {
  threshold: 0.01 // 1% difference threshold
});
```

**Returns:**
```javascript
{
  testName: 'campaign-view',
  passed: 2,
  failed: 1,
  comparisons: [
    {
      viewport: 'desktop',
      status: 'pass',
      sizeDifference: '0.5%'
    },
    {
      viewport: 'mobile',
      status: 'fail',
      sizeDifference: '2.3%',
      diffFile: '/tmp/playwright-diffs/...'
    }
  ]
}
```

#### `promoteToBaselines(testName)`
Promote current screenshots to baselines.

```javascript
promoteToBaselines('campaign-view');
```

### Utilities

#### `listBaselines()`
List all baseline files.

```javascript
const baselines = listBaselines();
```

#### `cleanup(options)`
Clean up old screenshots.

```javascript
cleanup({
  keepBaselines: true,
  keepCurrent: false,
  keepDiffs: false
});
```

### Standard Viewports

```javascript
const { VIEWPORTS } = require('./lib/visual-regression.js');

// Available viewports:
VIEWPORTS.desktop  // 1920x1080
VIEWPORTS.laptop   // 1366x768
VIEWPORTS.tablet   // 768x1024
VIEWPORTS.mobile   // 375x667
```

---

## Advanced Patterns

### Pattern 1: Observe-Execute-Heal

```javascript
const orchestrator = new AgentOrchestrator(page);

await orchestrator.executeWorkflow('Safe form submission', [
  { type: 'observe', selector: '#form-field' },
  { type: 'type', selector: '#form-field', text: 'data' },
  { type: 'observe', selector: 'button.submit' },
  { type: 'click', selector: 'button.submit' }
]);
```

### Pattern 2: Focused DOM + Interactive Elements

```javascript
// Get minimal DOM representation
const focusedDOM = await getFocusedDOM(page, { maxDepth: 2 });
const interactive = await getInteractiveElements(page);

// LLM sees only relevant elements (80% token reduction)
const context = { focusedDOM, interactive };
```

### Pattern 3: Security-Aware Testing

```javascript
// Filter sensitive data before LLM sees it
const rawDOM = await getFocusedDOM(page);
const safeDOM = filterSensitiveData(rawDOM);

// Observe before executing
const observation = await observeAction(page, selector, 'click');
if (observation.safeToExecute) {
  await page.click(selector);
}
```

### Pattern 4: Visual Regression in CI

```javascript
// Capture baselines (one-time)
if (process.env.CAPTURE_BASELINE) {
  await captureBaselines(page, 'feature-x');
}

// Compare in CI
const results = await runVisualRegression(page, 'feature-x', {
  compare: true,
  promoteOnPass: false
});

if (results.comparison.failed > 0) {
  throw new Error('Visual regression detected');
}
```

---

## Performance Benchmarks

| Operation | Token Count | Time |
|-----------|-------------|------|
| Full DOM | ~10,000 tokens | - |
| Focused DOM (FocusAgent) | ~2,000 tokens | - |
| Interactive Elements Only | ~500 tokens | - |
| Campaign creation test | - | 5-8s |
| Visual regression (3 viewports) | - | 8-12s |
| Modular agent workflow | - | 10-15s |

## Research Citations

1. **FocusAgent**: Reduces observation size by >50% (often >80%) - [OpenReview](https://openreview.net/pdf/a2e9652cb92e4140bf133ef06ec9824cecdf4ff2.pdf)
2. **D2Snap**: DOM downsampling maintaining ~1000 tokens - [arXiv](https://arxiv.org/html/2508.04412v2)
3. **Stagehand**: Security-aware observe() before act() pattern - [Stagehand Docs](https://stagehand.readme-i18n.com/examples/best_practices)

---

## Next Steps

1. Install Playwright: `cd skills/playwright-worldarchitect && npm install`
2. Run examples: `node run.js examples/smoke-test.js`
3. Capture baselines: `node run.js examples/visual-regression-complete.js --baseline`
4. Test DOM optimization: `node run.js examples/advanced-dom-optimization.js`
5. Try modular agents: `node run.js examples/modular-agent-workflow.js`
