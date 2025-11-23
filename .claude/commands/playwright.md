---
description: Playwright browser automation testing for WorldArchitect.AI
type: tool
scope: project
execution_mode: immediate
---

# /playwright - Browser Automation Testing

## Purpose
Execute Playwright browser automation tests for WorldArchitect.AI. Tests real browser interactions for campaigns, characters, dice mechanics, and visual regression.

## Activation
User types `/playwright` or requests browser automation testing.

## Execution Workflow

### Phase 1: Detect Environment
1. Check if dev server is running (`detectDevServers()`)
2. Verify Playwright skill installation
3. Set up test environment variables

### Phase 2: Execute Tests
Based on user request:
- **Campaign testing**: Create/list/delete campaigns
- **Character testing**: Create characters, verify stats
- **Game mechanics**: Dice rolls, actions, combat
- **Visual regression**: Screenshot comparison across viewports
- **Navigation**: Link validation, page load testing
- **Forms**: Validation, submission, error handling

### Phase 3: Report Results
1. Display test results with ✅/❌ indicators
2. Show screenshots if captured
3. Report performance metrics
4. Suggest follow-up tests if failures detected

## Usage Examples

### Test Campaign Creation
```
User: /playwright test campaign creation flow
```

### Visual Regression Testing
```
User: /playwright take responsive screenshots of the game interface
```

### Full E2E Test Suite
```
User: /playwright run complete game flow test
```

## Test Scripts Location
- Custom scripts: `/tmp/playwright-test-*.js`
- Example scripts: `skills/playwright-worldarchitect/examples/`
- Test results: `/tmp/playwright-results/`

## Available Test Patterns

### 1. Campaign Flow Test
Tests complete campaign lifecycle:
- Navigate to campaigns page
- Create new campaign
- Verify campaign appears in list
- Open campaign
- Delete campaign

### 2. Character Creation Test
Tests character creation:
- Navigate to character creation
- Fill character form (name, class, race)
- Submit and verify character sheet
- Test stat calculations

### 3. Dice Mechanics Test
Tests dice rolling:
- Trigger various dice rolls (d20, d6, etc.)
- Verify roll results display
- Test advantage/disadvantage
- Verify modifiers apply correctly

### 4. Visual Regression Test
Tests UI consistency:
- Capture screenshots at desktop/tablet/mobile
- Compare against baselines
- Report visual differences

### 5. Authentication Flow Test
Tests login/logout:
- Navigate to login
- Fill credentials
- Verify redirect to dashboard
- Test logout

## Integration with Other Commands

- **`/teste`**: Use Playwright for browser verification after mock tests pass
- **`/smoke`**: Add Playwright browser checks to smoke test suite
- **`/tdd`**: Write Playwright tests first, then implement features

## Environment Variables
```bash
PLAYWRIGHT_HEADLESS=false    # Show browser (default)
PLAYWRIGHT_SLOW_MO=100       # Slow motion delay (ms)
PLAYWRIGHT_TIMEOUT=30000     # Default timeout (ms)
TESTING=true                 # Enable test mode
```

## Prerequisites

### Install Playwright Skill
```bash
cd skills/playwright-worldarchitect
npm install
npx playwright install chromium
```

### Start Dev Server
```bash
cd mvp_site
python main.py  # Runs on http://localhost:5000
```

## Expected Output

### Success
```
🎭 WorldArchitect Playwright Test Runner
📡 Server detected: http://localhost:5000
✅ Playwright installed

🚀 Running test: Campaign Creation Flow

✅ Navigated to campaigns page
✅ Clicked "New Campaign"
✅ Filled campaign form
✅ Campaign created successfully
✅ Campaign appears in list

📊 Test Results: 5/5 passed
⏱️  Duration: 8.3s
```

### Failure
```
🎭 WorldArchitect Playwright Test Runner
📡 Server detected: http://localhost:5000
✅ Playwright installed

🚀 Running test: Campaign Creation Flow

✅ Navigated to campaigns page
✅ Clicked "New Campaign"
❌ Failed to fill campaign form
   Error: Element not found: #campaign-name
   Screenshot: /tmp/screenshot-error-2025-01-15T10-30-45.png

📊 Test Results: 2/5 passed
⏱️  Duration: 4.2s
```

## Troubleshooting

### Browser doesn't launch
```bash
cd skills/playwright-worldarchitect
npx playwright install chromium
```

### Server not detected
```bash
# Start server manually
cd mvp_site
python main.py &

# Or specify URL explicitly
export BASE_URL=http://localhost:5000
```

### Tests timeout
```bash
# Increase timeout
export PLAYWRIGHT_TIMEOUT=60000
```

## Advanced Usage

### Custom Test Script
```javascript
// /tmp/custom-campaign-test.js
const { launchBrowser, createCampaign } = require('./lib/helpers.js');

const browser = await launchBrowser({ headless: false });
const page = await browser.newPage();

await page.goto('http://localhost:5000');
await createCampaign(page, {
  name: 'My Custom Campaign',
  description: 'Testing advanced features'
});

console.log('✅ Custom test completed');
await browser.close();
```

Execute:
```bash
cd skills/playwright-worldarchitect
node run.js /tmp/custom-campaign-test.js
```

## Performance Benchmarks

- Campaign creation test: ~5-8s
- Character creation test: ~6-10s
- Visual regression (3 viewports): ~8-12s
- Full E2E suite: ~30-45s
- Headless mode: ~40% faster

## Security Notes

- Uses `X-Test-Bypass-Auth` header for automated tests
- Test data isolated to test user accounts
- Screenshots saved to `/tmp/` (not committed)
- Never test against production without explicit approval

## Next Steps

1. Run your first test: `/playwright test campaign creation`
2. Add visual baselines: `/playwright capture baseline screenshots`
3. Create custom test scripts in `/tmp/`
4. Integrate with CI/CD pipeline
5. Expand test coverage to all game features

---

**Skill Path**: `skills/playwright-worldarchitect/`
**Documentation**: `skills/playwright-worldarchitect/SKILL.md`
**Helper Functions**: `skills/playwright-worldarchitect/lib/helpers.js`
