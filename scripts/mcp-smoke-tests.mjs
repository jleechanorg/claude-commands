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
import os from 'node:os';
import crypto from 'node:crypto';
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
const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
const LOG_FILE = path.join(LOG_DIR, `mcp_output_${timestamp}.log`);
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

const timeoutMs = parsePositiveInt(process.env.MCP_TEST_TIMEOUT_MS, 600000); // 10 minutes default
const retryAttempts = parsePositiveInt(process.env.MCP_TEST_MAX_ATTEMPTS, 3);
const retryDelayMs = parsePositiveInt(process.env.MCP_TEST_RETRY_DELAY_MS, 2000);

const providerDefaults = {
  gemini: {
    // Cost-efficient default (Gemini 3 is 20x more expensive and restricted to allowlisted users)
    // Uses response_json_schema for structured output enforcement
    gemini_model: process.env.MCP_GEMINI_MODEL || 'gemini-2.0-flash',
  },
  openrouter: {
    // Must match backend allowlist (constants.ALLOWED_OPENROUTER_MODELS)
    // Note: Llama models don't enforce json_schema - use 'openrouter_grok' for strict schema testing
    openrouter_model:
      process.env.MCP_OPENROUTER_MODEL || 'meta-llama/llama-3.1-70b-instruct',
  },
  openrouter_grok: {
    // Grok 4.1 Fast - ONLY OpenRouter model that enforces json_schema with strict mode
    // Use this provider to test structured output enforcement on OpenRouter
    openrouter_model: 'x-ai/grok-4.1-fast',
  },
  cerebras: {
    // Qwen 3 235B (a22b-instruct-2507) - highest context (131K) and best for RPG campaigns
    // Uses json_schema with strict:false to allow dynamic choice keys in planning_block
    cerebras_model: process.env.MCP_CEREBRAS_MODEL || 'qwen-3-235b-a22b-instruct-2507',
  },
};

const bearerToken = process.env.MCP_BEARER_TOKEN;
let effectiveBearerToken = bearerToken;
let bearerTokenLoadedPromise = null;
const TOKEN_EXPIRY_SKEW_MS = 5 * 60 * 1000; // refresh if expiring within 5 minutes
const FALLBACK_FIREBASE_API_KEY =
  process.env.FIREBASE_API_KEY ||
  process.env.WORLDAI_FIREBASE_API_KEY ||
  process.env.AI_UNIVERSE_FIREBASE_API_KEY ||
  'AIzaSyARs7IekRptvhZIwtV7lwJh3axWFsn_4c8'; // worldarchitecture-ai public web key

function isTokenExpiring(expiresAt) {
  if (!expiresAt) return true;
  const expMs = Date.parse(expiresAt);
  if (Number.isNaN(expMs)) return true;
  return expMs - Date.now() <= TOKEN_EXPIRY_SKEW_MS;
}

async function refreshIdToken(refreshToken) {
  const apiKey = FALLBACK_FIREBASE_API_KEY;
  if (!apiKey || !refreshToken) return null;
  try {
    const res = await fetch(
      `https://securetoken.googleapis.com/v1/token?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          grant_type: 'refresh_token',
          refresh_token: refreshToken,
        }).toString(),
      },
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    const data = await res.json();
    if (data.id_token) {
      return {
        idToken: data.id_token,
        refreshToken: data.refresh_token || refreshToken,
        expiresAt: new Date(Date.now() + Number(data.expires_in) * 1000).toISOString(),
      };
    }
  } catch (error) {
    console.warn(`⚠️  Token refresh failed: ${error.message}`);
  }
  return null;
}

function loadBearerTokenFromFile() {
  try {
    const candidatePaths = [
      path.join(os.homedir(), '.worldarchitect-ai', 'auth-token.json'),
      path.join(os.homedir(), '.ai-universe', 'auth-token.json'),
    ];

    for (const tokenPath of candidatePaths) {
      if (fs.existsSync(tokenPath)) {
        const raw = fs.readFileSync(tokenPath, 'utf-8');
        const data = JSON.parse(raw);
        if (data?.idToken) {
          console.log(`🔑 Loaded bearer token from ${tokenPath}`);
          return data;
        }
      }
    }
  } catch (error) {
    console.warn(`⚠️  Could not load bearer token: ${error.message}`);
  }
  return null;
}

async function loginWithPassword() {
  const email = process.env.TEST_EMAIL || process.env.GOOGLE_TEST_EMAIL;
  const password = process.env.TEST_PASSWORD || process.env.GOOGLE_TEST_PASSWORD;
  const apiKey = process.env.FIREBASE_API_KEY || FALLBACK_FIREBASE_API_KEY;

  if (!email || !password || !apiKey) {
    console.warn('⚠️  Missing TEST_EMAIL/TEST_PASSWORD/FIREBASE_API_KEY; cannot perform password login');
    return null;
  }

  try {
    const res = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, returnSecureToken: true }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    const data = await res.json();
    if (data?.idToken) {
      console.log('🔑 Acquired bearer token via password login');
      return data.idToken;
    }
  } catch (error) {
    console.warn(`⚠️  Password login failed: ${error.message}`);
  }
  return null;
}

function readServiceAccountKey() {
  const keyPath = process.env.MCP_SERVICE_ACCOUNT_KEY || process.env.GOOGLE_APPLICATION_CREDENTIALS;
  if (!keyPath) return null;
  try {
    const raw = fs.readFileSync(keyPath, 'utf-8');
    const json = JSON.parse(raw);
    if (json.client_email && json.private_key) {
      return { clientEmail: json.client_email, privateKey: json.private_key };
    }
  } catch (error) {
    console.warn(`⚠️  Could not load service account key: ${error.message}`);
  }
  return null;
}
function base64UrlEncode(input) {
  return Buffer.from(input)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

function createCustomToken(uid) {
  const sa = readServiceAccountKey();
  if (!sa) return null;
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'RS256', typ: 'JWT' };
  const payload = {
    iss: sa.clientEmail,
    sub: sa.clientEmail,
    aud: 'https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit',
    uid,
    iat: now,
    exp: now + 3600,
  };
  const signingInput = `${base64UrlEncode(JSON.stringify(header))}.${base64UrlEncode(JSON.stringify(payload))}`;
  const signer = crypto.createSign('RSA-SHA256');
  signer.update(signingInput);
  const signature = signer.sign(sa.privateKey);
  return `${signingInput}.${base64UrlEncode(signature)}`;
}

async function exchangeCustomToken(customToken) {
  if (!customToken) return null;
  const apiKey = FALLBACK_FIREBASE_API_KEY;
  try {
    const res = await fetch(
      `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: customToken, returnSecureToken: true }),
      },
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    const data = await res.json();
    if (data?.idToken) {
      console.log('🔑 Acquired bearer token via service account custom token');
      return {
        idToken: data.idToken,
        refreshToken: data.refreshToken,
        expiresAt: new Date(Date.now() + Number(data.expiresIn || 3600) * 1000).toISOString(),
      };
    }
  } catch (error) {
    console.warn(`⚠️  Custom token exchange failed: ${error.message}`);
  }
  return null;
}

