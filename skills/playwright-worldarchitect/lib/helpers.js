/**
 * WorldArchitect.AI Playwright Helper Functions
 *
 * Browser automation utilities for RPG testing:
 * - Campaign creation and management
 * - Character creation and interaction
 * - Dice rolling and game mechanics
 * - Visual regression testing for game UI
 */

const { chromium, firefox, webkit } = require('playwright');

// ============================================
// CORE BROWSER & PAGE MANAGEMENT
// ============================================

/**
 * Launch browser with configurable options
 * @param {Object} options - Browser launch options
 * @returns {Promise<Browser>}
 */
async function launchBrowser(options = {}) {
  const {
    headless = false,
    slowMo = 100,
    browserType = 'chromium',
    args = []
  } = options;

  const browserTypes = { chromium, firefox, webkit };
  const browser = browserTypes[browserType] || chromium;

  return await browser.launch({
    headless,
    slowMo,
    args: ['--no-sandbox', '--disable-setuid-sandbox', ...args]
  });
}

/**
 * Create browser context with options
 * @param {Browser} browser - Browser instance
 * @param {Object} options - Context options
 * @returns {Promise<BrowserContext>}
 */
async function createContext(browser, options = {}) {
  const {
    viewport = { width: 1920, height: 1080 },
    userAgent = null,
    geolocation = null,
    locale = 'en-US',
    timezone = 'America/New_York'
  } = options;

  return await browser.newContext({
    viewport,
    userAgent,
    geolocation,
    locale,
    timezoneId: timezone
  });
}

/**
 * Create new page
 * @param {BrowserContext} context - Browser context
 * @param {Object} options - Page options
 * @returns {Promise<Page>}
 */
async function createPage(context, options = {}) {
  const { viewport = null, extraHTTPHeaders = {} } = options;

  const page = await context.newPage();

  if (viewport) {
    await page.setViewportSize(viewport);
  }

  if (Object.keys(extraHTTPHeaders).length > 0) {
    await page.setExtraHTTPHeaders(extraHTTPHeaders);
  }

  return page;
}

/**
 * Wait for page to be fully loaded
 * @param {Page} page - Playwright page
 * @param {Object} options - Wait options
 */
async function waitForPageReady(page, options = {}) {
  const { waitUntil = 'networkidle', timeout = 30000, selector = null } = options;

  try {
    if (selector) {
      await page.waitForSelector(selector, { timeout });
    } else {
      await page.waitForLoadState(waitUntil, { timeout });
    }
  } catch (err) {
    console.warn(`⚠️  Page ready timeout (${timeout}ms), continuing anyway`);
  }
}

// ============================================
// ELEMENT INTERACTION PATTERNS
// ============================================

/**
 * Safe click with retry logic
 * @param {Page} page - Playwright page
 * @param {string} selector - Element selector
 * @param {Object} options - Click options
 */
async function safeClick(page, selector, options = {}) {
  const { retries = 3, delay = 1000 } = options;

  for (let i = 0; i < retries; i++) {
    try {
      await page.waitForSelector(selector, { state: 'visible', timeout: 5000 });
      await page.click(selector);
      console.log(`✅ Clicked: ${selector}`);
      return true;
    } catch (err) {
      console.warn(`⚠️  Click attempt ${i + 1}/${retries} failed for ${selector}`);
      if (i < retries - 1) {
        await page.waitForTimeout(delay);
      }
    }
  }

  throw new Error(`❌ Failed to click ${selector} after ${retries} attempts`);
}

/**
 * Safe type with field clearing
 * @param {Page} page - Playwright page
 * @param {string} selector - Input selector
 * @param {string} text - Text to type
 * @param {Object} options - Type options
 */
async function safeType(page, selector, text, options = {}) {
  const { clear = true, slow = false } = options;

  await page.waitForSelector(selector, { state: 'visible', timeout: 5000 });

  if (clear) {
    await page.fill(selector, '');
  }

  if (slow) {
    await page.type(selector, text, { delay: 50 });
  } else {
    await page.fill(selector, text);
  }

  console.log(`✅ Typed into ${selector}: ${text}`);
}

/**
 * Extract text from multiple elements
 * @param {Page} page - Playwright page
 * @param {string} selector - Element selector
 * @returns {Promise<Array<string>>}
 */
async function extractTexts(page, selector) {
  const elements = await page.$$(selector);
  const texts = await Promise.all(
    elements.map(el => el.textContent())
  );
  return texts.filter(t => t && t.trim().length > 0);
}

/**
 * Scroll page in specified direction
 * @param {Page} page - Playwright page
 * @param {string} direction - Scroll direction (down, up, top, bottom)
 * @param {number} distance - Scroll distance in pixels
 */
