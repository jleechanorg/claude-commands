#!/usr/bin/env node
/**
 * Universal Playwright Executor for WorldArchitect.AI
 *
 * Handles module resolution, code execution, and cleanup for browser automation.
 * Supports file paths, inline code, and stdin input.
 */

const fs = require('fs');
const path = require('path');

// Switch to skill directory for proper module resolution
process.chdir(__dirname);

/**
 * Clean up old temporary execution files
 */
function cleanupOldTempFiles() {
  const files = fs.readdirSync(__dirname);
  const tempFiles = files.filter(f => f.startsWith('.temp-execution-'));

  tempFiles.forEach(file => {
    try {
      fs.unlinkSync(path.join(__dirname, file));
      console.log(`🧹 Cleaned up old temp file: ${file}`);
    } catch (err) {
      // Ignore cleanup errors
    }
  });
}

/**
 * Get code to execute from various sources
 */
function getCodeToExecute() {
  // Check for file path argument
  if (process.argv[2]) {
    const potentialPath = process.argv[2];

    // Check if it's a file path
    if (fs.existsSync(potentialPath)) {
      console.log(`📄 Reading code from file: ${potentialPath}`);
      return fs.readFileSync(potentialPath, 'utf8');
    }

    // Otherwise treat as inline code
    console.log('💻 Using inline code');
    return process.argv.slice(2).join(' ');
  }

  // Check for stdin (non-TTY means piped input)
  if (!process.stdin.isTTY) {
    console.log('📥 Reading code from stdin');
    return fs.readFileSync(0, 'utf8');
  }

  throw new Error('❌ No code provided. Usage: node run.js <file|code>');
}

/**
 * Wrap code with Playwright boilerplate if needed
 */
function wrapCodeIfNeeded(code) {
  const hasRequire = code.includes('require(') || code.includes('import ');
  const hasAsyncWrapper = code.includes('(async () =>') || code.includes('async function');

  // Code is already complete
  if (hasRequire && hasAsyncWrapper) {
    return code;
  }

  // Add requires if missing
  const requires = hasRequire ? '' : `const { chromium, firefox, webkit, devices } = require('playwright');\n`;

  // Add async wrapper if missing
  if (!hasAsyncWrapper) {
    return `${requires}(async () => {
  try {
    ${code}
  } catch (error) {
    console.error('❌ Execution error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
})();`;
  }

  return requires + code;
}

/**
 * Check and install Playwright if needed
 */
async function ensurePlaywrightInstalled() {
  try {
    require.resolve('playwright');
    console.log('✅ Playwright is installed');
    return true;
  } catch (err) {
    console.log('📦 Playwright not found, installing...');
    console.log('⚠️  This may take a few minutes on first run');

    const { execSync } = require('child_process');

    try {
      execSync('npm install', { cwd: __dirname, stdio: 'inherit' });
      execSync('npx playwright install chromium', { cwd: __dirname, stdio: 'inherit' });
      console.log('✅ Playwright installed successfully');
      return true;
    } catch (installErr) {
      console.error('❌ Failed to install Playwright');
      console.error('Please run: npm install && npx playwright install chromium');
      return false;
    }
  }
}

/**
 * Main execution flow
 */
async function main() {
  console.log('🎭 WorldArchitect Playwright Executor\n');

  // Clean up old temp files
  cleanupOldTempFiles();

  // Ensure Playwright is installed
  const installed = await ensurePlaywrightInstalled();
  if (!installed) {
    process.exit(1);
  }

  try {
    // Get and prepare code
    const code = getCodeToExecute();
    const wrappedCode = wrapCodeIfNeeded(code);

    // Write to temp file with timestamp
    const timestamp = Date.now();
    const tempFile = path.join(__dirname, `.temp-execution-${timestamp}.js`);
    fs.writeFileSync(tempFile, wrappedCode);

    console.log(`\n🚀 Executing test...\n`);

    // Execute the code
    require(tempFile);

    // Note: We don't delete tempFile here - it will be cleaned up on next run
    // This prevents race conditions with async operations

  } catch (error) {
    console.error('\n❌ Execution failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run main function
main().catch(err => {
  console.error('❌ Fatal error:', err);
  process.exit(1);
});