async function getBearerToken() {
  if (effectiveBearerToken) return effectiveBearerToken;
  if (!bearerTokenLoadedPromise) {
    bearerTokenLoadedPromise = (async () => {
      // Try password login first
      const fromLogin = await loginWithPassword();
      if (fromLogin) return fromLogin;

      // Then try stored token
      const stored = loadBearerTokenFromFile();
      if (stored) {
        const { idToken, refreshToken, expiresAt } = stored;
        if (!isTokenExpiring(expiresAt)) return idToken;
        const refreshed = await refreshIdToken(refreshToken);
        if (refreshed?.idToken) {
          console.log('🔄 Refreshed bearer token from stored refreshToken');
          return refreshed.idToken;
        }
        return idToken; // fall back to stored token even if refresh failed
      }

      // Finally, try service account → custom token → ID token (works in CI with GCP_SA_KEY)
      const custom = createCustomToken('smoke-test-user');
      if (custom) {
        const exchanged = await exchangeCustomToken(custom);
        if (exchanged?.idToken) return exchanged.idToken;
      }

      return null;
    })();
  }
  effectiveBearerToken = await bearerTokenLoadedPromise;
  return effectiveBearerToken;
}

// Default to Cerebras (cheapest real API) for smoke tests
// Can override with MCP_TEST_PROVIDERS env var
// Examples:
//   - 'cerebras' (default) - cheapest, tests json_schema
//   - 'gemini,cerebras,openrouter_grok' - all providers with json_schema enforcement
//   - 'gemini,openrouter,cerebras' - all providers (openrouter uses Llama without strict schema)
// Note: 'openrouter_grok' tests Grok 4.1 which enforces json_schema; 'openrouter' tests Llama which doesn't
const providersToTest = (process.env.MCP_TEST_PROVIDERS || 'cerebras')
  .split(',')
  .map((p) => p.trim())
  .filter(Boolean)
  .filter((p) => {
    if (!providerDefaults[p]) {
      console.warn(`⚠️  Unknown provider '${p}' - skipping. Valid options: ${Object.keys(providerDefaults).join(', ')}`);
      return false;
    }
    return true;
  });

const normalizedBaseUrl = effectiveBaseUrl.replace(/\/$/, '');
const serverBaseUrl = normalizedBaseUrl.endsWith('/mcp')
  ? normalizedBaseUrl.slice(0, -4)
  : normalizedBaseUrl;
const settingsBaseUrl = process.env.MCP_SETTINGS_BASE_URL
  ? String(process.env.MCP_SETTINGS_BASE_URL).replace(/\/$/, '')
  : serverBaseUrl;
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

