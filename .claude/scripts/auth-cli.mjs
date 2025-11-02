#!/usr/bin/env node

/**
 * CLI Authentication Tool for AI Universe
 *
 * Implements browser-based OAuth flow with localhost callback server
 * Pattern used by: gcloud CLI, Firebase CLI, GitHub CLI
 *
 * Usage:
 *   node ~/.claude/scripts/auth-cli.mjs login
 *   node ~/.claude/scripts/auth-cli.mjs logout
 *   node ~/.claude/scripts/auth-cli.mjs status
 *   node ~/.claude/scripts/auth-cli.mjs token
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

// Configuration
const CONFIG = {
  // Firebase config for AI Universe
  // Note: Firebase web API keys are safe to include in client code (public by design)
  // See: https://firebase.google.com/docs/projects/api-keys
  firebaseConfig: {
    apiKey: process.env.FIREBASE_API_KEY || 'AIzaSyARs7IekRptvhZIwtV7lwJh3axWFsn_4c8',
    authDomain: process.env.FIREBASE_AUTH_DOMAIN || 'ai-universe-b3551.firebaseapp.com',
    projectId: process.env.FIREBASE_PROJECT_ID || 'ai-universe-b3551'
  },
  callbackPort: 9005,
  callbackPath: '/auth/callback',
  tokenPath: join(homedir(), '.ai-universe', 'auth-token.json'),
  productionMcpUrl: 'https://ai-universe-backend-final.onrender.com/mcp'
};

// Validate required configuration
function validateConfig() {
  // Firebase API key is now hardcoded with sensible defaults
  // Environment variables can still override if needed
  if (!CONFIG.firebaseConfig.apiKey || CONFIG.firebaseConfig.apiKey.length < 10) {
    console.error('❌ Firebase configuration invalid.');
    console.error('   API key is missing or invalid.');
    console.error('');
    console.error('Set environment variable to override:');
    console.error('   export FIREBASE_API_KEY="your-firebase-web-api-key"');
    process.exit(1);
  }
}

// Ensure token directory exists when needed
const tokenDir = join(homedir(), '.ai-universe');

async function ensureTokenDir() {
  if (!existsSync(tokenDir)) {
    await mkdir(tokenDir, { recursive: true, mode: 0o700 });
  } else {
    // Ensure correct permissions on existing directory
    try {
      await chmod(tokenDir, 0o700);
    } catch (err) {
      // Ignore chmod errors on Windows or permission-restricted systems
    }
  }
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
    throw new Error('Not authenticated. Run: node ~/.claude/scripts/auth-cli.mjs login');
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

      // Save updated token
      await writeFile(CONFIG.tokenPath, JSON.stringify(tokenData, null, 2));
      await chmod(CONFIG.tokenPath, 0o600);

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
    throw new Error('Token expired. Run: node ~/.claude/scripts/auth-cli.mjs login');
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

      // Save token to file
      await ensureTokenDir();
      const tokenData = {
        idToken,
        refreshToken,
        user,
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + TOKEN_EXPIRATION_MS).toISOString()
      };

      await writeFile(CONFIG.tokenPath, JSON.stringify(tokenData, null, 2));
      await chmod(CONFIG.tokenPath, 0o600);

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
      expiresAt: new Date(Date.now() + refreshed.expiresIn * 1000).toISOString()
    };

    await writeFile(CONFIG.tokenPath, JSON.stringify(tokenData, null, 2));
    await chmod(CONFIG.tokenPath, 0o600);

    console.log('✅ Token refreshed successfully!');
    console.log(`   User: ${tokenData.user.displayName} (${tokenData.user.email})`);
    console.log(`   New expiration: ${new Date(tokenData.expiresAt).toLocaleString()}\n`);
  } catch (error) {
    console.error('❌ Refresh failed:', error.message);
    console.error('   Please run: node ~/.claude/scripts/auth-cli.mjs login');
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
      console.log('❌ Not authenticated. Run: node ~/.claude/scripts/auth-cli.mjs login');
      process.exit(1);
    }

    console.log('📊 Authentication Status:');
    console.log(`   User: ${tokenData.user.displayName} (${tokenData.user.email})`);
    console.log(`   UID: ${tokenData.user.uid}`);
    console.log(`   Created: ${new Date(tokenData.createdAt).toLocaleString()}`);
    console.log(`   Expires: ${expiresAt.toLocaleString()}`);
    console.log(`   Status: ${expired ? '❌ EXPIRED' : '✅ VALID'}\n`);

    if (expired) {
      console.log('⚠️  Token expired. Run: node ~/.claude/scripts/auth-cli.mjs login');
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
          name: 'rate-limit.status',
          arguments: {
            userId: tokenData.user.uid
          }
        },
        id: 1
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    // Validate response structure
    if (!result || typeof result !== 'object' ||
        !result.result || typeof result.result !== 'object' ||
        !Array.isArray(result.result.content) ||
        result.result.content.length === 0 ||
        typeof result.result.content[0]?.text !== 'string') {
      throw new Error('Unexpected MCP response structure. Cannot find rate limit data.');
    }

    let rateLimitData;
    try {
      rateLimitData = JSON.parse(result.result.content[0].text);
    } catch (err) {
      throw new Error(`Failed to parse rate limit data: ${err.message}`);
    }

    // Validate rate limit data structure
    if (!rateLimitData.userType || rateLimitData.limit === undefined) {
      throw new Error('Incomplete rate limit data in response');
    }

    console.log('✅ Authentication successful!\n');
    console.log('📊 Rate Limit Status:');
    console.log(`   User Type: ${rateLimitData.userType}`);
    console.log(`   Usage: ${rateLimitData.usage}/${rateLimitData.limit}`);
    console.log(`   Remaining: ${rateLimitData.remaining}`);
    console.log(`   Reset Time: ${new Date(rateLimitData.resetTime).toLocaleString()}\n`);

  } catch (error) {
    console.error('❌ MCP test failed:', error.message);
    process.exit(1);
  }
}

// Main CLI handler
const command = process.argv[2];

// Validate configuration for commands that need it
if (command === 'login' || command === 'test' || command === 'refresh') {
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
  node ~/.claude/scripts/auth-cli.mjs <command>

Commands:
  login    - Start browser-based authentication flow
  logout   - Remove saved authentication token
  status   - Show current authentication status
  token    - Output current token (auto-refreshes if expired)
  refresh  - Manually refresh the authentication token
  test     - Test authenticated connection to MCP server

Token Refresh:
  - ID tokens expire after 1 hour (Firebase security policy)
  - Refresh tokens allow automatic renewal without re-authentication
  - 'token' and 'test' commands auto-refresh expired tokens
  - Use 'refresh' command to manually refresh before expiration

Examples:
  # Authenticate
  node ~/.claude/scripts/auth-cli.mjs login

  # Check status
  node ~/.claude/scripts/auth-cli.mjs status

  # Get token (auto-refreshes if expired)
  TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)

  # Manually refresh token
  node ~/.claude/scripts/auth-cli.mjs refresh

  # Use token in HTTPie request
  TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)
  echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}' | \\
    http POST ${CONFIG.productionMcpUrl} \\
    Accept:'application/json, text/event-stream' \\
    Authorization:"Bearer $TOKEN"
`);
    process.exit(command ? 1 : 0);
}
