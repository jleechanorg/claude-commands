#!/usr/bin/env node

/**
 * Multi-project Firebase CLI Authentication Tool (AI Universe by default)
 *
 * Implements browser-based OAuth flow with localhost callback server
 * Pattern used by: gcloud CLI, Firebase CLI, GitHub CLI
 *
 * Usage:
 *   node scripts/auth-cli.mjs login                    # Login to ai-universe (default)
 *   node scripts/auth-cli.mjs login --project custom   # Login to custom project
 *   node scripts/auth-cli.mjs logout
 *   node scripts/auth-cli.mjs status
 *   node scripts/auth-cli.mjs token
 */

import express from 'express';
import { createServer } from 'http';
import { readFile, writeFile, unlink, mkdir, chmod } from 'fs/promises';
import { existsSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';
import { spawn } from 'child_process';

// Constants
const TOKEN_EXPIRATION_MS = 3600000; // 1 hour
const AUTH_TIMEOUT_MS = 300000; // 5 minutes
const REFRESH_TOKEN_URL = 'https://securetoken.googleapis.com/v1/token';

// Default project configuration (AI Universe)
const DEFAULT_PROJECT = {
  id: 'ai-universe-b3551',
  authDomain: 'ai-universe-b3551.firebaseapp.com',
  envPrefix: 'VITE_AI_UNIVERSE_FIREBASE',
  name: 'AI Universe'
};

// Known project configurations for convenience
const KNOWN_PROJECTS = {
  'ai-universe-b3551': DEFAULT_PROJECT,
  'worldarchitecture-ai': {
    id: 'worldarchitecture-ai',
    authDomain: 'worldarchitecture-ai.firebaseapp.com',
    envPrefix: 'VITE_FIREBASE',
    name: 'World Architecture AI'
  }
};

/**
 * Parse command-line arguments for --project flag
 */
function parseArgs() {
  const args = process.argv.slice(2);
  let command = null;
  let projectOverride = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--project' || args[i] === '-p') {
      if (!args[i + 1] || args[i + 1].startsWith('-')) {
        console.error('❌ --project flag requires a value');
        process.exit(1);
      }
      projectOverride = args[i + 1];
      i++; // Skip next arg
    } else if (!args[i].startsWith('-')) {
      command = args[i];
    }
  }

  return { command, projectOverride };
}

const { command: parsedCommand, projectOverride } = parseArgs();

/**
 * Get project configuration based on --project flag or default
 */
function getProjectConfig(projectOverride) {
  // If no override, use AI Universe (default)
  if (!projectOverride) {
    return DEFAULT_PROJECT;
  }

  // Check known projects first
  const knownProject = KNOWN_PROJECTS[projectOverride];
  if (knownProject) {
    return knownProject;
  }

  // Assume custom project ID format: project-id
  return {
    id: projectOverride,
    authDomain: `${projectOverride}.firebaseapp.com`,
    envPrefix: `VITE_${projectOverride.toUpperCase().replace(/-/g, '_')}_FIREBASE`,
    name: projectOverride
  };
}

const ACTIVE_PROJECT = getProjectConfig(projectOverride);

// Project-specific constants (derived from ACTIVE_PROJECT for backwards compatibility)
const EXPECTED_FIREBASE_PROJECT_ID = ACTIVE_PROJECT.id;
const EXPECTED_FIREBASE_AUTH_DOMAIN = ACTIVE_PROJECT.authDomain;

// Configuration
const REQUIRED_API_KEY_PLACEHOLDER = `__REQUIRED_${ACTIVE_PROJECT.id.toUpperCase().replace(/-/g, '_')}_FIREBASE_API_KEY__`;

const CONFIG = {
  // Firebase config - reads from environment with project-specific prefix
  firebaseConfig: {
    apiKey: process.env[`${ACTIVE_PROJECT.envPrefix}_API_KEY`] || REQUIRED_API_KEY_PLACEHOLDER,
    authDomain: process.env[`${ACTIVE_PROJECT.envPrefix}_AUTH_DOMAIN`] || ACTIVE_PROJECT.authDomain,
    projectId: process.env[`${ACTIVE_PROJECT.envPrefix}_PROJECT_ID`] || ACTIVE_PROJECT.id
  },
  callbackPort: 9005,
  callbackPath: '/auth/callback',
  tokenPath: join(homedir(), '.ai-universe', `auth-token-${ACTIVE_PROJECT.id}.json`),
  productionMcpUrl: 'https://ai-universe-backend-final.onrender.com/mcp',
  activeProject: ACTIVE_PROJECT
};

