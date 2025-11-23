# WorldArchitect.AI Playwright Skill

Browser automation skill for WorldArchitect.AI using Playwright. Enables AI-powered testing of RPG campaigns, character creation, dice mechanics, and game interactions.

## Quick Start

```bash
# Install dependencies
cd skills/playwright-worldarchitect
npm install

# Install Chromium browser
npx playwright install chromium

# Run a test
node run.js /tmp/my-test.js
```

## Usage

### Via Claude Code
When working with Claude Code, request browser automation tasks:
- "Test the campaign creation flow"
- "Take responsive screenshots of the game interface"
- "Verify character creation with all D&D classes"

Claude will automatically generate and execute Playwright scripts.

### Direct Execution
```bash
# Execute file
node run.js /tmp/test-script.js

# Execute inline code
node run.js "const browser = await chromium.launch(); ..."

# Execute via stdin
cat test.js | node run.js
```

## Helper Functions

See `lib/helpers.js` for:
- **Browser management**: `launchBrowser()`, `createContext()`, `createPage()`
- **Element interaction**: `safeClick()`, `safeType()`, `scrollPage()`
- **RPG testing**: `createCampaign()`, `createCharacter()`, `performDiceRoll()`
- **Visual testing**: `takeScreenshot()`, `takeResponsiveScreenshots()`

## Test Patterns

### Campaign Creation
```javascript
const { launchBrowser, createCampaign } = require('./lib/helpers.js');

const browser = await launchBrowser({ headless: false });
const page = await browser.newPage();
await page.goto('http://localhost:5000');

await createCampaign(page, {
  name: 'Dragon Quest',
  description: 'Epic adventure'
});

await browser.close();
```

### Visual Regression
```javascript
const { launchBrowser, takeResponsiveScreenshots } = require('./lib/helpers.js');

const browser = await launchBrowser();
const page = await browser.newPage();
await page.goto('http://localhost:5000/game');

// Desktop, tablet, mobile screenshots
await takeResponsiveScreenshots(page, 'game-interface');

await browser.close();
```

## Integration

This skill integrates with:
- `/testui` - Browser UI testing command
- `/teste` - E2E testing command
- `/smoke` - Smoke testing command
- `/tdd` - Test-driven development workflow

## Documentation

- **SKILL.md** - Complete skill reference and patterns
- **lib/helpers.js** - Helper function implementations
- **run.js** - Universal executor

## Architecture

```
skills/playwright-worldarchitect/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── lib/
│   └── helpers.js           # Helper functions
├── run.js                   # Universal executor
├── package.json             # Dependencies
├── SKILL.md                 # Skill documentation
└── README.md                # This file
```

## Requirements

- Node.js 18+
- Playwright 1.40.0+
- WorldArchitect.AI server running

## License

MIT
