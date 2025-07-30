/**
 * JavaScript Unit Tests for Planning Block Parsing
 * Tests the new string format for pros/cons in deep think mode
 *
 * Run with: node mvp_site/frontend_v1/js/test_planning_block_parsing.js
 */

// Mock functions that would normally be in app.js
function decodeHtmlEntities(text) {
  if (!text) return '';
  return text
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

function sanitizeHtml(text) {
  if (!text) return '';
  // First decode any existing entities, then encode for safety
  const decoded = decodeHtmlEntities(text);
  return decoded
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

function escapeHtmlAttribute(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, function (match) {
    const escapeMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#x27;',
    };
    return escapeMap[match];
  });
}

// Extract the relevant parsing logic from app.js
function parsePlanningBlocksJson(planningBlock) {
  console.log('parsePlanningBlocks: Processing JSON format planning block');

  // Validate structure
  if (!planningBlock.choices || typeof planningBlock.choices !== 'object') {
    console.warn(
      'parsePlanningBlocks: Invalid JSON structure - missing or invalid choices',
    );
    return '<div class="planning-block-error">❌ Error: Invalid planning block structure. Expected "choices" object.</div>';
  }

  let html = '<div class="planning-block-container">';

  // Add thinking section if present
  if (planningBlock.thinking) {
    const safeThinking = sanitizeHtml(planningBlock.thinking);
    html += `<div class="planning-thinking">
            <div class="thinking-header">💭 Character's Thoughts:</div>
            <div class="thinking-content">${safeThinking}</div>
        </div>`;
  }

  // Add context if present
  if (planningBlock.context) {
    const safeContext = sanitizeHtml(planningBlock.context);
    html += `<div class="planning-context">
            <div class="context-header">🌟 Current Situation:</div>
            <div class="context-content">${safeContext}</div>
        </div>`;
  }

  html += '<div class="planning-choices">';

  for (const [key, choice] of Object.entries(planningBlock.choices)) {
    if (!choice || typeof choice !== 'object') {
      console.warn(
        `parsePlanningBlocks: Invalid choice structure for key: ${key}`,
      );
      continue;
    }

    const safeKey = sanitizeHtml(key);
    const safeText = sanitizeHtml(choice.text || 'Unknown Action');
    const safeDescription = sanitizeHtml(choice.description || '');
    const riskLevel = choice.risk_level || 'low';

    // Check if this is a deep think mode choice with analysis
    if (choice.analysis && typeof choice.analysis === 'object') {
      // Deep think mode - render expanded format with pros/cons as STRINGS
      const analysis = choice.analysis;
      const safePros = analysis.pros ? sanitizeHtml(analysis.pros) : '';
      const safeCons = analysis.cons ? sanitizeHtml(analysis.cons) : '';
      const safeConfidence = analysis.confidence
        ? sanitizeHtml(analysis.confidence)
        : '';

      // Create choice data for form submission
      const choiceData = `${safeText} - ${safeDescription}`;
      const escapedChoiceData = escapeHtmlAttribute(choiceData);

      // Add deep-think class for enhanced styling
      const riskClass = `risk-${riskLevel} deep-think-choice`;

      html += `<div class="choice-container deep-think-choice">
                <button class="choice-button choice-button-expanded ${riskClass}"
                        data-choice-id="${safeKey}"
                        data-choice-text="${escapedChoiceData}">
                    <div class="choice-header">
                        <strong>${safeText}</strong>
                    </div>
                    <div class="choice-description">${safeDescription}</div>
                    <div class="choice-analysis">
                        <div class="pros-cons-container">
                            ${
                              safePros
                                ? `
                                <div class="pros-section">
                                    <span class="analysis-label">✅ Pros:</span>
                                    <div class="analysis-text">${safePros}</div>
                                </div>
                            `
                                : ''
                            }
                            ${
                              safeCons
                                ? `
                                <div class="cons-section">
                                    <span class="analysis-label">❌ Cons:</span>
                                    <div class="analysis-text">${safeCons}</div>
                                </div>
                            `
                                : ''
                            }
                        </div>
                        ${
                          safeConfidence
                            ? `
                            <div class="confidence-section">
                                <span class="analysis-label">🎯 Assessment:</span>
                                <div class="confidence-text">${safeConfidence}</div>
                            </div>
                        `
                            : ''
                        }
                    </div>
                </button>
            </div>`;
    } else {
      // Standard choice format
      const choiceData = `${safeText} - ${safeDescription}`;
      const escapedChoiceData = escapeHtmlAttribute(choiceData);
      const riskClass = `risk-${riskLevel}`;

      html += `<div class="choice-container">
                <button class="choice-button ${riskClass}"
                        data-choice-id="${safeKey}"
                        data-choice-text="${escapedChoiceData}">
                    <div class="choice-text">${safeText}</div>
                    <div class="choice-description">${safeDescription}</div>
                </button>
            </div>`;
    }
  }

  html += '</div></div>';
  return html;
}