// Validate required configuration
function validateConfig() {
  const missingEnvVars = [];
  const envPrefix = ACTIVE_PROJECT.envPrefix;

  if (CONFIG.firebaseConfig.apiKey === REQUIRED_API_KEY_PLACEHOLDER) {
    missingEnvVars.push(`${envPrefix}_API_KEY (${ACTIVE_PROJECT.name} web API key)`);
  }

  if (missingEnvVars.length > 0) {
    console.error(`❌ Firebase configuration missing for ${ACTIVE_PROJECT.name}.`);
    if (ACTIVE_PROJECT.id === 'ai-universe-b3551') {
      console.error('   Please run: ./scripts/setup-firebase-config.sh');
      console.error('');
    }
    console.error('Or set environment variables:');
    for (const variable of missingEnvVars) {
      console.error(`   ${variable}`);
    }
    process.exit(1);
  }

  if (CONFIG.firebaseConfig.projectId !== EXPECTED_FIREBASE_PROJECT_ID) {
    console.error(`❌ ${envPrefix}_PROJECT_ID must be set to "${EXPECTED_FIREBASE_PROJECT_ID}" (found "${CONFIG.firebaseConfig.projectId}").`);
    console.error(`   Run: export ${envPrefix}_PROJECT_ID=${EXPECTED_FIREBASE_PROJECT_ID}`);
    process.exit(1);
  }

  if (CONFIG.firebaseConfig.authDomain !== EXPECTED_FIREBASE_AUTH_DOMAIN) {
    console.error(`❌ ${envPrefix}_AUTH_DOMAIN must be "${EXPECTED_FIREBASE_AUTH_DOMAIN}" (found "${CONFIG.firebaseConfig.authDomain}").`);
    console.error(`   Run: export ${envPrefix}_AUTH_DOMAIN=${EXPECTED_FIREBASE_AUTH_DOMAIN}`);
    process.exit(1);
  }
}

// Ensure token directory exists when needed
const tokenDir = join(homedir(), '.ai-universe');

async function ensureTokenDir() {
  if (!existsSync(tokenDir)) {
    await mkdir(tokenDir, { recursive: true, mode: 0o700 });
  }
}

async function writeTokenFile(tokenData) {
  await ensureTokenDir();
  await writeFile(CONFIG.tokenPath, JSON.stringify(tokenData, null, 2));
  await chmod(CONFIG.tokenPath, 0o600);
}

/**
 * Open URL in default browser (cross-platform)
 */
function openBrowser(url) {
  const platform = process.platform;
  let command;
  let args;

  if (platform === 'darwin') {
    command = 'open';
    args = [url];
  } else if (platform === 'win32') {
    command = 'cmd';
    args = ['/c', 'start', '', url];
  } else {
    command = 'xdg-open';
    args = [url];
  }

  const child = spawn(command, args, { detached: true, stdio: 'ignore' });
  child.on('error', (err) => {
    console.error('⚠️  Failed to open browser automatically:', err.message);
    console.error(`   Please open ${url} manually in your browser.`);
  });
  child.unref();
  return child;
}

/**
 * Decode JWT payload (base64url)
 * @param {string} token
 * @returns {Record<string, unknown>}
 */
function decodeJwtPayload(token) {
  const parts = token.split('.');
  if (parts.length < 2) {
    throw new Error('Token has an invalid format.');
  }

  const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
  const json = Buffer.from(padded, 'base64').toString('utf-8');

  try {
    return JSON.parse(json);
  } catch (error) {
    throw new Error(`Token payload is not valid JSON: ${(error instanceof Error && error.message) || String(error)}`);
  }
}

/**
 * Ensure the Firebase token belongs to the expected project.
 * @param {string} idToken
 * @param {string} context
 * @returns {{ projectId: string, issuer: string }}
 */
