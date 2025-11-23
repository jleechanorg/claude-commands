/**
 * DOM Optimization & Observation Size Reduction
 *
 * Implements FocusAgent-inspired techniques and D2Snap principles to reduce
 * DOM observation size by 50-80% while maintaining performance.
 *
 * Based on research:
 * - FocusAgent: Reduces observation size by >50% (often >80%)
 * - D2Snap: DOM downsampling maintaining ~1000 tokens
 * - Stagehand security patterns: observe() before act()
 */

/**
 * Extract focused DOM snapshot with reduced token size
 * @param {Page} page - Playwright page
 * @param {Object} options - Optimization options
 * @returns {Promise<Object>} Focused DOM snapshot
 */
async function getFocusedDOM(page, options = {}) {
  const {
    includeHidden = false,
    maxDepth = 3,
    includeStyles = false,
    focusSelectors = ['main', 'article', '[role="main"]', '.content']
  } = options;

  return await page.evaluate(({ includeHidden, maxDepth, includeStyles, focusSelectors }) => {
    /**
     * Focus on relevant DOM areas (FocusAgent principle)
     */
    function findFocusArea() {
      for (const selector of focusSelectors) {
        const element = document.querySelector(selector);
        if (element) return element;
      }
      return document.body;
    }

    /**
     * Check if element is interactive or meaningful
     */
    function isRelevantElement(element) {
      const tagName = element.tagName.toLowerCase();

      // Always include interactive elements
      const interactiveElements = ['a', 'button', 'input', 'select', 'textarea', 'form'];
      if (interactiveElements.includes(tagName)) return true;

      // Include semantic elements
      const semanticElements = ['nav', 'header', 'main', 'article', 'section', 'aside', 'footer'];
      if (semanticElements.includes(tagName)) return true;

      // Include elements with ARIA roles
      if (element.hasAttribute('role')) return true;

      // Include elements with click handlers
      if (element.onclick || element.getAttribute('onclick')) return true;

      // Include elements with text content
      const text = element.textContent?.trim();
      if (text && text.length > 0 && text.length < 200) return true;

      return false;
    }

    /**
     * Downsample DOM node (D2Snap principle)
     */
    function downsampleNode(element, depth = 0) {
      if (depth > maxDepth) return null;

      // Skip hidden elements unless specified
      if (!includeHidden) {
        const style = window.getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden') {
          return null;
        }
      }

      // Only process relevant elements
      if (!isRelevantElement(element)) {
        // Still recurse through children to find relevant nested elements
        const relevantChildren = Array.from(element.children)
          .map(child => downsampleNode(child, depth + 1))
          .filter(Boolean);

        if (relevantChildren.length > 0) {
          return {
            tag: element.tagName.toLowerCase(),
            children: relevantChildren
          };
        }

        return null;
      }

      const node = {
        tag: element.tagName.toLowerCase(),
        id: element.id || undefined,
        classes: element.className ? element.className.split(' ').filter(Boolean) : undefined,
        text: element.textContent?.trim().substring(0, 200) || undefined,
        role: element.getAttribute('role') || undefined,
        type: element.getAttribute('type') || undefined,
        href: element.getAttribute('href') || undefined,
        name: element.getAttribute('name') || undefined,
        placeholder: element.getAttribute('placeholder') || undefined,
        ariaLabel: element.getAttribute('aria-label') || undefined
      };

      // Include computed styles only if requested (expensive)
      if (includeStyles) {
        const style = window.getComputedStyle(element);
        node.styles = {
          display: style.display,
          position: style.position,
          visibility: style.visibility
        };
      }

      // Recursively process children
      const children = Array.from(element.children)
        .map(child => downsampleNode(child, depth + 1))
        .filter(Boolean);

      if (children.length > 0) {
        node.children = children;
      }

      // Remove undefined properties to reduce size
      Object.keys(node).forEach(key => {
        if (node[key] === undefined) delete node[key];
      });

      return node;
    }

    const focusArea = findFocusArea();
    const snapshot = downsampleNode(focusArea);

    return {
      timestamp: Date.now(),
      url: window.location.href,
      title: document.title,
      focusArea: focusArea.tagName,
      snapshot
    };
  }, { includeHidden, maxDepth, includeStyles, focusSelectors });
}

/**
 * Extract accessibility tree (semantic DOM information)
 * @param {Page} page - Playwright page
 * @returns {Promise<Object>} Accessibility tree snapshot
 */
async function getAccessibilitySnapshot(page) {
  try {
    const snapshot = await page.accessibility.snapshot();
    return {
      timestamp: Date.now(),
      tree: snapshot
    };
  } catch (err) {
    console.warn('⚠️  Accessibility snapshot not available:', err.message);
    return null;
  }
}

/**
 * Observe action without execution (Stagehand security pattern)
 * @param {Page} page - Playwright page
 * @param {string} selector - Element selector
 * @param {string} actionType - Action to observe (click, type, etc.)
 * @returns {Promise<Object>} Action preview
 */
