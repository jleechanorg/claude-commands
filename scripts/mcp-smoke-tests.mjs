#!/usr/bin/env node

/**
 * MCP smoke test runner for WorldArchitect.AI
 *
 * Validates critical MCP functionality against deployed server:
 * 1. /health endpoint returns HTTP 200 with { status: 'healthy' }
 * 2. tools/list exposes 8 D&D campaign tools
 * 3. create_campaign generates campaign with AI story
 * 4. process_action executes gameplay with dice mechanics
 * 5. Error handling for invalid inputs
 *
 * Test modes (BOTH hit real server):
 * - mock: Quick validation - tests server endpoints without full campaign workflows
 * - real: Full validation - complete campaign creation and gameplay testing
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

// Setup automatic log file output to /tmp
const getRepoName = () => {
  try {
    return execSync('basename $(git rev-parse --show-toplevel)', { encoding: 'utf8' }).trim();
  } catch {
    return 'worldarchitect.ai';
  }
};

const getBranchName = () => {
  try {
    return execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim().replace(/\//g, '-');
  } catch {
    return 'unknown';
  }
};

const LOG_DIR = `/tmp/${getRepoName()}/${getBranchName()}/smoke_tests`;
const LOG_FILE = path.join(LOG_DIR, 'mcp_output.log');
let logStream = null;

// Create log directory and file
try {
  fs.mkdirSync(LOG_DIR, { recursive: true });
  logStream = fs.createWriteStream(LOG_FILE, { flags: 'w' });
  console.log(`📝 Logging to: ${LOG_FILE}\n`);
} catch (error) {
  console.warn(`⚠️  Could not create log file: ${error.message}`);
}

// Override console methods to also write to file
const originalLog = console.log;
const originalError = console.error;

console.log = (...args) => {
  originalLog(...args);
  if (logStream) logStream.write(args.join(' ') + '\n');
};

console.error = (...args) => {
  originalError(...args);
  if (logStream) logStream.write(args.join(' ') + '\n');
};

// Test mode: 'mock' (default) or 'real'
const testMode = (process.env.MCP_TEST_MODE || 'mock').toLowerCase();
const useQuickValidation = testMode === 'mock';

const rawBaseUrl = process.env.MCP_SERVER_URL ? String(process.env.MCP_SERVER_URL).trim() : '';

// MCP_SERVER_URL is ALWAYS required - both modes hit the real server
if (!rawBaseUrl) {
  console.error('❌ MCP_SERVER_URL environment variable is required');
  console.error('💡 Example: export MCP_SERVER_URL=https://mvp-site-app-pr-123.run.app');
  console.error('💡 Test modes:');
  console.error('   - mock: Quick validation (health + tools/list only)');
  console.error('   - real: Full validation (complete campaign workflows)');
  process.exit(1);
}

const effectiveBaseUrl = rawBaseUrl;

const parsePositiveInt = (value, fallback) => {
  if (value === undefined) {
    return fallback;
  }
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed <= 0) {
    throw new Error(`Expected positive integer but received "${value}"`);
  }
  return parsed;
};

const timeoutMs = parsePositiveInt(process.env.MCP_TEST_TIMEOUT_MS, 60000); // 60 seconds default
const retryAttempts = parsePositiveInt(process.env.MCP_TEST_MAX_ATTEMPTS, 3);
const retryDelayMs = parsePositiveInt(process.env.MCP_TEST_RETRY_DELAY_MS, 2000);

const normalizedBaseUrl = effectiveBaseUrl.replace(/\/$/, '');
const serverBaseUrl = normalizedBaseUrl.endsWith('/mcp')
  ? normalizedBaseUrl.slice(0, -4)
  : normalizedBaseUrl;
const healthUrl = serverBaseUrl.endsWith('/health') ? serverBaseUrl : `${serverBaseUrl}/health`;
const mcpEndpoint = normalizedBaseUrl.endsWith('/mcp') ? normalizedBaseUrl : `${normalizedBaseUrl}/mcp`;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Logging
const logEntries = [];

const addLogEntry = (entry) => {
  logEntries.push({
    timestamp: new Date().toISOString(),
    ...entry,
  });
};

const logInfo = (message) => {
  console.log(message);
  addLogEntry({ kind: 'info', message });
};

const logError = (message) => {
  console.error(message);
  addLogEntry({ kind: 'error', message });
};

const withTimeout = async (promiseFactory, ms, description) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await promiseFactory(controller.signal);
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error(`${description} timed out after ${ms}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
};

async function fetchJson(url, init, description) {
  return withTimeout(
    async (signal) => {
      const method = init?.method ?? 'GET';
      logInfo(`[HTTP][${description}] → ${method} ${url}`);

      // ALWAYS hit the real server - no mock bypass
      const response = await fetch(url, { ...init, signal });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const rawText = await response.text();
      try {
        return JSON.parse(rawText);
      } catch (error) {
        throw new Error(
          `${description} returned invalid JSON: ${error instanceof Error ? error.message : String(error)}\nResponse body: ${rawText}`,
        );
      }
    },
    timeoutMs,
    description,
  );
}

async function retry(fn, description) {
  let lastError;
  for (let attempt = 1; attempt <= retryAttempts; attempt += 1) {
    try {
      if (attempt > 1) {
        logInfo(`🔁 Retry attempt ${attempt}/${retryAttempts} for ${description}`);
      }
      return await fn();
    } catch (error) {
      lastError = error;
      if (attempt === retryAttempts) {
        break;
      }
      const backoff = retryDelayMs * attempt;
      logInfo(`⚠️ ${description} attempt ${attempt} failed: ${error instanceof Error ? error.message : String(error)}. Retrying in ${backoff}ms...`);
      await sleep(backoff);
    }
  }
  throw lastError ?? new Error(`${description} failed after ${retryAttempts} attempts`);
}

function logStep(message) {
  const formatted = `🔍 ${message}`;
  console.log(`\n${formatted}`);
  addLogEntry({ kind: 'step', message });
}

// Test functions
async function checkHealthEndpoint() {
  logStep(`Checking health endpoint at ${healthUrl}`);
  const payload = await retry(
    () => fetchJson(healthUrl, { method: 'GET', headers: { Accept: 'application/json' } }, 'Health endpoint request'),
    'health endpoint verification',
  );

  if (payload?.status !== 'healthy') {
    throw new Error(`Unexpected health status: ${JSON.stringify(payload)}`);
  }

  logInfo('✅ Health endpoint returned healthy status');
  return payload;
}

const generateRpcId = () => Date.now() + Math.floor(Math.random() * 1000);

async function callRpc(method, params = {}, id = generateRpcId()) {
  logInfo(`➡️  RPC call: ${method} (id: ${id})`);

  // ALWAYS hit the real server - no mock bypass
  const response = await retry(
    () => fetchJson(
      mcpEndpoint,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ jsonrpc: '2.0', id, method, params }),
      },
      `RPC ${method}`,
    ),
    `RPC ${method}`,
  );

  return response;
}

async function checkToolsList() {
  logStep('Testing tools/list endpoint');
  const payload = await callRpc('tools/list');

  if (!payload?.result?.tools || !Array.isArray(payload.result.tools)) {
    throw new Error(`tools/list returned invalid response: ${JSON.stringify(payload)}`);
  }

  const toolCount = payload.result.tools.length;
  if (toolCount !== 8) {
    throw new Error(`Expected 8 tools, found ${toolCount}`);
  }

  const requiredTools = ['create_campaign', 'get_campaign_state', 'process_action'];
  const toolNames = payload.result.tools.map(t => t.name);

  for (const required of requiredTools) {
    if (!toolNames.includes(required)) {
      throw new Error(`Missing required tool: ${required}`);
    }
  }

  logInfo(`✅ tools/list returned ${toolCount} tools including all required ones`);
  return payload;
}

async function testCampaignCreation(userId) {
  logStep('Testing campaign creation via create_campaign tool');

  const payload = await callRpc(
    'tools/call',
    {
      name: 'create_campaign',
      arguments: {
        user_id: userId,
        title: 'Smoke Test Campaign',
        character: 'Test Hero, Fighter',
        setting: 'Test dungeon for smoke tests',
        description: 'Automated MCP smoke test scenario',
        selected_prompts: ['mechanicalPrecision'],
        custom_options: [],
        debug_mode: true
      }
    }
  );

  if (payload?.error) {
    throw new Error(`create_campaign returned error: ${JSON.stringify(payload.error)}`);
  }

  const result = payload?.result;
  if (!result?.campaign_id) {
    throw new Error(`create_campaign missing campaign_id: ${JSON.stringify(result)}`);
  }

  logInfo(`✅ Campaign created: ${result.campaign_id}`);
  addLogEntry({
    kind: 'campaign-created',
    campaign_id: result.campaign_id,
    title: result.title,
    full_response: result
  });

  return result;
}

async function testCampaignCreationWithDefaultWorld(userId) {
  logStep('Testing campaign creation with defaultWorld enabled');

  const payload = await callRpc(
    'tools/call',
    {
      name: 'create_campaign',
      arguments: {
        user_id: userId,
        title: 'Smoke Test Campaign - Default World',
        character: '',
        setting: 'World of Assiah. Caught between an oath to a ruthless tyrant and a vow to protect the innocent.',
        selected_prompts: ['defaultWorld', 'mechanicalPrecision'],
        custom_options: ['defaultWorld'],
        debug_mode: true
      }
    }
  );

  if (payload?.error || payload?.result?.error) {
    const error = payload.error ?? payload.result?.error;
    const errorMsg = JSON.stringify(error);
    const isFileError =
      error?.code === 'FILE_NOT_FOUND' ||
      errorMsg.includes('FileNotFoundError') ||
      errorMsg.includes('world_assiah_compressed.md');
    // Check for FileNotFoundError which indicates missing world files
    if (isFileError) {
      throw new Error(
        `❌ WORLD FILE DEPLOYMENT ISSUE: ${errorMsg}\n` +
        '💡 The world directory may not be included in the Docker build.\n' +
        '   Check deploy.sh world directory copy logic.'
      );
    }
    throw new Error(`create_campaign with defaultWorld returned error: ${errorMsg}`);
  }

  const result = payload?.result;
  if (!result?.campaign_id) {
    throw new Error(`create_campaign with defaultWorld missing campaign_id: ${JSON.stringify(result)}`);
  }

  logInfo(`✅ Campaign with defaultWorld created: ${result.campaign_id}`);
  addLogEntry({
    kind: 'campaign-created-defaultworld',
    campaign_id: result.campaign_id,
    title: result.title,
    full_response: result
  });

  return result;
}

async function testGameplayAction(userId, campaignId, contextLabel = 'campaign') {
  logStep(`Testing gameplay action via process_action tool (${contextLabel})`);

  const payload = await callRpc(
    'tools/call',
    {
      name: 'process_action',
      arguments: {
        user_id: userId,
        campaign_id: campaignId,
        user_input: 'I search for clues in the room.',
        debug_mode: true
      }
    }
  );

  if (payload?.error) {
    throw new Error(`process_action returned error: ${JSON.stringify(payload.error)}`);
  }

  const result = payload?.result;
  if (!result?.narrative) {
    throw new Error(`process_action missing narrative: ${JSON.stringify(result)}`);
  }

  // Check for dice rolls in the response
  const diceRolls = result.dice_rolls ?? [];
  if (diceRolls.length === 0) {
    logInfo('⚠️  No dice rolls in action result (may be expected for some actions)');
  } else {
    const successMessage = `✅ Gameplay action for ${contextLabel} completed with ${diceRolls.length} dice roll(s)`;
    logInfo(successMessage);
    addLogEntry({
      kind: 'gameplay',
      campaign_id: campaignId,
      dice_rolls: diceRolls.length,
      message: successMessage,
    });
  }

  addLogEntry({
    kind: 'gameplay-action',
    campaign_id: campaignId,
    dice_rolls_count: result.dice_rolls?.length || 0,
    narrative_length: result.narrative?.length || 0,
    full_response: result
  });

  return result;
}

async function testErrorHandling() {
  logStep('Testing error handling for invalid inputs');

  // Test 1: Invalid campaign ID
  const payload1 = await callRpc(
    'tools/call',
    {
      name: 'get_campaign_state',
      arguments: {
        user_id: 'smoke-test',
        campaign_id: 'INVALID_CAMPAIGN_ID_12345'
      }
    }
  );

  // Check for JSON-RPC 2.0 error (top-level error field) or result.error
  if (!payload1?.error && !payload1?.result?.error) {
    throw new Error('Expected error for invalid campaign ID, got success');
  }

  logInfo('✅ Invalid campaign ID properly returns error');

  // Test 2: Missing required parameters
  const payload2 = await callRpc(
    'tools/call',
    {
      name: 'process_action',
      arguments: {
        user_id: 'smoke-test'
        // Missing campaign_id
      }
    }
  );

  // Check for JSON-RPC 2.0 error (top-level error field) or result.error
  if (!payload2?.error && !payload2?.result?.error) {
    throw new Error('Expected error for missing campaign_id, got success');
  }

  logInfo('✅ Missing required parameters properly returns error');
}

// Main test execution
async function main() {
  console.log('========================================');
  console.log(`🧪 MCP Smoke Tests - ${testMode.toUpperCase()} MODE`);
  console.log('========================================\n');

  if (useQuickValidation) {
    console.log('⚡ Quick Validation Mode - Testing server endpoints only');
    console.log(`🌐 Target server: ${effectiveBaseUrl}`);
    console.log('💡 Use MCP_TEST_MODE=real for full campaign workflow testing\n');
  } else {
    console.log('🔍 Full Validation Mode - Complete campaign workflow testing');
    console.log(`🌐 Target server: ${effectiveBaseUrl}\n`);
  }

  try {
    // Test 1: Health endpoint (ALWAYS run)
    await checkHealthEndpoint();

    // Test 2: Tools list (ALWAYS run)
    await checkToolsList();

    // Tests 3-5: Full campaign workflows (ONLY in real mode)
    if (!useQuickValidation) {
      // Generate consistent user ID for campaign tests
      const userId = `smoke-test-${Date.now()}`;

      // Test 3: Campaign creation (basic)
      const campaign = await testCampaignCreation(userId);

      // Test 3b: Campaign creation with defaultWorld (catches missing world files)
      const defaultWorldCampaign = await testCampaignCreationWithDefaultWorld(userId);

      // Test 4: Gameplay action (only if we got a real campaign ID)
      if (campaign.campaign_id) {
        await testGameplayAction(userId, campaign.campaign_id, 'basic campaign');
      }

      // Test 4b: Gameplay with defaultWorld campaign (verifies campaign can progress)
      if (defaultWorldCampaign.campaign_id) {
        await testGameplayAction(userId, defaultWorldCampaign.campaign_id, 'defaultWorld campaign');
      }

      // Test 5: Error handling
      await testErrorHandling();
    } else {
      logInfo('⚡ Quick validation complete - skipping full campaign workflows');
      logInfo('   (Campaign creation, gameplay, and error handling tests run in REAL mode only)');
    }

    console.log('\n========================================');
    console.log('✅ ALL SMOKE TESTS PASSED');
    console.log('========================================\n');

    // Save log entries to JSON file
    const jsonLogPath = path.join(LOG_DIR, 'test_results.json');
    fs.writeFileSync(jsonLogPath, JSON.stringify({
      status: 'success',
      mode: testMode,
      timestamp: new Date().toISOString(),
      logs: logEntries
    }, null, 2));
    console.log(`📄 Test results saved to: ${jsonLogPath}`);

    if (logStream) {
      logStream.end();
    }

    process.exit(0);
  } catch (error) {
    console.log('\n========================================');
    console.log('❌ SMOKE TESTS FAILED');
    console.log('========================================\n');
    logError(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);

    if (error instanceof Error && error.stack) {
      console.error(error.stack);
    }

    // Save failure log
    const jsonLogPath = path.join(LOG_DIR, 'test_results.json');
    fs.writeFileSync(jsonLogPath, JSON.stringify({
      status: 'failed',
      mode: testMode,
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : String(error),
      logs: logEntries
    }, null, 2));
    console.log(`📄 Failure log saved to: ${jsonLogPath}`);

    if (logStream) {
      logStream.end();
    }

    process.exit(1);
  }
}

main();
