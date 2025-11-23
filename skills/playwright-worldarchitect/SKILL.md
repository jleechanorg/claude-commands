# WorldArchitect.AI Playwright Browser Automation Skill

## Purpose
Custom browser automation using Playwright for testing WorldArchitect.AI RPG campaigns, character creation, dice mechanics, game interactions, and visual regression testing.

## Critical Workflow (In Order)

1. **Auto-detect dev servers** - Run server detection first for localhost testing
2. **Write scripts to /tmp** - Never clutter the skill or project directory
3. **Use visible browser by default** - `headless: false` unless explicitly requested otherwise
4. **Parameterize URLs** - Make endpoints configurable via constants
5. **Use RPG-specific helpers** - Leverage WorldArchitect helper functions for game testing

## How It Works

**User describes automation needs** → **Detect running servers** → **Write custom Playwright code to `/tmp/playwright-test-*.js`** → **Execute via `cd $SKILL_DIR && node run.js /tmp/playwright-test-*.js`** → **Display results with real-time browser visibility**

## Available Helpers

Import from `lib/helpers.js`:

```javascript
const {
  // Core browser management
  launchBrowser,
  createContext,
  createPage,
  waitForPageReady,

  // Element interaction
  safeClick,
  safeType,
  extractTexts,
  scrollPage,

  // Data extraction
  extractTableData,
  handleCookieBanner,
  takeScreenshot,

  // Advanced automation
  authenticate,
  retryWithBackoff,
  detectDevServers,

  // WorldArchitect RPG-specific
  createCampaign,
  createCharacter,
  performDiceRoll,
  sendGameAction,
  verifyCampaignState,
  takeResponsiveScreenshots
} = require('./lib/helpers.js');
```

## WorldArchitect Test Patterns

### Pattern 1: Campaign Creation Flow
```javascript
const { launchBrowser, createPage, detectDevServers, createCampaign, verifyCampaignState } = require('./lib/helpers.js');

const servers = await detectDevServers();
const BASE_URL = servers[0] || 'http://localhost:5000';

const browser = await launchBrowser({ headless: false });
const context = await browser.newContext();
const page = await context.newPage();

await page.goto(`${BASE_URL}/`);
await createCampaign(page, {
  name: 'Dragon Quest',
  description: 'Epic adventure in the mountains',
  setting: 'fantasy'
});

await verifyCampaignState(page);
await browser.close();
```

### Pattern 2: Character Creation & Dice Rolling
```javascript
const { launchBrowser, createCharacter, performDiceRoll, sendGameAction } = require('./lib/helpers.js');

const browser = await launchBrowser({ headless: false });
const page = await browser.newPage();

await page.goto('http://localhost:5000/campaigns/123');

// Create character
await createCharacter(page, {
  name: 'Gandalf the Grey',
  characterClass: 'Wizard',
  race: 'Human',
  level: 5
});

// Perform dice roll
await performDiceRoll(page, 'attack');

// Send game action
await sendGameAction(page, 'I cast fireball at the dragon');

await browser.close();
```

### Pattern 3: Visual Regression Testing
```javascript
const { launchBrowser, takeResponsiveScreenshots, takeScreenshot } = require('./lib/helpers.js');

const browser = await launchBrowser({ headless: false });
const page = await browser.newPage();

await page.goto('http://localhost:5000/campaigns/123/game');

// Take screenshots across viewports
await takeResponsiveScreenshots(page, 'game-view');

// Take specific element screenshot
await takeScreenshot(page, 'dice-roller', { fullPage: false });

await browser.close();
```

### Pattern 4: Authentication & Session Testing
```javascript
const { launchBrowser, authenticate, safeClick, waitForPageReady } = require('./lib/helpers.js');

const browser = await launchBrowser({ headless: false });
const page = await browser.newPage();

await page.goto('http://localhost:5000/login');

// Login
await authenticate(page, {
  username: 'test@example.com',
  password: 'testpass123'
}, {
  usernameSelector: '#email',
  passwordSelector: '#password',
  submitSelector: 'button[type="submit"]'
});

// Verify dashboard
await waitForPageReady(page);
const dashboardTitle = await page.textContent('h1');
console.log('✅ Dashboard loaded:', dashboardTitle);

await browser.close();
```

### Pattern 5: Form Validation Testing
```javascript
const { launchBrowser, safeType, safeClick, extractTexts } = require('./lib/helpers.js');

const browser = await launchBrowser({ headless: false });
const page = await browser.newPage();

await page.goto('http://localhost:5000/campaigns/new');

// Test empty form submission
await safeClick(page, 'button[type="submit"]');

// Extract validation errors
const errors = await extractTexts(page, '.error-message, .field-error');
console.log('Validation errors:', errors);

// Fill valid data
await safeType(page, '#campaign-name', 'Valid Campaign');
await safeClick(page, 'button[type="submit"]');

await browser.close();
```