async function scrollPage(page, direction = 'down', distance = 500) {
  const scrollMap = {
    down: `window.scrollBy(0, ${distance})`,
    up: `window.scrollBy(0, -${distance})`,
    top: 'window.scrollTo(0, 0)',
    bottom: 'window.scrollTo(0, document.body.scrollHeight)'
  };

  await page.evaluate(scrollMap[direction] || scrollMap.down);
  await page.waitForTimeout(500);
}

// ============================================
// DATA EXTRACTION & UTILITIES
// ============================================

/**
 * Extract table data into structured format
 * @param {Page} page - Playwright page
 * @param {string} tableSelector - Table selector
 * @returns {Promise<Array<Object>>}
 */
async function extractTableData(page, tableSelector) {
  return await page.evaluate((selector) => {
    const table = document.querySelector(selector);
    if (!table) return [];

    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
    const rows = Array.from(table.querySelectorAll('tbody tr'));

    return rows.map(row => {
      const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
      const rowData = {};
      headers.forEach((header, i) => {
        rowData[header] = cells[i] || '';
      });
      return rowData;
    });
  }, tableSelector);
}

/**
 * Handle cookie consent banners
 * @param {Page} page - Playwright page
 */
async function handleCookieBanner(page) {
  const selectors = [
    'button:has-text("Accept")',
    'button:has-text("Accept All")',
    'button:has-text("I Agree")',
    '#accept-cookies',
    '.cookie-accept'
  ];

  for (const selector of selectors) {
    try {
      const button = await page.$(selector);
      if (button) {
        await button.click();
        console.log('✅ Cookie banner dismissed');
        return;
      }
    } catch (err) {
      // Continue to next selector
    }
  }
}

/**
 * Take screenshot with timestamp
 * @param {Page} page - Playwright page
 * @param {string} name - Screenshot name
 * @param {Object} options - Screenshot options
 */
async function takeScreenshot(page, name, options = {}) {
  const { fullPage = true, path: customPath = null } = options;
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = customPath || `/tmp/screenshot-${name}-${timestamp}.png`;

  await page.screenshot({ path: filename, fullPage });
  console.log(`📸 Screenshot saved: ${filename}`);
  return filename;
}

// ============================================
// ADVANCED AUTOMATION
// ============================================

/**
 * Authenticate user with flexible selector patterns
 * @param {Page} page - Playwright page
 * @param {Object} credentials - Login credentials
 * @param {Object} selectors - Form selectors
 */
async function authenticate(page, credentials, selectors = {}) {
  const {
    usernameSelector = 'input[name="username"]',
    passwordSelector = 'input[name="password"]',
    submitSelector = 'button[type="submit"]'
  } = selectors;

  await safeType(page, usernameSelector, credentials.username);
  await safeType(page, passwordSelector, credentials.password);
  await safeClick(page, submitSelector);
  await waitForPageReady(page);

  console.log('✅ Authentication completed');
}

/**
 * Retry function with exponential backoff
 * @param {Function} fn - Function to retry
 * @param {Object} options - Retry options
 */
async function retryWithBackoff(fn, options = {}) {
  const { maxRetries = 3, initialDelay = 1000, maxDelay = 10000 } = options;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === maxRetries - 1) throw err;

      const delay = Math.min(initialDelay * Math.pow(2, i), maxDelay);
      console.warn(`⚠️  Attempt ${i + 1} failed, retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

/**
 * Detect running development servers
 * @returns {Promise<Array<string>>}
 */
async function detectDevServers() {
  const ports = [3000, 5000, 8000, 8080, 5173, 4200, 8081];
  const servers = [];

  for (const port of ports) {
    try {
      const http = require('http');
      await new Promise((resolve, reject) => {
        const req = http.request({
          hostname: 'localhost',
          port,
          method: 'HEAD',
          timeout: 1000
        }, (res) => {
          if (res.statusCode) {
            servers.push(`http://localhost:${port}`);
          }
          resolve();
        });
        req.on('error', resolve);
        req.on('timeout', () => {
          req.destroy();
          resolve();
        });
        req.end();
      });
    } catch (err) {
      // Server not running on this port
    }
  }

  return servers;
}

// ============================================
// WORLDARCHITECT RPG-SPECIFIC HELPERS
// ============================================

/**
 * Create a new campaign
 * @param {Page} page - Playwright page
 * @param {Object} campaignData - Campaign configuration
 */
