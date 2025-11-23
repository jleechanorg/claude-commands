/**
 * Modular Agent Architecture
 *
 * Implements separation of concerns between reasoning and action execution.
 * Based on Stagehand's approach: Claude for trajectory planning,
 * specialized models for action execution.
 *
 * Pattern: Planner (reasoning) → Generator (action) → Healer (error recovery)
 */

const {
  getFocusedDOM,
  getAccessibilitySnapshot,
  observeAction,
  filterSensitiveData,
  getInteractiveElements
} = require('./dom-optimizer.js');

/**
 * Planner Agent: High-level reasoning about browser state
 */
class PlannerAgent {
  constructor(page, options = {}) {
    this.page = page;
    this.verbose = options.verbose || false;
    this.history = [];
  }

  /**
   * Analyze current page state and plan next actions
   */
  async analyzePage(goal) {
    if (this.verbose) console.log('🧠 Planner: Analyzing page state...');

    // Get focused DOM (50-80% smaller than full DOM)
    const focusedDOM = await getFocusedDOM(this.page, {
      maxDepth: 3,
      includeHidden: false
    });

    // Get accessibility tree for semantic information
    const a11yTree = await getAccessibilitySnapshot(this.page);

    // Get interactive elements only (minimal toolset)
    const interactiveElements = await getInteractiveElements(this.page);

    // Filter sensitive data (security-aware pattern)
    const safeDOM = filterSensitiveData(focusedDOM);

    const pageState = {
      url: await this.page.url(),
      title: await this.page.title(),
      focusedDOM: safeDOM,
      accessibilityTree: a11yTree,
      interactiveElements: interactiveElements.slice(0, 20), // Limit to reduce token count
      viewportSize: await this.page.viewportSize()
    };

    // Simple planning logic (in real implementation, this would call LLM)
    const plan = this.generatePlan(pageState, goal);

    this.history.push({
      timestamp: Date.now(),
      goal,
      pageState,
      plan
    });

    if (this.verbose) {
      console.log(`✅ Planner: Generated ${plan.steps.length} step plan`);
    }

    return plan;
  }

  /**
   * Generate action plan (simplified - would use LLM in production)
   */
  generatePlan(pageState, goal) {
    return {
      goal,
      confidence: 0.8,
      steps: [
        {
          action: 'observe',
          target: 'main interactive elements',
          reasoning: 'Identify available actions before execution'
        },
        {
          action: 'execute',
          target: 'specific element',
          reasoning: 'Perform the planned action'
        }
      ]
    };
  }

  /**
   * Get planning history
   */
  getHistory() {
    return this.history;
  }
}

/**
 * Generator Agent: Execute specific actions based on plan
 */
class GeneratorAgent {
  constructor(page, options = {}) {
    this.page = page;
    this.verbose = options.verbose || false;
    this.executionLog = [];
  }

  /**
   * Execute a planned action
   */
  async executeAction(action) {
    if (this.verbose) console.log(`⚡ Generator: Executing ${action.type}...`);

    const result = {
      timestamp: Date.now(),
      action,
      success: false,
      error: null
    };

    try {
      switch (action.type) {
        case 'click':
          result.observation = await observeAction(this.page, action.selector, 'click');
          if (result.observation.safeToExecute) {
            await this.page.click(action.selector);
            result.success = true;
          } else {
            result.error = 'Element not safe to click';
          }
          break;

        case 'type':
          result.observation = await observeAction(this.page, action.selector, 'type');
          if (result.observation.safeToExecute) {
            await this.page.fill(action.selector, action.text);
            result.success = true;
          } else {
            result.error = 'Element not safe to type into';
          }
          break;

        case 'navigate':
          await this.page.goto(action.url);
          result.success = true;
          break;

        case 'wait':
          await this.page.waitForTimeout(action.duration || 1000);
          result.success = true;
          break;

        default:
          result.error = `Unknown action type: ${action.type}`;
      }
    } catch (error) {
      result.error = error.message;
    }

    this.executionLog.push(result);

    if (this.verbose) {
      const status = result.success ? '✅' : '❌';
      console.log(`${status} Generator: ${action.type} ${result.success ? 'succeeded' : 'failed'}`);
    }

    return result;
  }

  /**
   * Get execution log
   */
  getLog() {
    return this.executionLog;
  }
}

/**
 * Healer Agent: Error recovery and retry logic
 */
class HealerAgent {
  constructor(page, options = {}) {
    this.page = page;
    this.verbose = options.verbose || false;
    this.healingAttempts = [];
  }

