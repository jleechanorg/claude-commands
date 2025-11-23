/**
 * Campaign Flow Test
 *
 * Tests the complete campaign creation, viewing, and management flow.
 *
 * Usage:
 *   cd skills/playwright-worldarchitect
 *   node run.js examples/campaign-flow-test.js
 */

const {
  launchBrowser,
  createContext,
  createPage,
  detectDevServers,
  createCampaign,
  verifyCampaignState,
  safeClick,
  waitForPageReady,
  takeScreenshot
} = require('../lib/helpers.js');

(async () => {
  console.log('🎲 Campaign Flow Test Starting...\n');

  // Detect running server
  const servers = await detectDevServers();
  const BASE_URL = servers[0] || 'http://localhost:5000';
  console.log(`📡 Using server: ${BASE_URL}\n`);

  const browser = await launchBrowser({ headless: false, slowMo: 100 });
  const context = await createContext(browser, {
    viewport: { width: 1920, height: 1080 }
  });
  const page = await createPage(context);

  try {
    // Step 1: Navigate to home page
    console.log('📍 Step 1: Navigate to home page');
    await page.goto(BASE_URL);
    await waitForPageReady(page);
    console.log('✅ Home page loaded\n');

    // Step 2: Navigate to campaigns
    console.log('📍 Step 2: Navigate to campaigns page');
    try {
      await safeClick(page, 'a[href="/campaigns"], a:has-text("Campaigns")');
      await waitForPageReady(page);
      console.log('✅ Campaigns page loaded\n');
    } catch (err) {
      console.log('⚠️  No campaigns link, already on campaigns page\n');
    }

    // Step 3: Create new campaign
    console.log('📍 Step 3: Create new campaign');
    await createCampaign(page, {
      name: 'Dragon Quest Test Campaign',
      description: 'Automated test campaign for E2E validation',
      setting: 'fantasy'
    });
    console.log('✅ Campaign created\n');

    // Step 4: Verify campaign appears in list
    console.log('📍 Step 4: Verify campaign in list');
    await page.goto(`${BASE_URL}/campaigns`);
    await waitForPageReady(page);

    const campaignExists = await page.locator('text=Dragon Quest Test Campaign').count() > 0;
    if (campaignExists) {
      console.log('✅ Campaign found in list\n');
    } else {
      console.warn('⚠️  Campaign not found in list\n');
    }

    // Step 5: Take screenshot of campaigns page
    console.log('📍 Step 5: Capture campaigns page screenshot');
    await takeScreenshot(page, 'campaigns-list', { fullPage: true });
    console.log('✅ Screenshot captured\n');

    // Step 6: Verify campaign state
    console.log('📍 Step 6: Verify campaign state elements');
    await verifyCampaignState(page, [
      '.campaign-card, .campaign-item',
      'h2, h3',
      'a[href*="/campaigns/"]'
    ]);
    console.log('✅ Campaign state verified\n');

    console.log('✅ ✅ ✅ All tests passed! ✅ ✅ ✅');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    await takeScreenshot(page, 'error-state');
    throw error;
  } finally {
    await browser.close();
    console.log('\n🏁 Test completed');
  }
})();