function validateTokenProject(idToken, context) {
  const payload = decodeJwtPayload(idToken);
  const aud = typeof payload.aud === 'string' ? payload.aud : null;
  const iss = typeof payload.iss === 'string' ? payload.iss : null;

  if (aud !== EXPECTED_FIREBASE_PROJECT_ID) {
    throw new Error(
      `[${context}] Token project mismatch: expected "${EXPECTED_FIREBASE_PROJECT_ID}", received "${aud || 'unknown'}". ` +
      `Run \`node scripts/auth-cli.mjs login --project ${ACTIVE_PROJECT.id}\` for ${ACTIVE_PROJECT.name}.`
    );
  }

  if (!iss || !iss.endsWith(`/${EXPECTED_FIREBASE_PROJECT_ID}`)) {
    throw new Error(
      `[${context}] Token issuer mismatch: expected Firebase issuer for "${EXPECTED_FIREBASE_PROJECT_ID}", got "${iss || 'unknown'}". ` +
      `Run \`node scripts/auth-cli.mjs login --project ${ACTIVE_PROJECT.id}\` for ${ACTIVE_PROJECT.name}.`
    );
  }

  return { projectId: aud, issuer: iss };
}

/**
 * Refresh ID token using refresh token via Firebase REST API
 * @param {string} refreshToken - The refresh token
 * @returns {Promise<{idToken: string, refreshToken: string, expiresIn: number}>}
 */
async function refreshIdToken(refreshToken) {
  try {
    const response = await fetch(`${REFRESH_TOKEN_URL}?key=${CONFIG.firebaseConfig.apiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        grant_type: 'refresh_token',
        refresh_token: refreshToken
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`Token refresh failed: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();

    validateTokenProject(data.id_token, 'refresh');

    return {
      idToken: data.id_token,
      refreshToken: data.refresh_token,
      expiresIn: parseInt(data.expires_in, 10)
    };
  } catch (error) {
    throw new Error(`Failed to refresh token: ${error.message}`);
  }
}

async function readTokenData({ allowExpired = false, returnNullIfMissing = false, autoRefresh = false } = {}) {
  await ensureTokenDir();

  if (!existsSync(CONFIG.tokenPath)) {
    if (returnNullIfMissing) {
      return { tokenData: null, expiresAt: null, now: new Date(), expired: false };
    }
    throw new Error('Not authenticated. Run: node scripts/auth-cli.mjs login');
  }

  let rawToken;
  try {
    rawToken = await readFile(CONFIG.tokenPath, 'utf-8');
  } catch (err) {
    throw new Error(`Error reading token file: ${err.message}`);
  }

  let tokenData;
  try {
    tokenData = JSON.parse(rawToken);
  } catch (err) {
    throw new Error(`Corrupted token file: ${err.message}. Please login again.`);
  }

  const expiresAt = new Date(tokenData.expiresAt);
  if (Number.isNaN(expiresAt.getTime())) {
    throw new Error('Token has an invalid expiration timestamp. Please login again.');
  }

  try {
    validateTokenProject(tokenData.idToken, 'token');
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : String(error));
  }

  const now = new Date();
  const expired = now > expiresAt;

  // Auto-refresh if token is expired and we have a refresh token
  if (expired && autoRefresh && tokenData.refreshToken) {
    try {
      const refreshed = await refreshIdToken(tokenData.refreshToken);

      // Update token data with new ID token and expiration
      tokenData.idToken = refreshed.idToken;
      tokenData.refreshToken = refreshed.refreshToken; // Firebase may rotate refresh tokens
      tokenData.expiresAt = new Date(Date.now() + refreshed.expiresIn * 1000).toISOString();
      tokenData.firebaseProjectId = EXPECTED_FIREBASE_PROJECT_ID;

      // Save updated token
      await writeTokenFile(tokenData);

      // Return refreshed data
      return {
        tokenData,
        expiresAt: new Date(tokenData.expiresAt),
        now: new Date(),
        expired: false,
        refreshed: true
      };
    } catch (error) {
      throw new Error(`Token expired and refresh failed: ${error.message}. Please login again.`);
    }
  }

  if (expired && !allowExpired) {
    throw new Error('Token expired. Run: node scripts/auth-cli.mjs login');
  }

  return { tokenData, expiresAt, now, expired };
}