  /**
   * Attempt to recover from failed action
   */
  async heal(failedAction, error) {
    if (this.verbose) console.log('🔧 Healer: Attempting recovery...');

    const healing = {
      timestamp: Date.now(),
      failedAction,
      error,
      attempts: [],
      recovered: false
    };

    // Strategy 1: Wait and retry
    healing.attempts.push('wait-retry');
    try {
      await this.page.waitForTimeout(2000);
      await this.retryAction(failedAction);
      healing.recovered = true;
      if (this.verbose) console.log('✅ Healer: Recovery successful (wait-retry)');
      return healing;
    } catch (err) {
      healing.attempts.push(`wait-retry failed: ${err.message}`);
    }

    // Strategy 2: Try alternative selector
    if (failedAction.alternativeSelectors) {
      for (const altSelector of failedAction.alternativeSelectors) {
        healing.attempts.push(`alternative-selector: ${altSelector}`);
        try {
          const observation = await observeAction(this.page, altSelector, failedAction.type);
          if (observation.safeToExecute) {
            await this.executeAlternative(failedAction, altSelector);
            healing.recovered = true;
            if (this.verbose) console.log('✅ Healer: Recovery successful (alternative selector)');
            return healing;
          }
        } catch (err) {
          healing.attempts.push(`alternative-selector failed: ${err.message}`);
        }
      }
    }

    // Strategy 3: Reload page and retry
    healing.attempts.push('reload-retry');
    try {
      await this.page.reload();
      await this.page.waitForLoadState('networkidle');
      await this.retryAction(failedAction);
      healing.recovered = true;
      if (this.verbose) console.log('✅ Healer: Recovery successful (reload-retry)');
      return healing;
    } catch (err) {
      healing.attempts.push(`reload-retry failed: ${err.message}`);
    }

    if (this.verbose) console.log('❌ Healer: All recovery attempts failed');
    this.healingAttempts.push(healing);
    return healing;
  }

  /**
   * Retry original action
   */
  async retryAction(action) {
    switch (action.type) {
      case 'click':
        return await this.page.click(action.selector);
      case 'type':
        return await this.page.fill(action.selector, action.text);
      default:
        throw new Error(`Cannot retry action type: ${action.type}`);
    }
  }

  /**
   * Execute action with alternative selector
   */
  async executeAlternative(action, altSelector) {
    switch (action.type) {
      case 'click':
        return await this.page.click(altSelector);
      case 'type':
        return await this.page.fill(altSelector, action.text);
      default:
        throw new Error(`Cannot execute alternative for action type: ${action.type}`);
    }
  }

  /**
   * Get healing history
   */
  getHistory() {
    return this.healingAttempts;
  }
}

/**
 * Orchestrator: Coordinates Planner → Generator → Healer pipeline
 */
class AgentOrchestrator {
  constructor(page, options = {}) {
    this.page = page;
    this.verbose = options.verbose ?? true;

    this.planner = new PlannerAgent(page, { verbose: this.verbose });
    this.generator = new GeneratorAgent(page, { verbose: this.verbose });
    this.healer = new HealerAgent(page, { verbose: this.verbose });

    this.workflow = [];
  }

  /**
   * Execute complete workflow: Plan → Execute → Heal if needed
   */
  async executeWorkflow(goal, actions) {
    if (this.verbose) console.log(`\n🎯 Workflow Goal: ${goal}\n`);

    const workflowResult = {
      goal,
      startTime: Date.now(),
      plan: null,
      executionResults: [],
      healingResults: [],
      success: false
    };

    try {
      // Step 1: Plan
      workflowResult.plan = await this.planner.analyzePage(goal);

      // Step 2: Execute actions
      for (const action of actions) {
        const result = await this.generator.executeAction(action);
        workflowResult.executionResults.push(result);

        // Step 3: Heal if action failed
        if (!result.success) {
          const healing = await this.healer.heal(action, result.error);
          workflowResult.healingResults.push(healing);

          if (!healing.recovered) {
            throw new Error(`Failed to recover from: ${result.error}`);
          }
        }
      }

      workflowResult.success = true;
      if (this.verbose) console.log('\n✅ Workflow completed successfully\n');

    } catch (error) {
      workflowResult.success = false;
      workflowResult.error = error.message;
      console.error(`\n❌ Workflow failed: ${error.message}\n`);
    }

    workflowResult.endTime = Date.now();
    workflowResult.duration = workflowResult.endTime - workflowResult.startTime;

    this.workflow.push(workflowResult);
    return workflowResult;
  }

  /**
   * Get complete workflow history
   */
  getWorkflowHistory() {
    return {
      workflows: this.workflow,
      planner: this.planner.getHistory(),
      generator: this.generator.getLog(),
      healer: this.healer.getHistory()
    };
  }
}

module.exports = {
  PlannerAgent,
  GeneratorAgent,
  HealerAgent,
  AgentOrchestrator
};
