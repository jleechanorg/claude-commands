/**
 * Modular Agent Workflow Example
 *
 * Demonstrates Planner → Generator → Healer architecture
 * for robust browser automation.
 *
 * Usage:
 *   cd skills/playwright-worldarchitect
 *   node run.js examples/modular-agent-workflow.js
 */

const { chromium } = require('playwright');
const { AgentOrchestrator } = require('../lib/modular-agent.js');

(async () => {
  console.log('🤖 Modular Agent Workflow Demo\n');

  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  try {
    // Navigate to test page
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');

    // Create orchestrator with Planner → Generator → Healer pipeline
    const orchestrator = new AgentOrchestrator(page, { verbose: true });

    // Workflow 1: Simple navigation test
    console.log('\n' + '='.repeat(60));
    console.log('Workflow 1: Navigation Test');
    console.log('='.repeat(60));

    const navigationWorkflow = await orchestrator.executeWorkflow(
      'Navigate to campaigns page',
      [
        {
          type: 'click',
          selector: 'a[href="/campaigns"]',
          alternativeSelectors: ['a:has-text("Campaigns")', 'button:has-text("Campaigns")']
        },
        {
          type: 'wait',
          duration: 2000
        }
      ]
    );

    console.log('\nNavigation Result:', navigationWorkflow.success ? '✅ Success' : '❌ Failed');

    // Workflow 2: Form submission with error handling
    console.log('\n' + '='.repeat(60));
    console.log('Workflow 2: Form Submission with Auto-Healing');
    console.log('='.repeat(60));

    const formWorkflow = await orchestrator.executeWorkflow(
      'Create new campaign',
      [
        {
          type: 'click',
          selector: 'button:has-text("New Campaign")',
          alternativeSelectors: ['a[href="/campaigns/new"]', '[data-testid="new-campaign"]']
        },
        {
          type: 'wait',
          duration: 1000
        },
        {
          type: 'type',
          selector: '#campaign-name',
          text: 'Agent Test Campaign',
          alternativeSelectors: ['input[name="campaign_name"]', '[placeholder*="campaign"]']
        },
        {
          type: 'type',
          selector: '#campaign-description',
          text: 'Created by modular agent workflow',
          alternativeSelectors: ['textarea[name="description"]']
        },
        {
          type: 'click',
          selector: 'button[type="submit"]',
          alternativeSelectors: ['button:has-text("Create")', 'button:has-text("Submit")']
        }
      ]
    );

    console.log('\nForm Submission Result:', formWorkflow.success ? '✅ Success' : '❌ Failed');

    // Get complete workflow history
    const history = orchestrator.getWorkflowHistory();

    console.log('\n' + '='.repeat(60));
    console.log('📊 Workflow Summary');
    console.log('='.repeat(60));

    console.log(`\nTotal Workflows: ${history.workflows.length}`);
    console.log(`Planner Decisions: ${history.planner.length}`);
    console.log(`Actions Executed: ${history.generator.length}`);
    console.log(`Healing Attempts: ${history.healer.length}`);

    // Show detailed results
    history.workflows.forEach((workflow, i) => {
      console.log(`\nWorkflow ${i + 1}: ${workflow.goal}`);
      console.log(`  Status: ${workflow.success ? '✅ Success' : '❌ Failed'}`);
      console.log(`  Duration: ${workflow.duration}ms`);
      console.log(`  Actions: ${workflow.executionResults.length}`);

      if (workflow.healingResults.length > 0) {
        console.log(`  Healing: ${workflow.healingResults.length} attempts`);
        workflow.healingResults.forEach((healing, j) => {
          console.log(`    ${j + 1}. ${healing.recovered ? '✅ Recovered' : '❌ Failed'} (${healing.attempts.length} strategies)`);
        });
      }
    });

    console.log('\n' + '='.repeat(60));
    console.log('✅ Modular Agent Architecture Benefits:');
    console.log('='.repeat(60));
    console.log('1. ✅ Separation of concerns (Planner, Generator, Healer)');
    console.log('2. ✅ Automatic error recovery with multiple strategies');
    console.log('3. ✅ Comprehensive workflow history and debugging');
    console.log('4. ✅ Security-aware with observe-before-execute pattern');
    console.log('5. ✅ Reduced token consumption via focused DOM analysis');

  } catch (error) {
    console.error('\n❌ Workflow failed:', error.message);
    throw error;
  } finally {
    await browser.close();
    console.log('\n🏁 Demo completed');
  }
})();