async function updateUserSettings(userId, provider) {
  if (!providerDefaults[provider]) {
    throw new Error(`Unknown provider: ${provider}. Valid options: ${Object.keys(providerDefaults).join(', ')}`);
  }

  // Map openrouter_grok to openrouter provider with Grok model
  const actualProvider = provider === 'openrouter_grok' ? 'openrouter' : provider;
  const settingsPayload = { llm_provider: actualProvider };

  if (provider === 'openrouter' || provider === 'openrouter_grok') {
    settingsPayload.openrouter_model = providerDefaults[provider].openrouter_model;
  } else if (provider === 'cerebras') {
    settingsPayload.cerebras_model = providerDefaults.cerebras.cerebras_model;
  } else if (provider === 'gemini') {
    settingsPayload.gemini_model = providerDefaults.gemini.gemini_model;
  } else {
    throw new Error(`Unhandled provider in settings update: ${provider}`);
  }

  const url = `${serverBaseUrl}/api/settings`;
  const settingsUrl = `${settingsBaseUrl}/api/settings`;
  logStep(`Updating settings for ${provider} via ${url}`);

  const headers = {
    'Content-Type': 'application/json',
  };

  const token = await getBearerToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else {
    headers['X-Test-Bypass-Auth'] = 'true';
    headers['X-Test-User-ID'] = userId;
  }

  await fetchJson(
    settingsUrl,
    {
      method: 'POST',
      headers,
      body: JSON.stringify(settingsPayload),
    },
    `Update settings (${provider})`,
  );
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

async function testCampaignCreation(userId, providerLabel = 'gemini') {
  logStep(`Testing campaign creation via create_campaign tool (${providerLabel})`);

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
    provider: providerLabel,
    campaign_id: result.campaign_id,
    title: result.title,
    full_response: result
  });

  return result;
}

async function testCampaignCreationWithDefaultWorld(userId, providerLabel = 'gemini') {
  logStep(`Testing campaign creation with defaultWorld enabled (${providerLabel})`);

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
    provider: providerLabel,
    campaign_id: result.campaign_id,
    title: result.title,
    full_response: result
  });

  return result;
}

async function testGameplayAction(userId, campaignId, contextLabel = 'campaign', providerLabel = 'gemini') {
  logStep(`Testing gameplay action via process_action tool (${contextLabel}, ${providerLabel})`);

  const payload = await callRpc(
    'tools/call',
    {
      name: 'process_action',
      arguments: {
        user_id: userId,
        campaign_id: campaignId,
        user_input: 'A goblin lunges at me with a rusty dagger! I swing my sword to defend myself and strike back. Roll my attack to see if I hit.',
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
    // Validate dice roll format - should show pre-rolled dice values used by LLM
    // Expected format: "Perception: 1d20+3 = 15+3 = 18 vs DC 15 (Success)"
    // The roll value (15) should come from pre_rolled_dice, not be generated by LLM
    for (const roll of diceRolls) {
      if (typeof roll !== 'string') {
        throw new Error(`dice_rolls entry is not a string: ${JSON.stringify(roll)}`);
      }
      // Check that dice roll strings contain expected format elements
      const hasRollFormat = /\d+d\d+/.test(roll);  // e.g., "1d20" or "2d6"
      const hasResult = /=\s*\d+/.test(roll);      // e.g., "= 15" or "= 18"
      if (!hasRollFormat) {
        logInfo(`⚠️  Dice roll missing notation format: "${roll}"`);
      }
      if (!hasResult) {
        logInfo(`⚠️  Dice roll missing result value: "${roll}"`);
      }
    }
    const successMessage = `✅ Gameplay action for ${contextLabel} completed with ${diceRolls.length} dice roll(s)`;
    logInfo(successMessage);
    logInfo(`   📊 Dice rolls: ${JSON.stringify(diceRolls)}`);
    addLogEntry({
      kind: 'gameplay',
      campaign_id: campaignId,
      dice_rolls: diceRolls.length,
      dice_roll_strings: diceRolls,
      message: successMessage,
    });
  }

  addLogEntry({
    kind: 'gameplay-action',
    campaign_id: campaignId,
    dice_rolls_count: result.dice_rolls?.length || 0,
    narrative_length: result.narrative?.length || 0,
    provider: providerLabel,
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
      for (const provider of providersToTest) {
        // Generate consistent user ID for campaign tests
        const userId = `smoke-test-${provider}-${Date.now()}`;

        await updateUserSettings(userId, provider);

        // Test 3: Campaign creation (basic)
        const campaign = await testCampaignCreation(userId, provider);

        // Test 3b: Campaign creation with defaultWorld (catches missing world files)
        const defaultWorldCampaign = await testCampaignCreationWithDefaultWorld(
          userId,
          provider,
        );

        // Test 4: Gameplay action (only if we got a real campaign ID)
        if (campaign.campaign_id) {
          await testGameplayAction(userId, campaign.campaign_id, 'basic campaign', provider);
        }

        // Test 4b: Gameplay with defaultWorld campaign (verifies campaign can progress)
        if (defaultWorldCampaign.campaign_id) {
          await testGameplayAction(
            userId,
            defaultWorldCampaign.campaign_id,
            'defaultWorld campaign',
            provider,
          );
        }
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
