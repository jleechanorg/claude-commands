/**
 * Advanced DOM Optimization Example
 *
 * Demonstrates FocusAgent and D2Snap principles for 50-80% token reduction
 * while maintaining performance.
 *
 * Usage:
 *   cd skills/playwright-worldarchitect
 *   node run.js examples/advanced-dom-optimization.js
 */

const { chromium } = require('playwright');
const {
  getFocusedDOM,
  getAccessibilitySnapshot,
  observeAction,
  filterSensitiveData,
  getInteractiveElements
} = require('../lib/dom-optimizer.js');

(async () => {
  console.log('🔬 Advanced DOM Optimization Demo\n');

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    // Navigate to a page
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');

    console.log('📊 Comparing Optimization Techniques:\n');

    // Technique 1: Full DOM (baseline)
    console.log('1️⃣  Full DOM Snapshot (Baseline)');
    const fullDOM = await page.evaluate(() => {
      function serializeDOM(element) {
        return {
          tag: element.tagName,
          id: element.id,
          classes: Array.from(element.classList),
          text: element.textContent,
          children: Array.from(element.children).map(serializeDOM)
        };
      }
      return serializeDOM(document.body);
    });
    const fullSize = JSON.stringify(fullDOM).length;
    const fullTokens = Math.ceil(fullSize / 4);
    console.log(`   Size: ${fullSize} chars (~${fullTokens} tokens)\n`);

    // Technique 2: FocusAgent-inspired focused DOM
    console.log('2️⃣  FocusAgent-Inspired Focused DOM');
    const focusedDOM = await getFocusedDOM(page, {
      maxDepth: 3,
      includeHidden: false,
      includeStyles: false,
      focusSelectors: ['main', 'article', '[role="main"]', '.content']
    });
    const focusedSize = JSON.stringify(focusedDOM).length;
    const focusedTokens = Math.ceil(focusedSize / 4);
    const reduction = ((fullSize - focusedSize) / fullSize * 100).toFixed(2);
    console.log(`   Size: ${focusedSize} chars (~${focusedTokens} tokens)`);
    console.log(`   ✅ Reduction: ${reduction}% (${fullTokens - focusedTokens} tokens saved)\n`);

    // Technique 3: Accessibility tree (semantic information)
    console.log('3️⃣  Accessibility Tree (Semantic DOM)');
    const a11yTree = await getAccessibilitySnapshot(page);
    if (a11yTree) {
      const a11ySize = JSON.stringify(a11yTree).length;
      const a11yTokens = Math.ceil(a11ySize / 4);
      const a11yReduction = ((fullSize - a11ySize) / fullSize * 100).toFixed(2);
      console.log(`   Size: ${a11ySize} chars (~${a11yTokens} tokens)`);
      console.log(`   ✅ Reduction: ${a11yReduction}% (${fullTokens - a11yTokens} tokens saved)\n`);
    } else {
      console.log('   ⚠️  Accessibility tree not available\n');
    }

    // Technique 4: Interactive elements only (minimal toolset)
    console.log('4️⃣  Interactive Elements Only (Minimal Toolset)');
    const interactive = await getInteractiveElements(page);
    const interactiveSize = JSON.stringify(interactive).length;
    const interactiveTokens = Math.ceil(interactiveSize / 4);
    const interactiveReduction = ((fullSize - interactiveSize) / fullSize * 100).toFixed(2);
    console.log(`   Elements: ${interactive.length}`);
    console.log(`   Size: ${interactiveSize} chars (~${interactiveTokens} tokens)`);
    console.log(`   ✅ Reduction: ${interactiveReduction}% (${fullTokens - interactiveTokens} tokens saved)\n`);

    // Security-aware pattern: Observe before execute
    console.log('5️⃣  Security-Aware Pattern: Observe Before Execute');
    const testSelectors = ['a', 'button', 'input'];

    for (const selector of testSelectors) {
      const observation = await observeAction(page, selector, 'click');
      if (observation.success) {
        console.log(`   ✅ ${selector}: Safe to execute`);
        console.log(`      Element: ${observation.element.tag} - ${observation.element.text?.substring(0, 30)}`);
      } else {
        console.log(`   ⚠️  ${selector}: Not found`);
      }
    }
    console.log();

    // Filter sensitive data demonstration
    console.log('6️⃣  Sensitive Data Filtering');
    const testDOM = {
      snapshot: {
        tag: 'div',
        children: [
          {
            tag: 'input',
            name: 'password',
            text: 'secret123',
            placeholder: 'Enter password'
          },
          {
            tag: 'input',
            name: 'api_key',
            text: 'sk-1234567890'
          },
          {
            tag: 'span',
            text: 'User: john@example.com'
          }
        ]
      }
    };

    const filtered = filterSensitiveData(testDOM);
    console.log('   Before:', JSON.stringify(testDOM.snapshot.children[0], null, 2));
    console.log('   After:', JSON.stringify(filtered.snapshot.children[0], null, 2));
    console.log('   ✅ Sensitive data redacted\n');

    // Summary
    console.log('=' .repeat(60));
    console.log('📊 Optimization Summary\n');
    console.log(`Full DOM:              ${fullTokens} tokens (baseline)`);
    console.log(`Focused DOM:           ${focusedTokens} tokens (${reduction}% reduction) ⭐`);
    console.log(`Interactive Elements:  ${interactiveTokens} tokens (${interactiveReduction}% reduction) ⭐⭐`);
    console.log('=' .repeat(60));
    console.log(`\n✅ Achieved ${reduction}% token reduction with FocusAgent technique`);
    console.log(`✅ Research target: >50% reduction (often >80%)`);
    console.log(`✅ Our result: ${reduction}% - ${parseFloat(reduction) > 50 ? 'GOAL MET! 🎉' : 'Approaching target'}\n`);

  } catch (error) {
    console.error('\n❌ Demo failed:', error.message);
    throw error;
  } finally {
    await browser.close();
    console.log('🏁 Demo completed');
  }
})();