/**
 * Generate authentication HTML page served on localhost
 */
function getAuthHtml(callbackUrl) {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AI Universe - Sign In</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
    .status { padding: 20px; border-radius: 8px; margin: 20px 0; }
    .success { background: #d4edda; color: #155724; }
    .error { background: #f8d7da; color: #721c24; }
    button { padding: 12px 24px; font-size: 16px; cursor: pointer;
             background: #4285f4; color: white; border: none; border-radius: 4px; }
    button:hover { background: #357ae8; }
  </style>
</head>
<body>
  <h1>🚀 AI Universe Authentication</h1>
  <p>Sign in with your Google account to access the AI Universe MCP server</p>
  <button onclick="signIn()">Sign in with Google</button>
  <div id="status"></div>

  <script type="module">
    import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.4.0/firebase-app.js';
    import { getAuth, signInWithPopup, GoogleAuthProvider } from 'https://www.gstatic.com/firebasejs/12.4.0/firebase-auth.js';

    const firebaseConfig = ${JSON.stringify(CONFIG.firebaseConfig)};
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const provider = new GoogleAuthProvider();

    window.signIn = async function() {
      const statusDiv = document.getElementById('status');
      statusDiv.className = 'status';
      statusDiv.textContent = '⏳ Opening Google sign-in...';

      try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;
        const idToken = await user.getIdToken();

        // Get refresh token (available via stsTokenManager)
        const refreshToken = user.stsTokenManager?.refreshToken || user.refreshToken;

        // Send token back to CLI server
        const response = await fetch('${callbackUrl}', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            idToken,
            refreshToken,
            user: {
              uid: user.uid,
              email: user.email,
              displayName: user.displayName
            }
          })
        });

        if (response.ok) {
          statusDiv.className = 'status success';
          statusDiv.innerHTML = '✅ Authentication successful!<br>You can close this window and return to the terminal.';
        } else {
          throw new Error('Failed to save token');
        }
      } catch (error) {
        console.error('Authentication error:', error);
        statusDiv.className = 'status error';
        statusDiv.textContent = '❌ Authentication failed: ' + error.message;
      }
    };
  </script>
</body>
</html>`;
}

/**
 * Start local callback server and open browser for authentication
 */
async function login() {
  console.log('🔐 Starting authentication flow...\n');

  const app = express();
  app.use(express.json());

  let server;
  let tokenReceived = false;

  // Serve authentication page
  app.get('/', (req, res) => {
    const callbackUrl = `http://localhost:${CONFIG.callbackPort}${CONFIG.callbackPath}`;
    res.send(getAuthHtml(callbackUrl));
  });

  // Handle token callback
  app.post(CONFIG.callbackPath, async (req, res) => {
    try {
      const { idToken, refreshToken, user } = req.body;

      if (!idToken || typeof idToken !== 'string' || !idToken.trim()) {
        res.status(400).json({ error: 'Missing or invalid token' });
        return;
      }

      if (!refreshToken || typeof refreshToken !== 'string' || !refreshToken.trim()) {
        res.status(400).json({ error: 'Missing or invalid refresh token' });
        return;
      }

      if (!user || !user.uid || !user.email) {
        res.status(400).json({ error: 'Invalid user data' });
        return;
      }

      // Validate that the token belongs to the expected Firebase project
      try {
        validateTokenProject(idToken, 'login');
      } catch (validationError) {
        const message = validationError instanceof Error ? validationError.message : String(validationError);
        console.error(`❌ ${message}`);
        res.status(400).json({ error: message });
        return;
      }

      // Save token to file
      await ensureTokenDir();
      const tokenData = {
        idToken,
        refreshToken,
        user,
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + TOKEN_EXPIRATION_MS).toISOString(),
        firebaseProjectId: EXPECTED_FIREBASE_PROJECT_ID
      };

      await writeTokenFile(tokenData);

      res.json({ success: true });
      tokenReceived = true;

      if (server?.authTimeout) {
        clearTimeout(server.authTimeout);
        server.authTimeout = null;
      }

      console.log('\n✅ Authentication successful!');
      console.log(`   User: ${user.displayName} (${user.email})`);
      console.log(`   Token saved to: ${CONFIG.tokenPath}\n`);
      console.log('You can now use authenticated MCP tools.');

      // Close server after successful auth
      setTimeout(() => {
        server.close();
        process.exit(0);
      }, 1000);

    } catch (error) {
      console.error('❌ Error saving token:', error);
      res.status(500).json({ error: error.message });
    }
  });

  // Start server (bind to localhost only for security)
  server = createServer(app);
  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`❌ Port ${CONFIG.callbackPort} is already in use.`);
      console.error('   Please close any other applications using this port and try again.');
    } else {
      console.error('❌ Failed to start server:', err.message);
    }
    process.exit(1);
  });

  server.listen(CONFIG.callbackPort, '127.0.0.1', () => {
    const authUrl = `http://localhost:${CONFIG.callbackPort}`;
    console.log(`📡 Local authentication server started on ${authUrl}`);
    console.log('🌐 Opening browser for Google sign-in...\n');

    // Open browser after short delay
    setTimeout(() => {
      openBrowser(authUrl);
    }, 500);
  });

  // Timeout after 5 minutes
  const timeoutId = setTimeout(() => {
    if (!tokenReceived) {
      console.log('\n⏱️  Authentication timeout. Please try again.');
      server.close(() => {
        process.exit(1);
      });
    }
  }, AUTH_TIMEOUT_MS);

  // Store timeoutId for potential cleanup
  server.authTimeout = timeoutId;
}