async function observeAction(page, selector, actionType = 'click') {
  const element = await page.$(selector);

  if (!element) {
    return {
      success: false,
      error: `Element not found: ${selector}`,
      selector
    };
  }

  const elementInfo = await element.evaluate((el, action) => {
    const rect = el.getBoundingClientRect();
    const computedStyle = window.getComputedStyle(el);

    return {
      tag: el.tagName.toLowerCase(),
      id: el.id || null,
      classes: Array.from(el.classList),
      text: el.textContent?.trim().substring(0, 100),
      visible: computedStyle.display !== 'none' && computedStyle.visibility !== 'hidden',
      position: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      },
      attributes: {
        type: el.getAttribute('type'),
        href: el.getAttribute('href'),
        name: el.getAttribute('name'),
        disabled: el.disabled,
        readonly: el.readOnly
      },
      actionType: action,
      actionValid: action === 'click' ? true : el.tagName.match(/INPUT|TEXTAREA|SELECT/) !== null
    };
  }, actionType);

  return {
    success: true,
    selector,
    element: elementInfo,
    safeToExecute: elementInfo.visible && elementInfo.actionValid
  };
}

/**
 * Filter sensitive information from DOM snapshot
 * @param {Object} snapshot - DOM snapshot
 * @param {Array<string>} sensitivePatterns - Patterns to filter
 * @returns {Object} Filtered snapshot
 */
function filterSensitiveData(snapshot, sensitivePatterns = []) {
  const defaultPatterns = [
    /password/i,
    /token/i,
    /api[_-]?key/i,
    /secret/i,
    /credit[_-]?card/i,
    /ssn/i,
    /\d{3}-\d{2}-\d{4}/, // SSN pattern
    /\d{16}/, // Credit card pattern
  ];

  const patterns = [...defaultPatterns, ...sensitivePatterns];

  function filterNode(node) {
    if (!node) return null;

    const filtered = { ...node };

    // Filter text content
    if (filtered.text) {
      for (const pattern of patterns) {
        if (pattern.test(filtered.text)) {
          filtered.text = '[REDACTED]';
          break;
        }
      }
    }

    // Filter attribute values
    ['name', 'id', 'placeholder', 'ariaLabel'].forEach(attr => {
      if (filtered[attr]) {
        for (const pattern of patterns) {
          if (pattern.test(filtered[attr])) {
            filtered[attr] = '[REDACTED]';
            break;
          }
        }
      }
    });

    // Recursively filter children
    if (filtered.children) {
      filtered.children = filtered.children
        .map(child => filterNode(child))
        .filter(Boolean);
    }

    return filtered;
  }

  return {
    ...snapshot,
    snapshot: filterNode(snapshot.snapshot)
  };
}

/**
 * Measure DOM observation size reduction
 * @param {Object} fullDOM - Full DOM snapshot
 * @param {Object} focusedDOM - Focused DOM snapshot
 * @returns {Object} Size comparison metrics
 */
function measureOptimization(fullDOM, focusedDOM) {
  const fullSize = JSON.stringify(fullDOM).length;
  const focusedSize = JSON.stringify(focusedDOM).length;
  const reduction = ((fullSize - focusedSize) / fullSize * 100).toFixed(2);

  return {
    fullSize,
    focusedSize,
    reduction: `${reduction}%`,
    tokens: {
      full: Math.ceil(fullSize / 4), // Rough estimate: 1 token ≈ 4 chars
      focused: Math.ceil(focusedSize / 4)
    }
  };
}

/**
 * Extract interactive elements only (minimal toolset curation)
 * @param {Page} page - Playwright page
 * @returns {Promise<Array>} Interactive elements
 */
async function getInteractiveElements(page) {
  return await page.evaluate(() => {
    const interactiveSelectors = [
      'a[href]',
      'button',
      'input:not([type="hidden"])',
      'select',
      'textarea',
      '[onclick]',
      '[role="button"]',
      '[role="link"]',
      '[tabindex]:not([tabindex="-1"])'
    ];

    const elements = [];
    const seenElements = new Set();

    interactiveSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(el => {
        if (seenElements.has(el)) return;
        seenElements.add(el);

        const rect = el.getBoundingClientRect();
        const computedStyle = window.getComputedStyle(el);

        // Skip hidden elements
        if (computedStyle.display === 'none' || computedStyle.visibility === 'hidden') {
          return;
        }

        // Skip elements outside viewport (optional optimization)
        if (rect.bottom < 0 || rect.top > window.innerHeight) {
          return;
        }

        elements.push({
          tag: el.tagName.toLowerCase(),
          type: el.getAttribute('type'),
          id: el.id || null,
          classes: Array.from(el.classList),
          text: el.textContent?.trim().substring(0, 50),
          role: el.getAttribute('role') || el.tagName.toLowerCase(),
          ariaLabel: el.getAttribute('aria-label'),
          href: el.getAttribute('href'),
          position: {
            x: Math.round(rect.x),
            y: Math.round(rect.y)
          }
        });
      });
    });

    return elements;
  });
}

module.exports = {
  getFocusedDOM,
  getAccessibilitySnapshot,
  observeAction,
  filterSensitiveData,
  measureOptimization,
  getInteractiveElements
};
