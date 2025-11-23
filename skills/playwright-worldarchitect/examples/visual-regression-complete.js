/**
 * Complete Visual Regression Testing Example
 *
 * Demonstrates baseline capture, comparison, and promotion workflow.
 *
 * Usage:
 *   # Capture baselines
 *   cd skills/playwright-worldarchitect
 *   node run.js examples/visual-regression-complete.js --baseline
 *
 *   # Run comparison
 *   node run.js examples/visual-regression-complete.js
 */

const { chromium } = require('playwright');
const {
  runVisualRegression
} = require('../lib/visual-regression.js');

(async () => {
  const isBaselineMode = process.argv.includes('--baseline');

  console.log('🎨 Visual Regression Testing\n');
  console.log(`Mode: ${isBaselineMode ? 'BASELINE CAPTURE' : 'COMPARISON'}\n`);

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    // Test pages
    const testPages = [
      { url: 'http://localhost:5000/', name: 'home' },
      { url: 'http://localhost:5000/campaigns', name: 'campaigns' },
      { url: 'http://localhost:5000/login', name: 'login' }
    ];

    for (const testPage of testPages) {
      console.log(`\n📄 Testing: ${testPage.name} (${testPage.url})`);
      console.log('='.repeat(60));

      await page.goto(testPage.url);
      await page.waitForLoadState('networkidle');

      // Run visual regression workflow
      const results = await runVisualRegression(page, testPage.name, {
        captureBaseline: isBaselineMode,
        compare: !isBaselineMode,
        promoteOnPass: false
      });

      if (results.comparison) {
        const { passed, failed } = results.comparison;
        console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);

        if (failed > 0) {
          console.log('\n⚠️  Visual differences detected:');
          results.comparison.comparisons
            .filter(c => c.status === 'fail')
            .forEach(c => {
              console.log(`  ❌ ${c.viewport}: ${c.sizeDifference} difference (threshold: ${c.threshold})`);
              console.log(`     Baseline: ${c.baselineSize} bytes`);
              console.log(`     Current:  ${c.currentSize} bytes`);
              if (c.diffFile) {
                console.log(`     Diff:     ${c.diffFile}`);
              }
            });
        }
      }
    }

    // List all baselines
    console.log('\n' + '='.repeat(60));
    console.log('📁 Available Baselines');
    console.log('='.repeat(60));

    const baselines = listBaselines();
    if (baselines.length > 0) {
      baselines.forEach((baseline, i) => {
        console.log(`${i + 1}. ${baseline.name}`);
        console.log(`   Size: ${baseline.size} bytes`);
        console.log(`   Modified: ${baseline.modified.toISOString()}`);
      });
    } else {
      console.log('No baselines found. Run with --baseline to create them.');
    }

    // Instructions
    console.log('\n' + '='.repeat(60));
    console.log('📖 Next Steps');
    console.log('='.repeat(60));

    if (isBaselineMode) {
      console.log('\n✅ Baselines captured successfully!');
      console.log('\nTo compare against these baselines:');
      console.log('  node run.js examples/visual-regression-complete.js');
    } else {
      console.log('\nTo update baselines:');
      console.log('  node run.js examples/visual-regression-complete.js --baseline');
      console.log('\nTo clean up old screenshots:');
      console.log('  // In code: cleanup({ keepBaselines: true, keepCurrent: false })');
    }

  } catch (error) {
    console.error('\n❌ Visual regression failed:', error.message);
    throw error;
  } finally {
    await browser.close();
    console.log('\n🏁 Visual regression testing completed');
  }
})();