async function createCampaign(page, campaignData = {}) {
  const {
    name = 'Test Campaign',
    description = 'Automated test campaign'
  } = campaignData;

  console.log(`🎲 Creating campaign: ${name}`);

  // Navigate to campaign creation
  await safeClick(page, 'a[href="/campaigns/new"], button:has-text("New Campaign")');
  await waitForPageReady(page);

  // Fill campaign form
  await safeType(page, 'input[name="campaign_name"], #campaign-name', name);

  const descField = await page.$('textarea[name="description"], #campaign-description');
  if (descField) {
    await safeType(page, 'textarea[name="description"], #campaign-description', description);
  }

  // Submit form
  await safeClick(page, 'button[type="submit"], button:has-text("Create")');
  await waitForPageReady(page, { waitUntil: 'networkidle' });

  console.log('✅ Campaign created successfully');
}

/**
 * Create a new character
 * @param {Page} page - Playwright page
 * @param {Object} characterData - Character configuration
 */
async function createCharacter(page, characterData = {}) {
  const {
    name = 'Test Hero',
    characterClass = 'Fighter',
    race = 'Human'
  } = characterData;

  console.log(`⚔️  Creating character: ${name}`);

  await safeClick(page, 'button:has-text("New Character"), a[href*="character"]');
  await waitForPageReady(page);

  await safeType(page, 'input[name="character_name"], #character-name', name);

  // Select class and race if dropdowns exist
  const classSelect = await page.$('select[name="class"], #character-class');
  if (classSelect) {
    await page.selectOption('select[name="class"], #character-class', characterClass);
  }

  const raceSelect = await page.$('select[name="race"], #character-race');
  if (raceSelect) {
    await page.selectOption('select[name="race"], #character-race', race);
  }

  await safeClick(page, 'button[type="submit"], button:has-text("Create Character")');
  await waitForPageReady(page);

  console.log('✅ Character created successfully');
}

/**
 * Perform a dice roll action
 * @param {Page} page - Playwright page
 * @param {string} actionType - Type of action (attack, skill, save)
 */
async function performDiceRoll(page, actionType = 'attack') {
  console.log(`🎲 Rolling dice for: ${actionType}`);

  const buttonSelectors = {
    attack: 'button:has-text("Attack"), button.attack-roll',
    skill: 'button:has-text("Skill Check"), button.skill-roll',
    save: 'button:has-text("Saving Throw"), button.save-roll'
  };

  const selector = buttonSelectors[actionType] || buttonSelectors.attack;
  await safeClick(page, selector);
  await page.waitForTimeout(1000); // Wait for animation

  // Extract roll result if visible
  const resultSelector = '.dice-result, .roll-result, #roll-result';
  const result = await page.$(resultSelector);
  if (result) {
    const resultText = await result.textContent();
    console.log(`✅ Roll result: ${resultText}`);
    return resultText;
  }

  console.log('✅ Dice roll completed');
  return null;
}

/**
 * Send a game action/message
 * @param {Page} page - Playwright page
 * @param {string} action - Action text to send
 */
async function sendGameAction(page, action) {
  console.log(`💬 Sending action: ${action}`);

  const inputSelector = 'textarea[name="action"], input[name="action"], #action-input, .action-input';
  await safeType(page, inputSelector, action);

  const submitSelector = 'button[type="submit"], button:has-text("Send"), button:has-text("Submit Action")';
  await safeClick(page, submitSelector);

  // Wait for response
  await page.waitForTimeout(2000);
  console.log('✅ Action sent, waiting for response');
}

/**
 * Verify campaign state elements
 * @param {Page} page - Playwright page
 * @param {Array<string>} expectedElements - Elements to verify
 */
async function verifyCampaignState(page, expectedElements = []) {
  console.log('🔍 Verifying campaign state...');

  const defaultElements = [
    '.campaign-name, #campaign-name',
    '.character-list, #character-list',
    '.game-log, #game-log'
  ];

  const elementsToCheck = expectedElements.length > 0 ? expectedElements : defaultElements;

  for (const selector of elementsToCheck) {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      console.log(`✅ Found: ${selector}`);
    } catch (err) {
      console.warn(`⚠️  Missing: ${selector}`);
    }
  }
}

/**
 * Take multi-viewport screenshots for responsive testing
 * @param {Page} page - Playwright page
 * @param {string} name - Base name for screenshots
 */
async function takeResponsiveScreenshots(page, name) {
  const viewports = [
    { width: 1920, height: 1080, name: 'desktop' },
    { width: 768, height: 1024, name: 'tablet' },
    { width: 375, height: 667, name: 'mobile' }
  ];

  const screenshots = [];

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.waitForTimeout(500); // Let layout adjust

    const filename = await takeScreenshot(page, `${name}-${viewport.name}`);
    screenshots.push({ viewport: viewport.name, file: filename });
  }

  console.log(`✅ Captured ${screenshots.length} responsive screenshots`);
  return screenshots;
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
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
};