### Pattern 6: Link & Navigation Testing
```javascript
const { launchBrowser, extractTexts } = require('./lib/helpers.js');

const browser = await launchBrowser({ headless: false });
const page = await browser.newPage();

await page.goto('http://localhost:5000/');

// Extract all navigation links
const links = await page.$$eval('a[href]', links =>
  links.map(l => ({ text: l.textContent.trim(), href: l.href }))
);

// Test each link
for (const link of links) {
  console.log(`Testing: ${link.text} -> ${link.href}`);
  const response = await page.goto(link.href);
  const status = response.status();

  if (status >= 400) {
    console.error(`❌ ${link.href} returned ${status}`);
  } else {
    console.log(`✅ ${link.href} OK (${status})`);
  }
}

await browser.close();
```

## Execution Methods

### File-based (Recommended for Complex Tests)
```bash
# Write test to /tmp/
cd $SKILL_DIR && node run.js /tmp/playwright-test-campaign.js
```

### Inline (Quick One-off Tasks)
```bash
cd $SKILL_DIR && node run.js "
const { chromium } = require('playwright');
const browser = await chromium.launch({ headless: false });
const page = await browser.newPage();
await page.goto('http://localhost:5000');
const title = await page.title();
console.log('Page title:', title);
await browser.close();
"
```

## Key Principles

1. **Always detect servers before hardcoding URLs** - Use `detectDevServers()`
2. **Default to visible browser mode for debugging** - Set `headless: false`
3. **Use wait strategies over fixed timeouts** - Use `waitForPageReady()`, `safeClick()`
4. **Include comprehensive error handling** - Wrap operations in try-catch
5. **Track progress via console output** - Log each major step
6. **Leverage RPG-specific helpers** - Use `createCampaign()`, `createCharacter()`, etc.
7. **Test responsively** - Use `takeResponsiveScreenshots()` for visual regression

## Test Coverage Areas

### Campaign Management
- Campaign creation with various settings
- Campaign listing and filtering
- Campaign deletion and archival
- Multi-user campaign access

### Character Management
- Character creation with D&D 5e classes/races
- Character sheet validation
- Character progression and leveling
- Inventory management

### Game Mechanics
- Dice rolling (d4, d6, d8, d10, d12, d20, d100)
- Combat actions (attack, defend, cast)
- Skill checks and saving throws
- Turn-based gameplay flow

### UI/UX Testing
- Responsive design (desktop, tablet, mobile)
- Dark/light theme switching
- Accessibility (ARIA labels, keyboard navigation)
- Loading states and error messages

### Integration Testing
- Firebase authentication flow
- Firestore data persistence
- Gemini AI response generation
- Real-time game state updates

## Environment Detection

The skill automatically detects:
- **Development servers**: Ports 3000, 5000, 8000, 8080, 5173, 4200, 8081
- **CI environment**: Adjusts timeouts and headless settings
- **Authentication**: Test bypass headers or real login flow

## Best Practices

### ✅ DO
- Write tests to `/tmp/playwright-test-*.js`
- Use server detection for dynamic URLs
- Leverage helper functions for common tasks
- Add console.log statements for progress tracking
- Use meaningful test names and descriptions
- Clean up browser resources with `await browser.close()`

### ❌ DON'T
- Write tests to skill directory or project root
- Hardcode localhost URLs without detection
- Use fixed timeouts without wait strategies
- Skip error handling
- Leave browsers running after tests
- Test production servers without explicit approval

## Integration with Existing Commands

This skill integrates with WorldArchitect slash commands:

- `/teste` - Mock E2E tests (use Playwright for real browser verification)
- `/testui` - Browser tests (use this skill for implementation)
- `/smoke` - Smoke tests (add Playwright browser checks)
- `/tdd` - Test-driven development (write Playwright tests first)

## Troubleshooting

### Browser doesn't launch
```bash
# Install Chromium
cd skills/playwright-worldarchitect
npx playwright install chromium
```

### Server not detected
```bash
# Start dev server first
cd mvp_site
python main.py
```

### Element not found
```javascript
// Use retry logic and multiple selectors
await safeClick(page, 'button:has-text("Submit"), button[type="submit"], #submit-btn');
```

### Screenshots not saved
```javascript
// Ensure /tmp/ directory exists and is writable
const fs = require('fs');
if (!fs.existsSync('/tmp')) fs.mkdirSync('/tmp');
```

## Performance Notes

- First run: ~30s (Playwright installation)
- Subsequent runs: ~3-5s (browser launch)
- Headless mode: ~40% faster
- Slow motion: Adds 100ms per action

## Security Considerations

- Use test authentication tokens, not production credentials
- Clean up test data after runs
- Never commit screenshots with sensitive data
- Use `X-Test-Bypass-Auth` header for automated tests

## Next Steps

1. Run your first test: `/testui` command
2. Create custom test scripts in `/tmp/`
3. Add visual regression baselines
4. Integrate with CI/CD pipeline
5. Expand test coverage systematically

---

**Skill Directory**: `skills/playwright-worldarchitect/`
**Executor**: `run.js`
**Helpers**: `lib/helpers.js`
**Dependencies**: `package.json`
