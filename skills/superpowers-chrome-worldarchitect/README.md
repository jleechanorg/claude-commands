# WorldArchitect Superpowers Chrome Integration

Lightweight browser automation for WorldArchitect.AI using [obra/superpowers-chrome](https://github.com/obra/superpowers-chrome) - zero dependencies, direct Chrome DevTools Protocol access.

## Why Superpowers Chrome?

**Zero Dependencies**: No Playwright, Puppeteer, or Selenium required - just native Chrome CDP
**Persistent Sessions**: Connects to existing Chrome instances (not fresh browsers)
**Lightweight**: Minimal overhead, perfect for quick tests and debugging
**Cross-Platform**: Works on macOS, Linux, Windows automatically

## Quick Start

```bash
# Install superpowers-chrome
npm install github:obra/superpowers-chrome

# Start Chrome with remote debugging
./worldarchitect-chrome.sh start

# Run smoke tests
./worldarchitect-chrome.sh smoke http://localhost:5000

# Test campaign creation
./worldarchitect-chrome.sh campaign http://localhost:5000 "Dragon Quest"
```

## Installation

### Option 1: Via Claude Code Plugin (Recommended)
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers-chrome@superpowers-marketplace
```

### Option 2: Via NPM
```bash
cd skills/superpowers-chrome-worldarchitect
npm install github:obra/superpowers-chrome
```

### Option 3: MCP Mode (Claude Desktop)
Add to `claude_desktop_config.json`:
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

## WorldArchitect Helper Commands

The `worldarchitect-chrome.sh` wrapper provides RPG-specific automation:

### `start`
Start Chrome with remote debugging enabled

```bash
./worldarchitect-chrome.sh start
```

### `smoke [url]`
Run quick smoke tests across main pages

```bash
./worldarchitect-chrome.sh smoke http://localhost:5000
```

**Tests:**
- Home page loads
- Navigation exists
- Login page loads
- Campaigns page loads

### `campaign [url] [name]`
Test campaign creation flow

```bash
./worldarchitect-chrome.sh campaign http://localhost:5000 "Epic Quest"
```

**Steps:**
1. Navigate to campaigns page
2. Click "New Campaign"
3. Fill campaign form
4. Submit and verify
5. Take screenshot

### `character [tab] [name]`
Test character creation

```bash
./worldarchitect-chrome.sh character 0 "Gandalf the Grey"
```

### `dice [tab]`
Test dice rolling mechanics

```bash
./worldarchitect-chrome.sh dice 0
```

### `state [tab]`
Extract current game state

```bash
./worldarchitect-chrome.sh state 0
```

**Extracts:**
- Campaign name
- Character names
- Recent game log

### `screenshots [tab] [name]`
Capture responsive screenshots (desktop/tablet/mobile)

```bash
./worldarchitect-chrome.sh screenshots 0 game-view
```

**Generates:**
- `game-view-desktop.png` (1920x1080)
- `game-view-tablet.png` (768x1024)
- `game-view-mobile.png` (375x667)

### `session`
Show session directory contents

```bash
./worldarchitect-chrome.sh session
```

## Direct chrome-ws Usage

For advanced scenarios, use `chrome-ws` directly:

### 17 Available Commands

**Setup:**
```bash
chrome-ws start              # Launch Chrome with debugging
```

**Tab Management:**
```bash
chrome-ws tabs               # List all open tabs
chrome-ws new "URL"          # Create new tab
chrome-ws close 0            # Close tab by index
```

**Navigation:**
```bash
chrome-ws navigate 0 "URL"           # Go to URL
chrome-ws wait-for 0 "selector"      # Wait for element
chrome-ws wait-text 0 "text"         # Wait for text
```

**Interaction:**
```bash
chrome-ws click 0 "button.submit"           # Click element
chrome-ws fill 0 "input#name" "text"        # Fill input
chrome-ws select 0 "select#class" "Wizard"  # Select dropdown
```

**Data Extraction:**
```bash
chrome-ws eval 0 "document.title"                    # Execute JavaScript
chrome-ws extract 0 ".campaign-name"                 # Get element text
chrome-ws attr 0 "a.link" "href"                     # Get attribute
chrome-ws html 0 "main"                              # Get HTML content
```

**Export:**
```bash
chrome-ws screenshot 0 > screenshot.png    # Capture screenshot
chrome-ws markdown 0 > page.md             # Export as markdown
```

**Advanced:**
```bash
chrome-ws raw 0 "Page.navigate" '{"url":"http://example.com"}'  # Direct CDP
```

## MCP Mode: Single Tool Interface

When using MCP mode, you get a single `use_browser` tool with auto-capture:

```json
{
  "action": "navigate",
  "payload": "https://localhost:5000/campaigns"
}
```

**Auto-generates:**
- Full HTML snapshot
- Markdown content
- Visual screenshot
- Console logs
- Token-efficient DOM summary

### Example MCP Response
```
→ http://localhost:5000/campaigns (capture #001)
Size: 1920×1080
Snapshot: /tmp/chrome-session-123/001-navigate-456/
Resources: page.html, page.md, screenshot.png, console-log.txt
DOM:
  WorldArchitect Campaigns
  Interactive: 3 buttons, 2 inputs, 15 links
```

## When to Use Superpowers Chrome

✅ **Use Superpowers Chrome when:**
- Quick debugging and exploration
- Persistent browsing sessions needed
- Minimal dependencies preferred
- Connecting to existing Chrome instance
- Lightweight automation (< 10 steps)
- CLI-first workflows

❌ **Use Playwright instead when:**
- Fresh browser instances required
- Complex E2E test suites
- Visual regression testing needed
- Multi-browser testing (Firefox, WebKit)
- Need advanced helpers (retry logic, healing)
- Parallel test execution

## Architecture: Zero Dependencies

Superpowers Chrome achieves zero dependencies by:

1. **Native WebSocket Implementation**: No `ws` package needed
2. **Platform Detection**: Auto-finds Chrome on macOS/Linux/Windows
3. **Direct CDP**: Raw Chrome DevTools Protocol access
4. **Numeric Tab Indexing**: No URL management complexity

**Comparison:**
```
Playwright: ~200 npm packages
Puppeteer: ~50 npm packages
Superpowers Chrome: 0 npm packages (uses built-in Node.js APIs)
```

## Examples

### Example 1: Quick Campaign Test
```bash
# Start Chrome
./worldarchitect-chrome.sh start

# Test campaign creation
./worldarchitect-chrome.sh campaign http://localhost:5000 "Test Campaign"

# View results
./worldarchitect-chrome.sh session
```

### Example 2: Manual Testing with CLI
```bash
# Start Chrome and open page
chrome-ws start
chrome-ws new "http://localhost:5000/campaigns"

# Interact with page
chrome-ws fill 0 "#campaign-name" "Dragon Quest"
chrome-ws click 0 "button[type='submit']"

# Capture result
chrome-ws screenshot 0 > result.png
chrome-ws markdown 0 > result.md
```

### Example 3: MCP Mode (Claude Desktop)
```
User: "Test the campaign creation flow on localhost:5000"

Claude: I'll test the campaign creation flow using the browser automation tool.

[Uses use_browser tool with {"action": "navigate", "payload": "http://localhost:5000/campaigns"}]
[Auto-captures: HTML, markdown, screenshot]
[Uses use_browser tool with {"action": "click", "payload": "button:has-text('New Campaign')"}]
[...continues automation with auto-capture at each step...]
```

## Performance Benchmarks

| Operation | Playwright | Superpowers Chrome |
|-----------|------------|-------------------|
| Browser Launch | ~3-5s | ~1-2s (reuses existing) |
| Page Navigation | ~500ms | ~200ms |
| Element Click | ~100ms | ~50ms |
| Screenshot | ~500ms | ~300ms |
| Dependencies | 200+ packages | 0 packages |

## Troubleshooting

### Chrome doesn't start
```bash
# Check if Chrome is installed
which google-chrome chrome chromium-browser

# Manual start with debugging
google-chrome --remote-debugging-port=9222 --remote-allow-origins=* &
```

### Can't connect to Chrome
```bash
# Check if port is available
lsof -i :9222

# Use custom port
export CHROME_WS_PORT=9223
chrome-ws start
```

### Commands timeout
```bash
# Increase wait time in scripts
chrome-ws wait-for 0 "selector" # Default: 30s timeout
```

## Integration with Existing Commands

Superpowers Chrome complements existing WorldArchitect test commands:

- `/teste` - Mock E2E tests (use Superpowers Chrome for quick verification)
- `/smoke` - Smoke tests (add Superpowers Chrome for lightweight browser checks)
- `/playwright` - Full E2E tests (use for complex scenarios)

## Next Steps

1. Install superpowers-chrome: `npm install github:obra/superpowers-chrome`
2. Run smoke tests: `./worldarchitect-chrome.sh smoke`
3. Try campaign creation: `./worldarchitect-chrome.sh campaign`
4. Explore direct CLI: `chrome-ws help`
5. Read comparison guide: See `BROWSER_AUTOMATION_COMPARISON.md`

## Resources

- [obra/superpowers-chrome GitHub](https://github.com/obra/superpowers-chrome)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [WorldArchitect Playwright Skill](../playwright-worldarchitect/)
- [Browser Automation Comparison](../../docs/BROWSER_AUTOMATION_COMPARISON.md)

## License

MIT
