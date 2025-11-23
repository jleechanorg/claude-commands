/**
 * Visual Regression Test
 *
 * Captures screenshots across multiple viewports for visual regression testing.
 *
 * Usage:
 *   cd skills/playwright-worldarchitect
 *   node run.js examples/visual-regression-test.js
 */

const {
  launchBrowser,
  detectDevServers,
  takeResponsiveScreenshots,
  takeScreenshot,
  waitForPageReady
} = require('../lib/helpers.js');

(async () => {
  console.log('📸 Visual Regression Test Starting...\n');

  // Detect running server
  const servers = await detectDevServers();
  const BASE_URL = servers[0] || 'http://localhost:5000';
  console.log(`📡 Using server: ${BASE_URL}\n`);

  const browser = await launchBrowser({ headless: false });
  const page = await browser.newPage();

  try {
    // Test pages to capture
    const pages = [
      { path: '/', name: 'home' },
      { path: '/campaigns', name: 'campaigns-list' },
      { path: '/login', name: 'login' }
    ];

    for (const testPage of pages) {
      console.log(`📍 Testing page: ${testPage.path}`);

      await page.goto(`${BASE_URL}${testPage.path}`);
      await waitForPageReady(page);

      // Capture responsive screenshots
      console.log(`📸 Capturing responsive screenshots for ${testPage.name}...`);
      await takeResponsiveScreenshots(page, testPage.name);

      console.log(`✅ ${testPage.name} screenshots captured\n`);
    }

    // Capture specific game interface elements if available
    console.log('📍 Checking for game interface elements...');

    const gameElements = [
      { selector: '.dice-roller', name: 'dice-roller' },
      { selector: '.character-sheet', name: 'character-sheet' },
      { selector: '.game-log', name: 'game-log' }
    ];

    for (const element of gameElements) {
      try {
        const elementHandle = await page.$(element.selector);
        if (elementHandle) {
          console.log(`📸 Capturing ${element.name}...`);
          await elementHandle.screenshot({
            path: `/tmp/screenshot-${element.name}-${Date.now()}.png`
          });
          console.log(`✅ ${element.name} captured`);
        }
      } catch (err) {
        console.log(`⚠️  ${element.name} not found on this page`);
      }
    }

    console.log('\n✅ ✅ ✅ Visual regression test completed! ✅ ✅ ✅');
    console.log('📁 Screenshots saved to /tmp/screenshot-*.png');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    await takeScreenshot(page, 'visual-test-error');
    throw error;
  } finally {
    await browser.close();
    console.log('\n🏁 Test completed');
  }
})();
