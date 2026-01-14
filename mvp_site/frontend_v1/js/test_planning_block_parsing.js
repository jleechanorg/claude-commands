/**
 * JavaScript Unit Tests for Planning Block Parsing
 * Tests pros/cons/confidence rendering for planning block choices
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
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

const sanitizeIdentifier = (text) => {
  if (!text) return 'unknown';
  // Keep only alphanumeric, underscore, and hyphen characters
  return text.toString().replace(/[^a-zA-Z0-9_-]/g, '');
};

// Extract the relevant parsing logic from app.js
function parsePlanningBlocksJson(planningBlock) {
  console.log('parsePlanningBlocks: Processing JSON format planning block');

  // Validate structure
  if (!planningBlock.choices || typeof planningBlock.choices !== 'object') {
    console.warn(
      'parsePlanningBlocks: Invalid JSON structure - missing or invalid choices',
    );
    return planningBlock.thinking || '';
  }

  const choices = planningBlock.choices;
  const choiceKeys = Object.keys(choices);

  // If no choices, just return thinking text
  if (choiceKeys.length === 0) {
    console.log('parsePlanningBlocks: No choices in planning block');
    return planningBlock.thinking || '';
  }

  // Build HTML output
  let html = '';

  // Add thinking text if present
  if (planningBlock.thinking) {
    const sanitizedThinking = sanitizeHtml(planningBlock.thinking);
    html += `<div class="planning-block-thinking">${sanitizedThinking}</div>`;
  }

  // Add context if present
  if (planningBlock.context) {
    const sanitizedContext = sanitizeHtml(planningBlock.context);
    html += `<div class="planning-block-context">${sanitizedContext}</div>`;
  }

  // Create choice buttons
  html += '<div class="planning-block-choices">';

  choiceKeys.forEach((choiceKey) => {
    const choice = choices[choiceKey];

    // Validate choice structure
    if (!choice || typeof choice !== 'object') {
      console.warn(
        `parsePlanningBlocks: Invalid choice object for key: ${choiceKey}`,
      );
      return;
    }

    if (!choice.text || !choice.description) {
      console.warn(
        `parsePlanningBlocks: Choice missing required fields: ${choiceKey}`,
      );
      return;
    }

    // Sanitize choice data
    const safeKey = sanitizeIdentifier(choiceKey);
    const safeText = sanitizeHtml(choice.text);
    const safeDescription = sanitizeHtml(choice.description);
    const riskLevel = choice.risk_level || 'low';
    const switchToStory = choice.switch_to_story_mode === true;

    // Expanded rendering when pros/cons/confidence are present.
    const hasExpandedDetails =
      (Array.isArray(choice.pros) && choice.pros.length > 0) ||
      (Array.isArray(choice.cons) && choice.cons.length > 0) ||
      (typeof choice.confidence === 'string' && choice.confidence.trim());

    if (hasExpandedDetails) {
      const safePros = Array.isArray(choice.pros)
        ? choice.pros.map((p) => sanitizeHtml(p))
        : [];
      const safeCons = Array.isArray(choice.cons)
        ? choice.cons.map((c) => sanitizeHtml(c))
        : [];
      const safeConfidence =
        typeof choice.confidence === 'string'
          ? sanitizeHtml(choice.confidence)
          : '';

      // Build multi-line button text
      let buttonText = `${safeText}: ${safeDescription}`;
      if (safePros.length > 0) {
        buttonText += `\nPros: ${safePros.join(', ')}`;
      }
      if (safeCons.length > 0) {
        buttonText += `\nCons: ${safeCons.join(', ')}`;
      }
      if (safeConfidence) {
        buttonText += `\nAssessment: ${safeConfidence}`;
      }

      const choiceData = `${safeText} - ${safeDescription}`;
      const escapedChoiceData = escapeHtmlAttribute(choiceData);
      const escapedTitle = escapeHtmlAttribute(safeDescription);
      const riskClass = `risk-${riskLevel}`;

      html +=
        `<button class="choice-button ${riskClass}" ` +
        `data-choice-id="${safeKey}" ` +
        `data-choice-text="${escapedChoiceData}" ` +
        `data-switch-to-story="${switchToStory}" ` +
        `title="${escapedTitle}" ` +
        `style="white-space: pre-wrap; text-align: left;">${buttonText}</button>`;
    } else {
      // Standard mode - render simple button format
      const buttonText = `${safeText}: ${safeDescription}`;
      const choiceData = `${safeText} - ${safeDescription}`;
      const escapedChoiceData = escapeHtmlAttribute(choiceData);
      const escapedTitle = escapeHtmlAttribute(safeDescription);
      const riskClass = `risk-${riskLevel}`;

      html +=
        `<button class="choice-button ${riskClass}" ` +
        `data-choice-id="${safeKey}" ` +
        `data-choice-text="${escapedChoiceData}" ` +
        `data-switch-to-story="${switchToStory}" ` +
        `title="${escapedTitle}">${buttonText}</button>`;
    }
  });

  html += '</div>';

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

// Test 1: Expanded choice rendering with top-level fields
suite.test(
  'Should render expanded choice with choice-level pros/cons/confidence',
  function () {
    const planningBlock = {
      thinking:
        'This is a critical moment. I need to weigh my options carefully.',
      choices: {
        attack_head_on: {
          text: 'Attack Head-On',
          description: 'Charge forward with sword raised',
          risk_level: 'high',
          // Canonical schema: pros/cons/confidence at the choice level.
          pros: ['Quick resolution', 'Shows courage', 'Might catch dragon off-guard'],
          cons: ['High risk of injury', 'Could provoke rage', 'Uses up stamina'],
          confidence: 'Low - this seems reckless but could work',
          // analysis is reserved for metadata (not required for this test)
          analysis: { coordination_dc: 16 },
        },
      },
    };

    const html = parsePlanningBlocksJson(planningBlock);

    // Should contain content from arrays (rendered as comma-separated strings in button text)
    this.assertContains(
      html,
      'Quick resolution',
      'Should contain pros content',
    );
    this.assertContains(
      html,
      'High risk of injury',
      'Should contain cons content',
    );
    this.assertContains(
      html,
      'Low - this seems reckless',
      'Should contain confidence assessment',
    );

    // Should contain button with expanded details (matching production code)
    this.assertContains(
      html,
      'class="choice-button',
      'Should contain choice-button class',
    );
    this.assertContains(html, 'Pros:', 'Should contain pros label');
    this.assertContains(html, 'Cons:', 'Should contain cons label');
    this.assertContains(
      html,
      'Assessment:',
      'Should contain assessment label',
    );
    // Production uses newline-separated text in button, not nested divs
    this.assertContains(
      html,
      'white-space: pre-wrap',
      'Should use pre-wrap styling for multi-line text',
    );
    // Check for correct class names from production
    this.assertContains(
      html,
      'planning-block-thinking',
      'Should use production thinking class',
    );
    this.assertContains(
      html,
      'planning-block-choices',
      'Should use production choices container class',
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
        pros: [
          "<script>alert('xss')</script>Safe option",
          "No danger<img src=x onerror=alert('xss')>",
        ],
        cons: ["Might be boring<script>console.log('evil')</script>"],
        confidence: 'High confidence<b>bold text</b>',
        analysis: { note: 'metadata-only' },
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
  this.assertContains(html, 'No danger', 'Should preserve safe content');
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
        pros: [],
        cons: [],
        confidence: '',
        analysis: {},
      },
    },
  };

  const html = parsePlanningBlocksJson(planningBlock);

  // Should not render empty sections (production doesn't use these labels if empty)
  this.assertNotContains(html, 'Pros:', 'Should not render pros label when empty');
  this.assertNotContains(html, 'Cons:', 'Should not render cons label when empty');
  this.assertNotContains(html, 'Assessment:', 'Should not render assessment label when empty');
  
  this.assertContains(
    html,
    'class="choice-button',
    'Should contain choice-button class',
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
        pros: ['Thoughtful approach, well-considered'],
        cons: ['Takes more time, requires focus'],
        confidence: 'High confidence in this approach',
        analysis: { note: 'metadata-only' },
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

  // Deep think choice SHOULD have expanded details in button text
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
    'Pros:',
    'Should have pros label in expanded choice',
  );
  this.assertContains(
    html,
    'white-space: pre-wrap',
    'Should use pre-wrap for multi-line expanded choice',
  );
});

// Test 5: Malformed data handling
suite.test('Should handle malformed planning blocks gracefully', function () {
  const malformedBlock = {
    thinking: 'Malformed test',
    choices: 'not an object',
  };

  const html = parsePlanningBlocksJson(malformedBlock);

  // Should return thinking text only (matching production app.js line 1233)
  this.assert(html === 'Malformed test', 'Should return thinking text on malformed choices');
});

// Run the tests
if (require.main === module) {
  suite.run();
}

module.exports = { parsePlanningBlocksJson, PlanningBlockTestSuite };