/**
 * Logout (remove saved token)
 */
async function logout() {
  try {
    if (existsSync(CONFIG.tokenPath)) {
      await unlink(CONFIG.tokenPath);
      console.log('✅ Logged out successfully. Token removed.');
    } else {
      console.log('ℹ️  No active session found.');
    }
  } catch (error) {
    console.error('❌ Error during logout:', error.message);
    process.exit(1);
  }
}

/**
 * Manually refresh the authentication token
 */
async function refresh() {
  try {
    const { tokenData: oldTokenData } = await readTokenData({ allowExpired: true });

    if (!oldTokenData.refreshToken) {
      throw new Error('No refresh token found. Please login again.');
    }

    console.log('🔄 Refreshing authentication token...\n');

    const refreshed = await refreshIdToken(oldTokenData.refreshToken);

    // Update token data
    const tokenData = {
      ...oldTokenData,
      idToken: refreshed.idToken,
      refreshToken: refreshed.refreshToken,
      expiresAt: new Date(Date.now() + refreshed.expiresIn * 1000).toISOString(),
      firebaseProjectId: EXPECTED_FIREBASE_PROJECT_ID
    };

    await writeTokenFile(tokenData);

    console.log('✅ Token refreshed successfully!');
    console.log(`   User: ${tokenData.user.displayName} (${tokenData.user.email})`);
    console.log(`   New expiration: ${new Date(tokenData.expiresAt).toLocaleString()}\n`);
  } catch (error) {
    console.error('❌ Refresh failed:', error.message);
    console.error('   Please run: node scripts/auth-cli.mjs login');
    process.exit(1);
  }
}

/**
 * Show authentication status
 */