// Test Suite
class PlanningBlockTestSuite {
  constructor() {
    this.tests = [];
    this.passed = 0;
    this.failed = 0;
  }

  test(name, testFn) {
    this.tests.push({ name, testFn });
  }

  assert(condition, message) {
    if (!condition) {
      throw new Error(message);
    }
  }

  assertContains(html, substring, message) {
    if (!html.includes(substring)) {
      throw new Error(
        `${message}\nExpected to contain: "${substring}"\nActual HTML: ${html.slice(0, 200)}...`,
      );
    }
  }

  assertNotContains(html, substring, message) {
    if (html.includes(substring)) {
      throw new Error(
        `${message}\nExpected NOT to contain: "${substring}"\nActual HTML: ${html.slice(0, 200)}...`,
      );
    }
  }

  run() {
    console.log(`\n🧪 Running ${this.tests.length} tests...\n`);

    for (const { name, testFn } of this.tests) {
      try {
        testFn.call(this);
        console.log(`✅ PASS: ${name}`);
        this.passed++;
      } catch (error) {
        console.log(`❌ FAIL: ${name}`);
        console.log(`   Error: ${error.message}\n`);
        this.failed++;
      }
    }

    console.log(`\n📊 Results: ${this.passed} passed, ${this.failed} failed`);

    if (this.failed > 0) {
      console.log('\n🚨 TESTS FAILED - Fix required');
      process.exit(1);
    } else {
      console.log('\n🎉 ALL TESTS PASSED');
      process.exit(0);
    }
  }
}

// Create test suite
const suite = new PlanningBlockTestSuite();

// Test 1: Basic string format parsing
suite.test(
  'Should parse deep think mode with STRING format pros/cons',
  function () {
    const planningBlock = {
      thinking:
        'This is a critical moment. I need to weigh my options carefully.',
      choices: {
        attack_head_on: {
          text: 'Attack Head-On',
          description: 'Charge forward with sword raised',
          risk_level: 'high',
          analysis: {
            pros: [
              'Quick resolution',
              'Shows courage',
              'Might catch dragon off-guard',
            ],
            cons: [
              'High risk of injury',
              'Could provoke rage',
              'Uses up stamina',
            ],
            confidence: 'Low - this seems reckless but could work',
          },
        },
      },
    };

    const html = parsePlanningBlocksJson(planningBlock);

    // Should contain bullet points and content from arrays
    this.assertContains(
      html,
      '• Quick resolution',
      'Should contain bullet point pros',
    );
    this.assertContains(
      html,
      '• High risk of injury',
      'Should contain bullet point cons',
    );
    this.assertContains(
      html,
      'Low - this seems reckless',
      'Should contain confidence assessment',
    );

    // Should contain single blue analysis section
    this.assertContains(
      html,
      'analysis-content',
      'Should contain analysis-content class',
    );
    this.assertContains(html, '✅ Pros:', 'Should contain pros label');
    this.assertContains(html, '❌ Cons:', 'Should contain cons label');
    this.assertContains(
      html,
      '🎯 Assessment:',
      'Should contain assessment label',
    );
  },
);

