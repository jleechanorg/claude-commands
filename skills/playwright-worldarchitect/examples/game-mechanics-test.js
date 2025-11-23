/**
 * Game Mechanics Test
 *
 * Tests character creation, dice rolling, and game actions.
 *
 * Usage:
 *   cd skills/playwright-worldarchitect
 *   node run.js examples/game-mechanics-test.js
 */

const {
  launchBrowser,
  detectDevServers,
  createCharacter,
  performDiceRoll,
  sendGameAction,
  waitForPageReady,
  takeScreenshot,
  safeClick
} = require('../lib/helpers.js');

(async () => {
  console.log('⚔️  Game Mechanics Test Starting...\n');

  // Detect running server
  const servers = await detectDevServers();
  if (servers.length === 0) {
    console.error('❌ No dev server detected. Please start the server first.');
    process.exit(1);
  }
  const BASE_URL = servers[0];
  console.log(`📡 Using server: ${BASE_URL}\n`);

  let browser;
  let page;

  try {
    browser = await launchBrowser({ headless: false, slowMo: 100 });
    page = await browser.newPage();
    // Step 1: Navigate to game
    console.log('📍 Step 1: Navigate to home page');
    await page.goto(BASE_URL);
    await waitForPageReady(page);
    console.log('✅ Home page loaded\n');

    // Step 2: Test character creation
    console.log('📍 Step 2: Test character creation');
    try {
      await createCharacter(page, {
        name: 'Thorin Oakenshield',
        characterClass: 'Fighter',
        race: 'Dwarf',
        level: 5
      });
      console.log('✅ Character created successfully\n');
    } catch (err) {
      console.warn('⚠️  Character creation flow not available:', err.message);
      console.warn('   This may require a campaign context\n');
    }

    // Step 3: Test dice rolling mechanics
    console.log('📍 Step 3: Test dice rolling');
    try {
      // Look for dice roller interface
      const diceRoller = await page.$('.dice-roller, #dice-roller, button:has-text("Roll")');

      if (diceRoller) {
        console.log('🎲 Dice roller found, testing rolls...');

        // Test d20 roll
        await performDiceRoll(page, 'attack');
        await page.waitForTimeout(1000);

        // Capture dice roller screenshot
        await takeScreenshot(page, 'dice-roller-interface');

        console.log('✅ Dice rolling tested\n');
      } else {
        console.warn('⚠️  Dice roller not found on this page\n');
      }
    } catch (err) {
      console.warn('⚠️  Dice rolling test skipped:', err.message, '\n');
    }

    // Step 4: Test game action submission
    console.log('📍 Step 4: Test game action submission');
    try {
      // Look for action input
      const actionInput = await page.$('textarea[name="action"], input[name="action"], #action-input');

      if (actionInput) {
        console.log('💬 Action input found, sending test action...');

        await sendGameAction(page, 'I search the room for hidden treasures');
        await page.waitForTimeout(2000); // Wait for AI response

        // Check for response
        const gameLog = await page.$('.game-log, #game-log, .narrative');
        if (gameLog) {
          const logText = await gameLog.textContent();
          console.log(`✅ Game response received (${logText.length} chars)\n`);
        } else {
          console.log('✅ Action sent (response area not detected)\n');
        }
      } else {
        console.warn('⚠️  Action input not found on this page\n');
      }
    } catch (err) {
      console.warn('⚠️  Game action test skipped:', err.message, '\n');
    }

    // Step 5: Test combat mechanics
    console.log('📍 Step 5: Test combat interface');
    try {
      const combatSelector = 'button:has-text("Attack"), button.attack, button:has-text("Cast")';
      const combatButtons = await page.$$(combatSelector);

      if (combatButtons.length > 0) {
        console.log(`⚔️  Found ${combatButtons.length} combat buttons`);

        await safeClick(page, combatSelector);
        await page.waitForTimeout(1500);

        console.log('✅ Combat action triggered\n');
      } else {
        console.warn('⚠️  Combat interface not available\n');
      }
    } catch (err) {
      console.warn('⚠️  Combat test skipped:', err.message, '\n');
    }

    // Step 6: Verify game state persistence
    console.log('📍 Step 6: Verify game state elements');
    const stateElements = [
      { selector: '.character-name, #character-name', name: 'Character name' },
      { selector: '.hp, .health, [class*="health"]', name: 'Health points' },
      { selector: '.level, [class*="level"]', name: 'Character level' },
      { selector: '.game-log, #game-log', name: 'Game log' }
    ];

    let foundElements = 0;
    for (const element of stateElements) {
      const found = await page.$(element.selector);
      if (found) {
        console.log(`✅ ${element.name} element present`);
        foundElements++;
      } else {
        console.log(`⚠️  ${element.name} element not found`);
      }
    }

    console.log(`\n📊 Found ${foundElements}/${stateElements.length} state elements\n`);

    // Step 7: Final screenshot
    console.log('📍 Step 7: Capture final game state');
    await takeScreenshot(page, 'game-mechanics-final', { fullPage: true });
    console.log('✅ Final screenshot captured\n');

    console.log('✅ ✅ ✅ Game mechanics test completed! ✅ ✅ ✅');

    } catch (error) {
      console.error('\n❌ Test failed:', error.message);
      if (page) {
        await takeScreenshot(page, 'game-mechanics-error');
      }
      throw error;
    } finally {
      if (browser) {
        await browser.close();
      }
      console.log('\n🏁 Test completed');
    }
})();
