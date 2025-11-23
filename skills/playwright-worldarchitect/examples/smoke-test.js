/**
 * Smoke Test
 *
 * Quick validation that the application is running and core pages load.
 *
 * Usage:
 *   cd skills/playwright-worldarchitect
 *   node run.js examples/smoke-test.js
 */

const {
  launchBrowser,
  detectDevServers,
  waitForPageReady
} = require('../lib/helpers.js');

(async () => {
  console.log('💨 Smoke Test Starting...\n');

  // Detect running server
  const servers = await detectDevServers();
  if (servers.length === 0) {
    console.error('❌ No dev server detected. Please start the server first.');
    process.exit(1);
  }

  const BASE_URL = servers[0];
  console.log(`📡 Server detected: ${BASE_URL}\n`);

  const browser = await launchBrowser({ headless: false, slowMo: 50 });
  const page = await browser.newPage();

  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };

  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  /**
   * Test helper function
   */
  async function test(name, testFn) {
    console.log(`🧪 Test: ${name}`);
    try {
      await testFn();
      console.log(`✅ PASS: ${name}\n`);
      results.passed++;
      results.tests.push({ name, status: 'PASS' });
    } catch (error) {
      console.error(`❌ FAIL: ${name}`);
      console.error(`   Error: ${error.message}\n`);
      results.failed++;
      results.tests.push({ name, status: 'FAIL', error: error.message });
    }
  }

  try {
    // Test 1: Home page loads
    await test('Home page loads', async () => {
      await page.goto(BASE_URL);
      await waitForPageReady(page);
      const title = await page.title();
      if (!title) throw new Error('Page title is empty');
    });

    // Test 2: Navigation exists
    await test('Navigation menu exists', async () => {
      const nav = await page.$('nav, .navbar, header');
      if (!nav) throw new Error('No navigation found');
    });

    // Test 3: Login page loads
    await test('Login page loads', async () => {
      await page.goto(`${BASE_URL}/login`);
      await waitForPageReady(page);
      const loginForm = await page.$('form, input[type="password"]');
      if (!loginForm) throw new Error('No login form found');
    });

    // Test 4: Campaigns page loads
    await test('Campaigns page loads', async () => {
      await page.goto(`${BASE_URL}/campaigns`);
      await waitForPageReady(page);
      const pageLoaded = await page.$('body');
      if (!pageLoaded) throw new Error('Page not loaded');
    });

    // Test 5: Static assets load
    await test('Static assets load (CSS/JS)', async () => {
      await page.goto(BASE_URL);
      const styles = await page.$$('link[rel="stylesheet"]');
      const scripts = await page.$$('script[src]');
      if (styles.length === 0 && scripts.length === 0) {
        throw new Error('No static assets found');
      }
    });

    // Test 6: No console errors
    await test('No critical console errors', async () => {
      await page.goto(BASE_URL);
      await waitForPageReady(page);

      // Filter out common benign errors
      const criticalErrors = consoleErrors.filter(err =>
        !err.includes('favicon') &&
        !err.includes('DevTools')
      );

      if (criticalErrors.length > 0) {
        throw new Error(`Console errors: ${criticalErrors.join(', ')}`);
      }
    });

  } catch (error) {
    console.error('\n❌ Smoke test suite failed:', error.message);
  } finally {
    await browser.close();

    // Print summary
    console.log('\n' + '='.repeat(50));
    console.log('📊 Smoke Test Results');
    console.log('='.repeat(50));
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`📈 Total: ${results.passed + results.failed}`);
    console.log('='.repeat(50));

    results.tests.forEach(test => {
      const icon = test.status === 'PASS' ? '✅' : '❌';
      console.log(`${icon} ${test.name}`);
      if (test.error) {
        console.log(`   └─ ${test.error}`);
      }
    });

    console.log('\n🏁 Smoke test completed');

    // Exit with error code if any tests failed
    if (results.failed > 0) {
      process.exit(1);
    }
  }
})();
