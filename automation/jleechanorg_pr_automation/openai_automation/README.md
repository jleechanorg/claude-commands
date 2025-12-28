# OpenAI Automation Scripts

Playwright-based automation scripts for OpenAI Codex and ChatGPT that connect to existing browser sessions to avoid detection.

## Overview

This directory contains scripts for:

1. **Codex GitHub Mentions** - Automate finding and updating "GitHub mention" tasks in Codex
2. **Oracle CLI** - Ask GPT-5 Pro questions via browser (no API key needed)
3. **Chrome Debug Mode** - Helper to start Chrome with remote debugging

## Key Features

- ✅ **Non-Detectable** - Uses Chrome DevTools Protocol (CDP) instead of WebDriver
- ✅ **Reuses Browser** - Connects to your existing Chrome session (with cookies/login)
- ✅ **No Headless Mode** - Runs in normal browser mode to avoid detection
- ✅ **Real User Profile** - Uses your actual Chrome profile with extensions

---

## Setup

### 1. Install Dependencies

```bash
# Install Playwright for Python
pip install playwright

# Install Playwright browsers
playwright install chromium
```

### 2. Start Chrome in Debug Mode

```bash
# Start Chrome with remote debugging enabled
./scripts/openai_automation/start_chrome_debug.sh

# Or with custom port
./scripts/openai_automation/start_chrome_debug.sh 9223
```

This will:
- Start Chrome with remote debugging on port 9222
- Open ChatGPT in a new window
- Display connection details

**Important:** Log in to OpenAI/ChatGPT in this browser window!

Tip: If you run `jleechanorg-pr-monitor --codex-update`, the monitor can auto-start
Chrome when CDP is unavailable. Configure with `CODEX_CDP_AUTO_START`,
`CODEX_CDP_HOST`, `CODEX_CDP_PORT`, and `CODEX_CDP_USER_DATA_DIR`.

---

## Usage

### Codex GitHub Mentions Automation

Finds all "github mention" tasks in Codex and clicks "Update PR" on each one.

```bash
# Make sure Chrome is running in debug mode first!
./scripts/openai_automation/start_chrome_debug.sh

# Run the automation
python3 scripts/openai_automation/codex_github_mentions.py

# With custom CDP port
python3 scripts/openai_automation/codex_github_mentions.py --cdp-port 9223

# Verbose mode
python3 scripts/openai_automation/codex_github_mentions.py --verbose
```

**What it does:**

1. Connects to your existing Chrome browser
2. Checks if you're logged into OpenAI (prompts if not)
3. Navigates to Codex
4. Finds all tasks containing "github mention"
5. Opens each task and clicks "Update PR"
6. Reports results

---

### Oracle CLI (GPT-5 Pro)

Ask questions to GPT-5 Pro via browser automation (no API key needed).

```bash
# Ask a single question
python3 scripts/openai_automation/oracle_cli.py "What is the capital of France?"

# Interactive mode (multiple questions)
python3 scripts/openai_automation/oracle_cli.py --interactive

# Use specific model
python3 scripts/openai_automation/oracle_cli.py "Explain quantum computing" --model gpt-4

# Use existing browser (requires start_chrome_debug.sh)
python3 scripts/openai_automation/oracle_cli.py "Question" --use-existing-browser

# With timeout
python3 scripts/openai_automation/oracle_cli.py "Complex question" --timeout 120
```

**Interactive Mode:**

```bash
$ python3 scripts/openai_automation/oracle_cli.py --interactive

🎙️  Oracle Interactive Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type your questions (or 'exit' to quit)

❓ Your question: What is the meaning of life?

💡 Answer:
[GPT-5 Pro's response here...]

❓ Your question: exit
👋 Goodbye!
```

---

## How It Works

### Non-Detectable Automation

These scripts avoid detection by:

1. **Chrome DevTools Protocol (CDP)** - Connects via CDP instead of WebDriver
   - No `navigator.webdriver` flag
   - Appears as regular browser to websites

2. **Existing Browser Session** - Reuses your logged-in Chrome instance
   - Preserves cookies and login state
   - Uses real user profile with extensions

3. **No Headless Mode** - Runs in visible browser window
   - Headless mode is easily detectable
   - Visible mode appears more natural

4. **Disable Automation Flags**
   ```bash
   --disable-blink-features=AutomationControlled
   ```

### Architecture

```
┌─────────────────────┐
│   Python Script     │
│  (Playwright)       │
└──────────┬──────────┘
           │ CDP (WebSocket)
           │
┌──────────▼──────────┐
│   Chrome Browser    │
│  (Debug Mode)       │
│                     │
│  Port: 9222         │
│  Your Profile       │
│  Logged In          │
└─────────────────────┘
```

---

## Configuration

### Chrome Debug Port

Default: 9222

To change:

```bash
# Start Chrome on different port
./scripts/openai_automation/start_chrome_debug.sh 9223

# Connect to that port
python3 scripts/openai_automation/codex_github_mentions.py --cdp-port 9223
```

### Selectors (Codex Script)

The Codex automation uses CSS selectors to find tasks and buttons. You may need to update these based on the actual UI:

In `codex_github_mentions.py`:

```python
# Find tasks with "GitHub Mention:" text
tasks = await self.page.locator('a:has-text("GitHub Mention:")').all()

# Find "Update branch" button
update_btn = self.page.locator('button:has-text("Update branch")').first
```

### Model Selection (Oracle)

Default: `gpt-5-pro`

Supported:
- `gpt-5-pro`
- `gpt-4`
- `gpt-4-turbo`
- Other models available in ChatGPT

```bash
python3 scripts/openai_automation/oracle_cli.py "Question" --model gpt-4-turbo
```

---

## Troubleshooting

### Chrome Not Starting

**Error:** "Could not find Chrome or Chromium"

**Solution:**
```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt install google-chrome-stable
```

### Port Already in Use

**Error:** "Port 9222 is already in use"

**Solution:**
```bash
# Kill existing Chrome debug instance
pkill -f 'remote-debugging-port=9222'

# Or use different port
./scripts/openai_automation/start_chrome_debug.sh 9223
```

### Cannot Connect to Browser

**Error:** "Failed to connect to Chrome"

**Solution:**

1. Make sure Chrome is running in debug mode
2. Check if port is open:
   ```bash
   lsof -i :9222
   ```
3. Verify CDP endpoint:
   ```bash
   curl http://localhost:9222/json/version
   ```

### Not Logged Into OpenAI

**Symptom:** Script asks you to log in manually

**Solution:**

1. Log in to OpenAI/ChatGPT in the Chrome window
2. Wait for login to complete
3. Press Enter in the terminal to continue

### Tasks Not Found

**Error:** "No tasks found with 'github mention'"

**Solution:**

1. The selectors may need updating for the current UI
2. Check the actual HTML structure in DevTools
3. Update the selectors in the script
4. Or manually adjust the search term

---

## Advanced Usage

### Using with Your Own Chrome Profile

By default, the script starts a new Chrome instance. To use your existing profile:

1. **Find your Chrome profile path:**
   ```bash
   # macOS
   ~/Library/Application Support/Google/Chrome/Default

   # Linux
   ~/.config/google-chrome/default
   ```

2. **Edit `start_chrome_debug.sh`:**
   ```bash
   # Uncomment this line
   "--user-data-dir=$USER_DATA_DIR"
   ```

3. **Or set custom profile:**
   ```bash
   export USER_DATA_DIR="$HOME/Library/Application Support/Google/Chrome/Default"
   ./scripts/openai_automation/start_chrome_debug.sh
   ```

### Headless Mode (Not Recommended)

While headless mode may be detected, you can try it:

```python
# In codex_github_mentions.py or oracle_cli.py
automation = CodexGitHubMentionsAutomation(
    cdp_url=cdp_url,
    headless=True  # Enable headless
)
```

### Running on Remote Server

1. **Forward CDP port via SSH:**
   ```bash
   ssh -L 9222:localhost:9222 user@remote-server
   ```

2. **Run automation locally:**
   ```bash
   python3 scripts/openai_automation/codex_github_mentions.py
   ```

---

## Security Considerations

⚠️ **Important Security Notes:**

1. **Credentials** - Scripts use your logged-in session
   - Don't share CDP port externally
   - Don't run on untrusted networks

2. **CDP Access** - Anyone with access to CDP port can control your browser
   - Use localhost only (not 0.0.0.0)
   - Kill Chrome debug instance when done

3. **Automation Detection** - While designed to avoid detection, no guarantee
   - OpenAI may update detection methods
   - Use responsibly and within ToS

---

## Comparison with Other Approaches

| Approach | Detection Risk | Setup | Speed |
|----------|---------------|-------|-------|
| **CDP (This)** | Low | Medium | Fast |
| WebDriver | High | Easy | Medium |
| Headless | High | Easy | Fast |
| API | None | Easy | Fastest |
| Manual | None | None | Slowest |

---

## References

- [Playwright Documentation](https://playwright.dev/python/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Stealth Automation Guide](https://github.com/berstend/puppeteer-extra/tree/master/packages/puppeteer-extra-plugin-stealth)

---

## License

MIT - See root project LICENSE

---

## Contributing

1. Test selectors against latest OpenAI UI
2. Add error handling for edge cases
3. Improve detection avoidance techniques
4. Add support for more models/features

---

## Credits

Inspired by:
- Oracle tool's browser-based approach
- Playwright's CDP connection features
- puppeteer-extra-stealth techniques