// Test 2: XSS protection with string format (HTML escaping)
suite.test('Should escape HTML in STRING format for safety', function () {
  const planningBlock = {
    thinking: 'Testing HTML escaping',
    choices: {
      test_choice: {
        text: 'Test Choice',
        description: 'Testing HTML escaping',
        risk_level: 'low',
        analysis: {
          pros: [
            "<script>alert('xss')</script>Safe option",
            "No danger<img src=x onerror=alert('xss')>",
          ],
          cons: ["Might be boring<script>console.log('evil')</script>"],
          confidence: 'High confidence<b>bold text</b>',
        },
      },
    },
  };

  const html = parsePlanningBlocksJson(planningBlock);

  // HTML should be escaped (not removed)
  this.assertContains(html, '&lt;script&gt;', 'Should escape script tags');
  this.assertContains(
    html,
    '&lt;/script&gt;',
    'Should escape closing script tags',
  );
  this.assertContains(html, '&lt;img', 'Should escape img tags');
  this.assertContains(html, '&lt;b&gt;', 'Should escape bold tags');

  // Should NOT contain unescaped HTML
  this.assertNotContains(
    html,
    '<script>',
    'Should not contain unescaped script tags',
  );
  this.assertNotContains(html, '<img', 'Should not contain unescaped img tags');

  // Safe content should remain (with escaped HTML)
  this.assertContains(html, 'Safe option', 'Should preserve safe content');
  this.assertContains(html, 'no danger', 'Should preserve safe content');
  this.assertContains(html, 'Might be boring', 'Should preserve safe content');
  this.assertContains(
    html,
    'alert(&#x27;xss&#x27;)',
    'Should escape quotes in JavaScript',
  );
});

// Test 3: Empty analysis fields
suite.test('Should handle empty analysis fields gracefully', function () {
  const planningBlock = {
    thinking: 'Empty analysis test',
    choices: {
      empty_choice: {
        text: 'Empty Analysis',
        description: 'Testing empty fields',
        risk_level: 'medium',
        analysis: {
          pros: '',
          cons: '',
          confidence: '',
        },
      },
    },
  };

  const html = parsePlanningBlocksJson(planningBlock);

  // Should not render empty sections
  this.assertNotContains(
    html,
    'pros-section',
    'Should not render empty pros section',
  );
  this.assertNotContains(
    html,
    'cons-section',
    'Should not render empty cons section',
  );
  this.assertNotContains(
    html,
    'confidence-section',
    'Should not render empty confidence section',
  );
});

// Test 4: Mixed standard and deep think choices
suite.test('Should handle mixed choice types correctly', function () {
  const planningBlock = {
    thinking: 'Mixed choice types',
    choices: {
      standard_choice: {
        text: 'Standard Choice',
        description: 'No analysis field',
      },
      deep_think_choice: {
        text: 'Deep Think Choice',
        description: 'Has analysis field',
        analysis: {
          pros: 'Thoughtful approach, well-considered',
          cons: 'Takes more time, requires focus',
          confidence: 'High confidence in this approach',
        },
      },
    },
  };

  const html = parsePlanningBlocksJson(planningBlock);

  // Standard choice should NOT have analysis sections
  this.assertContains(
    html,
    'Standard Choice',
    'Should contain standard choice',
  );

  // Deep think choice SHOULD have analysis sections
  this.assertContains(
    html,
    'Thoughtful approach, well-considered',
    'Should contain deep think pros',
  );
  this.assertContains(
    html,
    'Takes more time, requires focus',
    'Should contain deep think cons',
  );
  this.assertContains(
    html,
    'High confidence in this approach',
    'Should contain confidence',
  );

  // Should have both choice types
  this.assertContains(
    html,
    'choice-button-expanded',
    'Should have expanded choice',
  );
  this.assertContains(
    html,
    'deep-think-choice',
    'Should have deep think class',
  );
});

// Test 5: Malformed data handling
suite.test('Should handle malformed planning blocks gracefully', function () {
  const malformedBlock = {
    choices: {
      bad_choice: {
        text: 'Bad Choice',
        analysis: 'not an object', // Should be object, not string
      },
    },
  };

  const html = parsePlanningBlocksJson(malformedBlock);

  // Should render as standard choice when analysis is malformed
  this.assertContains(html, 'Bad Choice', 'Should still render the choice');
  this.assertNotContains(
    html,
    'choice-button-expanded',
    'Should not render as expanded choice',
  );
});

// Run the tests
if (require.main === module) {
  suite.run();
}

module.exports = { parsePlanningBlocksJson, PlanningBlockTestSuite };