async function status() {
  try {
    const { tokenData, expiresAt, expired } = await readTokenData({ allowExpired: true, returnNullIfMissing: true });

    if (!tokenData) {
      console.log('❌ Not authenticated. Run: node scripts/auth-cli.mjs login');
      process.exit(1);
    }

    console.log('📊 Authentication Status:');
    console.log(`   User: ${tokenData.user.displayName} (${tokenData.user.email})`);
    console.log(`   UID: ${tokenData.user.uid}`);
    console.log(`   Firebase Project: ${tokenData.firebaseProjectId || EXPECTED_FIREBASE_PROJECT_ID}`);
    console.log(`   Created: ${new Date(tokenData.createdAt).toLocaleString()}`);
    console.log(`   Expires: ${expiresAt.toLocaleString()}`);
    console.log(`   Status: ${expired ? '❌ EXPIRED' : '✅ VALID'}\n`);

    if (expired) {
      console.log('⚠️  Token expired. Run: node scripts/auth-cli.mjs login');
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Error reading status:', error.message);
    process.exit(1);
  }
}

/**
 * Get current token (for use in other scripts)
 */
async function getToken() {
  try {
    const { tokenData, refreshed } = await readTokenData({ autoRefresh: true });

    if (refreshed) {
      console.error('ℹ️  Token was expired and has been automatically refreshed');
    }

    // Output just the token (for piping to other commands)
    console.log(tokenData.idToken);
  } catch (error) {
    console.error('❌', error.message);
    process.exit(1);
  }
}

/**
 * Test authenticated MCP call
 */
async function testMcp() {
  try {
    const { tokenData, refreshed } = await readTokenData({ autoRefresh: true });

    if (refreshed) {
      console.log('ℹ️  Token was expired and has been automatically refreshed\n');
    }

    console.log('🧪 Testing authenticated MCP connection...\n');

    const response = await fetch(CONFIG.productionMcpUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': `Bearer ${tokenData.idToken}`
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: 'get_second_opinion',
          arguments: {
            feedback_type: 'design',
            question: 'Authentication connectivity check'
          }
        },
        id: 1
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    const content = result?.result?.content;
    if (!Array.isArray(content) || typeof content[0]?.text !== 'string') {
      throw new Error('Unexpected MCP response structure. Cannot read tool output.');
    }

    const text = content[0].text;

    console.log('✅ Authentication successful!\n');
    console.log('🧪 MCP Response Preview:');
    console.log(text);

  } catch (error) {
    console.error('❌ MCP test failed:', error.message);
    process.exit(1);
  }
}

// Main CLI handler
const command = parsedCommand;

// Show active project if not default
if (projectOverride && command) {
  console.log(`🎯 Using project: ${ACTIVE_PROJECT.name} (${ACTIVE_PROJECT.id})\n`);
}

// Validate configuration for commands that need it
if (command === 'login' || command === 'test' || command === 'refresh' || command === 'token') {
  validateConfig();
}

switch (command) {
  case 'login':
    await login();
    break;
  case 'logout':
    await logout();
    break;
  case 'status':
    await status();
    break;
  case 'token':
    await getToken();
    break;
  case 'refresh':
    await refresh();
    break;
  case 'test':
    await testMcp();
    break;
  default:
    console.log(`
AI Universe CLI Authentication Tool

Usage:
  node scripts/auth-cli.mjs <command> [--project <project-id>]

Commands:
  login    - Start browser-based authentication flow
  logout   - Remove saved authentication token
  status   - Show current authentication status
  token    - Output current token (auto-refreshes if expired)
  refresh  - Manually refresh the authentication token
  test     - Test authenticated connection to MCP server

Options:
  --project, -p <id>  - Use a specific Firebase project instead of default
                        Known projects: ai-universe, worldarchitecture-ai
                        Custom project IDs are also supported

Default Project: ai-universe (ai-universe-b3551)

Token Refresh:
  - ID tokens expire after 1 hour (Firebase security policy)
  - Refresh tokens allow automatic renewal without re-authentication
  - 'token' and 'test' commands auto-refresh expired tokens
  - Use 'refresh' command to manually refresh before expiration

Examples:
  # Authenticate with AI Universe (default)
  node scripts/auth-cli.mjs login

  # Authenticate with a different project
  node scripts/auth-cli.mjs login --project worldarchitecture-ai
  node scripts/auth-cli.mjs login -p my-custom-project

  # Check status
  node scripts/auth-cli.mjs status

  # Get token (auto-refreshes if expired)
  TOKEN=$(node scripts/auth-cli.mjs token)

  # Manually refresh token
  node scripts/auth-cli.mjs refresh

  # Use token in HTTPie request
  TOKEN=$(node scripts/auth-cli.mjs token)
  echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}' | \\
    http POST ${CONFIG.productionMcpUrl} \\
    Accept:'application/json, text/event-stream' \\
    Authorization:"Bearer $TOKEN"
`);
    process.exit(command ? 1 : 0);
}
