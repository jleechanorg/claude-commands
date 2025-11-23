/**
 * Visual Regression Testing
 *
 * Captures, stores, and compares screenshots for visual regression testing
 * across multiple viewports (desktop, tablet, mobile).
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const BASELINE_DIR =
  process.env.PLAYWRIGHT_BASELINE_DIR || path.join(os.tmpdir(), 'playwright-baselines');
const CURRENT_DIR =
  process.env.PLAYWRIGHT_CURRENT_DIR || path.join(os.tmpdir(), 'playwright-current');
const DIFF_DIR = process.env.PLAYWRIGHT_DIFF_DIR || path.join(os.tmpdir(), 'playwright-diffs');

/**
 * Ensure directories exist
 */
function ensureDirectories() {
  [BASELINE_DIR, CURRENT_DIR, DIFF_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

/**
 * Standard viewport configurations
 */
const VIEWPORTS = {
  desktop: { width: 1920, height: 1080, name: 'desktop' },
  laptop: { width: 1366, height: 768, name: 'laptop' },
  tablet: { width: 768, height: 1024, name: 'tablet' },
  mobile: { width: 375, height: 667, name: 'mobile' }
};

/**
 * Internal helper to capture screenshots to a target directory
 */
async function captureScreenshots(page, testName, outputDir, options = {}) {
  ensureDirectories();

  const {
    viewports = Object.values(VIEWPORTS),
    fullPage = true,
    element = null,
    layoutTimeout = 500
  } = options;

  const captures = [];

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.waitForTimeout(layoutTimeout);

    const filename = `${testName}-${viewport.name}.png`;
    const filepath = path.join(outputDir, filename);

    try {
      if (element) {
        const el = await page.$(element);
        if (!el) {
          console.warn(`⚠️  Element not found: ${element}`);
          continue;
        }
        await el.screenshot({ path: filepath });
      } else {
        await page.screenshot({ path: filepath, fullPage });
      }

      console.log(`  ✅ ${viewport.name}: ${filepath}`);
      captures.push({
        viewport: viewport.name,
        file: filepath,
        size: viewport
      });
    } catch (error) {
      console.error(`❌ Failed to capture ${viewport.name}: ${error.message}`);
    }
  }

  return captures;
}

/**
 * Capture baseline screenshots for a page
 */
async function captureBaselines(page, testName, options = {}) {
  console.log(`📸 Capturing baselines for: ${testName}`);
  const captures = await captureScreenshots(page, testName, BASELINE_DIR, options);
  console.log(`✅ Captured ${captures.length} baseline screenshots`);
  return captures;
}

/**
 * Capture current screenshots for comparison
 */
async function captureCurrents(page, testName, options = {}) {
  console.log(`📸 Capturing current screenshots for: ${testName}`);
  return captureScreenshots(page, testName, CURRENT_DIR, options);
}

/**
 * Compare current screenshots against baselines
 * @param {string} testName - Name of the test
 * @param {Object} options - Comparison options
 * @returns {Object} Comparison results
 */
async function compareWithBaselines(testName, options = {}) {
  ensureDirectories();

  const {
    viewports = Object.values(VIEWPORTS),
    threshold = 0.01 // 1% difference threshold
  } = options;

  console.log(`🔍 Comparing screenshots for: ${testName}`);
  console.log(
    'ℹ️  Using size-based comparison; for stricter checks, integrate a pixel diff like pixelmatch.'
  );

  const results = {
    testName,
    passed: 0,
    failed: 0,
    comparisons: []
  };

  console.warn(
    'ℹ️ Using size-based comparison only. For stricter checks, integrate pixel-level diff (e.g., pixelmatch or Playwright assertions).'
  );

  for (const viewport of viewports) {
    const baselineFile = path.join(BASELINE_DIR, `${testName}-${viewport.name}.png`);
    const currentFile = path.join(CURRENT_DIR, `${testName}-${viewport.name}.png`);

    if (!fs.existsSync(baselineFile)) {
      console.warn(`⚠️  No baseline found for ${viewport.name}, skipping comparison`);
      results.comparisons.push({
        viewport: viewport.name,
        status: 'no-baseline',
        baselineFile,
        currentFile
      });
      continue;
    }

    if (!fs.existsSync(currentFile)) {
      console.warn(`⚠️  No current screenshot for ${viewport.name}, skipping comparison`);
      results.comparisons.push({
        viewport: viewport.name,
        status: 'no-current',
        baselineFile,
        currentFile
      });
      continue;
    }

    // Simple file size comparison (in production, use pixelmatch or similar)
    const baselineStats = fs.statSync(baselineFile);
    const currentStats = fs.statSync(currentFile);

    // Guard against division by zero (empty baseline file)
    if (baselineStats.size === 0) {
      console.warn(`⚠️  Empty baseline file for ${viewport.name}, skipping comparison`);
      results.comparisons.push({
        viewport: viewport.name,
        status: 'empty-baseline',
        baselineFile,
        currentFile
      });
      continue;
    }

    const sizeDiff = Math.abs(baselineStats.size - currentStats.size) / baselineStats.size;
    const match = sizeDiff <= threshold;

    const comparison = {
      viewport: viewport.name,
      status: match ? 'pass' : 'fail',
      baselineFile,
      currentFile,
      baselineSize: baselineStats.size,
      currentSize: currentStats.size,
      sizeDifference: `${(sizeDiff * 100).toFixed(2)}%`,
      threshold: `${(threshold * 100).toFixed(2)}%`
    };

    if (match) {
      console.log(`  ✅ ${viewport.name}: Match (${comparison.sizeDifference} difference)`);
      results.passed++;
    } else {
      console.log(`  ❌ ${viewport.name}: Mismatch (${comparison.sizeDifference} difference)`);
      results.failed++;

      // Save diff info (in production, generate actual diff image)
      const diffFile = path.join(DIFF_DIR, `${testName}-${viewport.name}-diff.json`);
      fs.writeFileSync(diffFile, JSON.stringify(comparison, null, 2));
      comparison.diffFile = diffFile;
    }

    results.comparisons.push(comparison);
  }

  console.log(`\n📊 Visual Regression Results: ${results.passed} passed, ${results.failed} failed`);
  return results;
}

/**
 * Promote current screenshots to baselines
 * @param {string} testName - Name of the test
 */
function promoteToBaselines(testName) {
  ensureDirectories();

  console.log(`📋 Promoting current screenshots to baselines for: ${testName}`);

  const currentFiles = fs
    .readdirSync(CURRENT_DIR)
    .filter(file => file.startsWith(`${testName}-`) && file.endsWith('.png'));

  let promoted = 0;

  currentFiles.forEach(file => {
    const currentPath = path.join(CURRENT_DIR, file);
    const baselinePath = path.join(BASELINE_DIR, file);

    fs.copyFileSync(currentPath, baselinePath);
    console.log(`  ✅ Promoted: ${file}`);
    promoted++;
  });

  console.log(`✅ Promoted ${promoted} screenshots to baselines`);
  return promoted;
}

/**
 * List all baselines
 * @returns {Array} List of baseline files
 */
function listBaselines() {
  if (!fs.existsSync(BASELINE_DIR)) {
    return [];
  }

  const files = fs.readdirSync(BASELINE_DIR)
    .filter(file => file.endsWith('.png'))
    .map(file => {
      const stats = fs.statSync(path.join(BASELINE_DIR, file));
      return {
        name: file,
        path: path.join(BASELINE_DIR, file),
        size: stats.size,
        modified: stats.mtime
      };
    });

  return files;
}

/**
 * Clean up old screenshots
 * @param {Object} options - Cleanup options
 */
function cleanup(options = {}) {
  const {
    keepBaselines = true,
    keepCurrent = false,
    keepDiffs = false
  } = options;

  console.log('🧹 Cleaning up screenshots...');

  if (!keepCurrent && fs.existsSync(CURRENT_DIR)) {
    fs.rmSync(CURRENT_DIR, { recursive: true });
    console.log('  ✅ Removed current screenshots');
  }

  if (!keepDiffs && fs.existsSync(DIFF_DIR)) {
    fs.rmSync(DIFF_DIR, { recursive: true });
    console.log('  ✅ Removed diff files');
  }

  if (!keepBaselines && fs.existsSync(BASELINE_DIR)) {
    fs.rmSync(BASELINE_DIR, { recursive: true });
    console.log('  ✅ Removed baseline screenshots');
  }

  console.log('✅ Cleanup complete');
}

/**
 * Complete visual regression workflow
 * @param {Page} page - Playwright page
 * @param {string} testName - Name of the test
 * @param {Object} options - Workflow options
 */
async function runVisualRegression(page, testName, options = {}) {
  const {
    captureBaseline = false,
    compare = true,
    promoteOnPass = false
  } = options;

  console.log(`\n🎨 Visual Regression Workflow: ${testName}\n`);

  let results = {};

  // Capture baseline if requested
  if (captureBaseline) {
    await captureBaselines(page, testName, options);
    results.baselinesCaptured = true;
  }

  // Capture current screenshots
  const captures = await captureCurrents(page, testName, options);
  results.currentsCaptured = captures.length;

  // Compare against baselines
  if (compare) {
    const comparison = await compareWithBaselines(testName, options);
    results.comparison = comparison;

    // Promote to baselines if all passed and promoteOnPass is true
    if (promoteOnPass && comparison.failed === 0) {
      promoteToBaselines(testName);
      results.promoted = true;
    }
  }

  return results;
}

module.exports = {
  VIEWPORTS,
  captureBaselines,
  captureCurrents,
  compareWithBaselines,
  promoteToBaselines,
  listBaselines,
  cleanup,
  runVisualRegression
};
